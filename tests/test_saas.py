import io,json,secrets,tempfile,threading,unittest
from unittest.mock import patch
import server,saas,wsgi
from test_app import Client

class SaaSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.original_db=server.DB;server.DB=cls.tmp.name+'/saas.sqlite3';server.init()
        cls.environment=patch.dict(server.os.environ,{'BAZAR_ALLOW_SIGNUP':'1','COOKIE_SECURE':'0'});cls.environment.start()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start();cls.base=f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.environment.stop();server.DB=cls.original_db;cls.tmp.cleanup()
    def setUp(self):
        self.owner=Client(self.base);self.owner.request('register',{'name':'Owner','email':secrets.token_hex(8)+'@test.ma','company':'Client company','password':'Long-owner-password'})
        self.owner_state=self.owner.state();self.shop=self.owner_state['shops'][0]['id']
        with server.connect() as c:
            self.company=c.execute('SELECT company_id FROM shops WHERE id=?',(self.shop,)).fetchone()[0]
            self.admin_email=secrets.token_hex(8)+'@test.ma'
            c.execute("INSERT INTO users(company_id,name,email,password,role) VALUES(NULL,'Publisher',?,?,'platform_admin')",(self.admin_email,server.password('Publisher-long-password')))
        self.admin=Client(self.base);self.admin.request('login',{'email':self.admin_email,'password':'Publisher-long-password'});self.admin.state()
    def plan(self,shops=3,users=10):
        code,result=self.admin.request('platform/plans',{'name':'Pro','price':300,'max_shops':shops,'max_users':users});self.assertEqual(code,200)
        self.assertEqual(self.admin.request('platform/plan',{'company_id':self.company,'plan_id':result['id']})[0],200)
        return result['id']
    def payment(self,**overrides):
        data={'company_id':self.company,'key':secrets.token_hex(16),'amount':300,'months':1,'method':'bank_transfer','reference':secrets.token_hex(8)};data.update(overrides);return data
    def test_publisher_provisions_first_shop_and_owner(self):
        email=secrets.token_hex(8)+'@test.ma'
        code,result=self.admin.request('platform/companies',{'company_name':'Atlas client','shop_name':'Médina','owner_name':'New owner','email':email,'password':'Temporary-password-123','plan_id':1})
        self.assertEqual(code,200)
        client=Client(self.base);self.assertEqual(client.request('login',{'email':email,'password':'Temporary-password-123'})[0],200)
        data=client.state();self.assertTrue(data['password_required']);self.assertNotIn('shops',data)
        self.assertEqual(client.create('shops',name='Denied',address='')[0],403)
        self.assertEqual(client.request('account/password',{'current_password':'Temporary-password-123','new_password':'My-personal-password-123'})[0],200)
        data=client.state();self.assertEqual([s['name'] for s in data['shops']],['Médina']);self.assertEqual(data['user']['role'],'owner')
        self.assertTrue(data['subscription']['accessible'])
    def test_closed_registration(self):
        with patch.dict(server.os.environ,{'BAZAR_ALLOW_SIGNUP':'0'}):
            visitor=Client(self.base);self.assertEqual(visitor.request('public-config')[1],{'allow_signup':False})
            self.assertEqual(visitor.request('register',{})[0],403)
    def test_platform_is_separate_from_customer(self):
        state=self.admin.state();self.assertTrue(state['platform']);self.assertNotIn('sales',state);self.assertNotIn('products',state)
        self.assertEqual(self.owner.request('platform/access',{'company_id':self.company,'enabled':False})[0],403)
        self.assertEqual(self.admin.create('shops',name='No tenant',address='')[0],403)
    def test_suspend_and_restore_existing_session(self):
        self.assertEqual(self.admin.request('platform/access',{'company_id':self.company,'enabled':False})[0],200)
        state=self.owner.state();self.assertTrue(state['blocked']);self.assertNotIn('products',state)
        self.assertEqual(self.owner.create('clients',name='Denied',email='',phone='',address='')[0],403)
        self.admin.request('platform/access',{'company_id':self.company,'enabled':True});self.assertIn('shops',self.owner.state())
    def test_expired_access_is_checked_each_request(self):
        with server.connect() as c:c.execute("UPDATE subscriptions SET period_end='2000-01-01T00:00:00+00:00' WHERE company_id=?",(self.company,))
        state=self.owner.state();self.assertTrue(state['blocked']);self.assertEqual(state['subscription']['effective_status'],'expired')
        self.assertEqual(self.owner.create('shops',name='Denied',address='')[0],403)
    def test_quotas_cannot_be_bypassed(self):
        self.plan(shops=1,users=1)
        self.assertEqual(self.owner.create('shops',name='Extra',address='')[0],400)
        self.assertEqual(self.owner.create('users',name='Extra',email='extra@test.ma',password='Long-password-123',role='owner')[0],400)
    def test_manual_payment_and_idempotency(self):
        self.plan();data=self.payment();code,first=self.admin.request('platform/payment',data);self.assertEqual(code,200)
        self.assertEqual(self.admin.request('platform/payment',data),(200,first))
        self.assertEqual(self.owner.state()['subscription']['status'],'active')
        self.assertEqual(len(self.owner.state()['subscription_payments']),1)
        changed={**data,'amount':600,'months':2};self.assertEqual(self.admin.request('platform/payment',changed)[0],400)
        self.assertEqual(self.admin.request('platform/payment',{**data,'key':secrets.token_hex(16)})[0],400)
    def test_payment_does_not_remove_suspension(self):
        self.plan();self.admin.request('platform/access',{'company_id':self.company,'enabled':False})
        self.assertEqual(self.admin.request('platform/payment',self.payment())[0],200);self.assertTrue(self.owner.state()['blocked'])
    def test_arbitrary_amount_and_fractional_months_rejected(self):
        self.plan()
        self.assertEqual(self.admin.request('platform/payment',self.payment(amount=1))[0],400)
        self.assertEqual(self.admin.request('platform/payment',self.payment(months=1.5))[0],400)
        self.assertEqual(self.admin.request('platform/plans',{'name':'Invalid','price':10,'max_shops':1.5,'max_users':2})[0],400)
    def test_customer_cannot_read_other_subscription_payments(self):
        self.plan();self.admin.request('platform/payment',self.payment())
        other=Client(self.base);other.request('register',{'name':'Other','email':secrets.token_hex(8)+'@test.ma','company':'Other','password':'Long-other-password'})
        self.assertEqual(other.state()['subscription_payments'],[])
    def test_initialization_does_not_extend_trial(self):
        before=self.owner.state()['subscription']['period_end'];server.init();self.assertEqual(self.owner.state()['subscription']['period_end'],before)
    def test_bruteforce_throttle(self):
        visitor=Client(self.base);email=secrets.token_hex(8)+'@test.ma'
        for _ in range(10):self.assertEqual(visitor.request('login',{'email':email,'password':'bad'})[0],401)
        self.assertEqual(visitor.request('login',{'email':email,'password':'bad'})[0],429)
    def test_reset_owner_revokes_existing_sessions(self):
        owner_id=self.owner_state['user']['id']
        self.assertEqual(self.admin.request('platform/reset-owner',{'company_id':self.company,'owner_id':owner_id,'password':'Reset-customer-secret-123'})[0],200)
        self.assertEqual(self.owner.request('state')[0],401)
        self.owner.request('login',{'email':self.owner_state['user']['email'],'password':'Reset-customer-secret-123'})
        self.assertTrue(self.owner.state()['password_required'])
    def test_wsgi_health_and_origin_enforcement(self):
        def request(path,method='GET',origin=None):
            environ={'PATH_INFO':path,'REQUEST_METHOD':method,'HTTP_HOST':'erp.example.com','wsgi.input':io.BytesIO(b'{}'),'CONTENT_LENGTH':'2','CONTENT_TYPE':'application/json'}
            if origin:environ['HTTP_ORIGIN']=origin
            result={}
            def start(status,headers):result.update(status=status,headers=dict(headers))
            result['body']=b''.join(wsgi.application(environ,start));return result
        with patch.dict(server.os.environ,{'PUBLIC_BASE_URL':'https://erp.example.com','COOKIE_SECURE':'1'}):
            health=request('/healthz');self.assertTrue(health['status'].startswith('200'));self.assertIn('Strict-Transport-Security',health['headers'])
            self.assertTrue(request('/api/login','POST','https://evil.example')['status'].startswith('403'))
            self.assertTrue(request('/','HEAD')['body']==b'')

if __name__=='__main__':unittest.main()
