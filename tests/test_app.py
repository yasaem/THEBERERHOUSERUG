import unittest, tempfile, threading, json, urllib.request, urllib.error, http.cookiejar, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

class Client:
    def __init__(self,base):
        self.base=base; self.csrf=''; self.language='fr'; self.http=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def request(self,path,data=None,csrf=True):
        req=urllib.request.Request(self.base+'/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json','X-App-Language':self.language,'X-CSRF-Token':self.csrf if csrf else ''})
        try:
            with self.http.open(req) as r: return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def state(self):
        code,s=self.request('state'); self.csrf=s.get('csrf','');return s
    def create(self,t,**values):return self.request('create',{'entity':t,'values':values})

class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from unittest.mock import patch
        cls.signup_patch=patch.dict(server.os.environ,{'BAZAR_ALLOW_SIGNUP':'1'});cls.signup_patch.start()
        cls.tmp=tempfile.TemporaryDirectory();server.DB=cls.tmp.name+'/test.sqlite3';server.init()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler); cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start();cls.base=f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup();cls.signup_patch.stop()
    def setUp(self):
        self.a=Client(self.base);self.b=Client(self.base)
        import secrets
        for c in [self.a,self.b]:
            self.assertEqual(c.request('register',{'company':'Bazar','name':'Owner','email':secrets.token_hex(10)+'@test.ma','password':'A-long-secret-123'})[0],200)
        self.sa=self.a.state()['shops'][0]['id'];self.sb=self.b.state()['shops'][0]['id']
        self.pid=self.a.create('products',shop_id=self.sa,name='Tapis',reference='T01',category='Tapis',cost=4000,price=10000,quantity=10)[1]['id']
    def sale(self,**overrides):
        d={'key':'one','shop_id':self.sa,'client':'Client','lines':[{'product_id':self.pid,'quantity':1,'price':10000}],'shipping':500,'bank':150,'paid':3000,'commissions':[{'name':'Guide','kind':'Guide','value':10},{'name':'Agence','kind':'Agence','value':5},{'name':'Vendeur A','kind':'Vendeur','value':3,'share':50},{'name':'Vendeur B','kind':'Vendeur','value':3,'share':50}]};d.update(overrides);return self.a.request('sales',d)
    def test_commission_shipping_profit(self):
        self.assertEqual(self.sale()[0],200);s=self.a.state();sale=s['sales'][0]
        self.assertEqual(sum(x['amount'] for x in s['commissions']),171000)
        self.assertEqual(sale['total']-sale['cost']-sale['shipping']-sale['bank']-sum(x['amount'] for x in s['commissions']),364000)
        self.assertTrue(all(c['base']==950000 for c in s['commissions']))
        self.assertTrue(all(c['paid']==0 for c in s['commissions']))
    def test_idempotency(self):
        a=self.sale();b=self.sale();self.assertEqual(a,b);s=self.a.state();self.assertEqual(len(s['sales']),1);self.assertEqual(s['products'][0]['quantity'],9)
    def test_stock_failure_rolls_back(self):
        self.assertEqual(self.sale(lines=[{'product_id':self.pid,'quantity':11,'price':10000}])[0],400)
        s=self.a.state();self.assertEqual(s['sales'],[]);self.assertEqual(s['products'][0]['quantity'],10)
    def test_tenant_isolation(self):
        self.assertEqual(self.b.state()['products'],[])
        self.assertEqual(self.b.request('adjust',{'id':self.pid,'quantity':9,'reason':'hack'})[0],400)
        self.assertEqual(self.sale(shop_id=self.sb)[0],400)
    def test_partial_payments_and_overpayment(self):
        ident=self.sale()[1]['id'];self.assertEqual(self.a.request('pay',{'entity':'sales','id':ident,'amount':2000})[0],200)
        self.assertEqual(self.a.state()['sales'][0]['paid'],500000)
        self.assertEqual(self.a.request('pay',{'entity':'sales','id':ident,'amount':6000})[0],400)
    def test_cancel_once_restores_stock(self):
        ident=self.sale()[1]['id'];self.assertEqual(self.a.request('cancel',{'id':ident})[0],200);self.a.request('cancel',{'id':ident});s=self.a.state()
        self.assertEqual(s['products'][0]['quantity'],10);self.assertEqual(s['sales'][0]['status'],'Annulée');self.assertEqual(sum(c['amount'] for c in s['commissions']),0)
    def test_paid_commission_blocks_cancel(self):
        ident=self.sale()[1]['id'];c=self.a.state()['commissions'][0]
        self.assertEqual(self.a.request('pay',{'entity':'commissions','id':c['id'],'amount':1})[0],200)
        self.assertEqual(self.a.request('cancel',{'id':ident})[0],400)
    def test_free_item_tax_discount(self):
        self.assertEqual(self.sale(lines=[{'name':'Poterie libre','quantity':2,'price':100,'cost':20}],discount=10,vat=20,paid=0,shipping=0,commissions=[])[0],200)
        s=self.a.state();self.assertEqual(s['sales'][0]['total'],22800);self.assertEqual(s['products'][0]['quantity'],10)
    def test_vendor_split(self):
        self.assertEqual(self.sale(commissions=[{'name':'A','kind':'Vendeur','value':3,'share':60}])[0],400)
        self.assertEqual(self.sale(commissions=[{'name':'A','kind':'Vendeur','value':3,'share':50},{'name':'B','kind':'Vendeur','value':4,'share':50}])[0],400)
    def test_csrf(self):self.assertEqual(self.a.request('adjust',{'id':self.pid,'quantity':1,'reason':'bad'},csrf=False)[0],403)
    def test_operator_permissions(self):
        self.a.create('users',name='Opérateur',email='op'+str(self.pid)+'@test.ma',password='Operator-secret-123',role='operator',assigned_shop=self.sa)
        op=Client(self.base);self.assertEqual(op.request('login',{'email':'op'+str(self.pid)+'@test.ma','password':'Operator-secret-123'})[0],200);s=op.state()
        self.assertNotIn('expenses',s);self.assertNotIn('cost',s['products'][0]);self.assertNotIn('sales',s)
        self.assertEqual(op.create('shops',name='bad',address='')[0],403)
    def test_seller_confidentiality(self):
        self.sale();self.a.create('users',name='Seller',email=f'seller{self.pid}@test.ma',password='Seller-secret-123',role='seller',assigned_shop=self.sa);seller=Client(self.base);seller.request('login',{'email':f'seller{self.pid}@test.ma','password':'Seller-secret-123'});s=seller.state()
        self.assertEqual(s['sales'],[]);self.assertEqual(s['commissions'],[]);self.assertNotIn('expenses',s)
        self.assertEqual(seller.request('invoice',{'id':self.a.state()['sales'][0]['id']})[0],403)
    def test_import_atomic_duplicate(self):
        row={'name':'Bol','reference':'B1','quantity':2,'cost':10,'price':20}
        self.assertEqual(self.a.request('import',{'shop_id':self.sa,'rows':[row,row]})[0],400)
        self.assertEqual(len(self.a.state()['products']),1)
        self.assertEqual(self.a.request('import',{'shop_id':self.sa,'rows':[row]})[0],200)
    def test_invoice_snapshot(self):
        ident=self.sale()[1]['id']
        with server.connect() as c:c.execute('UPDATE products SET price=1,cost=1 WHERE id=?',(self.pid,))
        code,invoice=self.a.request('invoice',{'id':ident});self.assertEqual(code,200);self.assertEqual(invoice['lines'][0]['price'],1000000)
        self.assertEqual(self.b.request('invoice',{'id':ident})[0],400)
    def test_shop_permissions(self):
        other=self.a.create('shops',name='Seconde',address='')[1]['id']
        self.a.create('users',name='Responsable',email=f'manager{self.pid}@test.ma',password='Manager-secret-123',role='manager',assigned_shop=self.sa)
        m=Client(self.base);m.request('login',{'email':f'manager{self.pid}@test.ma','password':'Manager-secret-123'});s=m.state()
        self.assertEqual([x['id'] for x in s['shops']],[self.sa]);self.assertNotIn('users',s)
        self.assertEqual(m.create('products',shop_id=other,name='bad',reference='bad',category='',cost=1,price=2,quantity=1)[0],400)
        self.assertEqual(m.create('users',name='bad',email='bad@test.ma',password='Bad-secret-123',role='owner')[0],403)
    def test_penny_allocation(self):
        self.assertEqual(self.sale(lines=[{'name':'Libre','quantity':1,'price':0.01}],shipping=0,paid=0,commissions=[{'name':'A','kind':'Vendeur','value':100,'share':50},{'name':'B','kind':'Vendeur','value':100,'share':50}])[0],200)
        self.assertEqual(sum(c['amount'] for c in self.a.state()['commissions']),1)
    def test_pdf_and_immutable_company(self):
        self.a.request('company-settings',{'ice':'ICE-ORIGINAL','address':'Médina','tax_id':'IF123'})
        ident=self.sale()[1]['id'];self.a.request('company-settings',{'ice':'CHANGED','address':'Autre','tax_id':'IF999'})
        code,invoice=self.a.request('invoice',{'id':ident});self.assertEqual(invoice['company']['ice'],'ICE-ORIGINAL')
        import base64
        code,doc=self.a.request('invoice-pdf',{'id':ident});self.assertEqual(code,200);self.assertTrue(base64.b64decode(doc['content']).startswith(b'%PDF'))
    def test_excel_preview(self):
        import zipfile,io,base64
        file=io.BytesIO()
        with zipfile.ZipFile(file,'w') as z:
            z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="inlineStr"><is><t>name</t></is></c><c r="B1" t="inlineStr"><is><t>quantity</t></is></c></row><row><c r="A2" t="inlineStr"><is><t>Tapis</t></is></c><c r="B2"><v>4</v></c></row></sheetData></worksheet>')
        code,r=self.a.request('import-preview',{'filename':'stock.xlsx','content':base64.b64encode(file.getvalue()).decode()});self.assertEqual(code,200);self.assertEqual(r['rows'],[['Tapis','4']])
    def test_archive_and_user_revocation(self):
        self.a.request('update',{'entity':'products','id':self.pid,'values':{'active':0}})
        self.assertEqual(self.sale()[0],400)
        uid=self.a.create('users',name='Seller',email=f'revoke{self.pid}@test.ma',password='Seller-secret-123',role='seller',assigned_shop=self.sa)[1]['id']
        seller=Client(self.base);seller.request('login',{'email':f'revoke{self.pid}@test.ma','password':'Seller-secret-123'});seller.state()
        self.assertEqual(self.a.request('update',{'entity':'users','id':uid,'values':{'active':0}})[0],200)
        self.assertEqual(seller.request('state')[0],401)
    def test_pdf_languages(self):
        ident=self.sale()[1]['id']
        import base64
        from unittest.mock import patch
        from reportlab.platypus import Paragraph
        for selected,heading,total in [('fr','FACTURE','Total TTC'),('en','INVOICE','Total incl. VAT')]:
            with patch('documents.Paragraph',wraps=Paragraph) as paragraph:
                code,result=self.a.request('invoice-pdf',{'id':ident,'language':selected})
                self.assertEqual(code,200)
                self.assertEqual(result['language'],selected)
                self.assertTrue(base64.b64decode(result['content']).startswith(b'%PDF'))
                texts=[call.args[0] for call in paragraph.call_args_list]
                self.assertIn(heading+' F-'+str(ident).zfill(6),texts)
                self.assertTrue(any(text.startswith(total+' :') for text in texts))
        self.assertEqual(self.a.request('invoice-pdf',{'id':ident,'language':'de'})[0],400)
    def test_localized_error_keeps_business_data(self):
        from localization import translate
        self.assertEqual(translate('Stock insuffisant: Client','en'),'Insufficient stock: Client')
        self.a.language='en'
        code,result=self.a.request('adjust',{'id':self.pid,'quantity':-1,'reason':'test'})
        self.assertEqual(code,400);self.assertEqual(result['error'],'Quantity and reason are required')
    def test_email_languages_without_external_delivery(self):
        from unittest.mock import patch
        ident=self.sale()[1]['id']
        for selected,subject,greeting in [('fr','Votre facture','Bonjour'),('en','Your invoice','Hello')]:
            with patch.dict(server.os.environ,{'SMTP_HOST':'smtp.example.test','SMTP_FROM':'bazar@example.test'}), patch('server.smtplib.SMTP') as smtp:
                code,_=self.a.request('invoice-email',{'id':ident,'email':'customer@example.test','language':selected})
                self.assertEqual(code,200)
                message=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
                self.assertTrue(message['Subject'].startswith(subject))
                self.assertIn(greeting,message.get_body(preferencelist=('plain',)).get_content())
                self.assertEqual(len(list(message.iter_attachments())),1)
                smtp.return_value.__enter__.return_value.starttls.assert_called_once()
    def test_invalid_quantity(self):
        self.assertEqual(self.sale(lines=[{'product_id':self.pid,'quantity':1.5,'price':10000}])[0],400)

if __name__=='__main__':unittest.main()
