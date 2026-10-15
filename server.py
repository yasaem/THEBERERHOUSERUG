import os, json, sqlite3, secrets, hashlib, hmac, time, csv, io, base64, zipfile
import xml.etree.ElementTree as ET
import smtplib, ssl
import saas
from email.message import EmailMessage
from documents import pdf as invoice_pdf
from localization import translate, language as validate_language
from decimal import Decimal, ROUND_HALF_UP
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path

ROOT = Path(__file__).parent
DB = os.environ.get('BAZAR_DB', str(ROOT / '.data' / 'bazar.sqlite3'))

def money(v):
    d = Decimal(str(v))
    if not d.is_finite() or d < 0: raise ValueError('Montant invalide')
    return int((d * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def rate(base, pct):
    p = Decimal(str(pct))
    if not p.is_finite() or not 0 <= p <= 100: raise ValueError('Pourcentage invalide')
    return int((Decimal(base)*p/100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def password(raw, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256', raw.encode(), salt.encode(), 210000).hex()

class ManagedConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

def connect():
    c = sqlite3.connect(DB, timeout=20, factory=ManagedConnection)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=20000')
    return c

def init():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    with connect() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS companies(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies, name TEXT,email TEXT UNIQUE,password TEXT,role TEXT,active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS company_settings(company_id INTEGER PRIMARY KEY REFERENCES companies,address TEXT DEFAULT '',ice TEXT DEFAULT '',tax_id TEXT DEFAULT '',logo TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS invoices(sale_id INTEGER PRIMARY KEY REFERENCES sales,snapshot TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS user_shops(user_id INTEGER REFERENCES users,shop_id INTEGER REFERENCES shops,PRIMARY KEY(user_id,shop_id));
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users,expires REAL,csrf TEXT);
CREATE TABLE IF NOT EXISTS shops(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,name TEXT,address TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,shop_id INTEGER REFERENCES shops,name TEXT,reference TEXT,category TEXT,cost INTEGER,price INTEGER,quantity INTEGER,active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,name TEXT,email TEXT,phone TEXT,address TEXT);
CREATE TABLE IF NOT EXISTS partners(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,name TEXT,kind TEXT);
CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,shop_id INTEGER REFERENCES shops,date TEXT,name TEXT,category TEXT,amount INTEGER,paid INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,shop_id INTEGER REFERENCES shops,name TEXT,position TEXT,salary INTEGER);
CREATE TABLE IF NOT EXISTS salaries(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,shop_id INTEGER REFERENCES shops,employee_id INTEGER REFERENCES employees,name TEXT,date TEXT,amount INTEGER,paid INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,shop_id INTEGER REFERENCES shops,user_id INTEGER REFERENCES users,client TEXT,date TEXT,status TEXT,subtotal INTEGER,discount INTEGER,tax INTEGER,total INTEGER,shipping INTEGER,bank INTEGER,cost INTEGER,paid INTEGER DEFAULT 0,idempotency TEXT,UNIQUE(company_id,idempotency));
CREATE TABLE IF NOT EXISTS lines(id INTEGER PRIMARY KEY,sale_id INTEGER REFERENCES sales,product_id INTEGER REFERENCES products,name TEXT,quantity INTEGER,price INTEGER,cost INTEGER);
CREATE TABLE IF NOT EXISTS commissions(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,shop_id INTEGER REFERENCES shops,sale_id INTEGER REFERENCES sales,partner TEXT,user_id INTEGER REFERENCES users,kind TEXT,base INTEGER,method TEXT,value TEXT,amount INTEGER,paid INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,entity TEXT,entity_id INTEGER,amount INTEGER,date TEXT,user_id INTEGER REFERENCES users);
CREATE TABLE IF NOT EXISTS movements(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,product_id INTEGER REFERENCES products,quantity INTEGER,reason TEXT,date TEXT,user_id INTEGER REFERENCES users);
CREATE INDEX IF NOT EXISTS sales_company_date ON sales(company_id,shop_id,date);
CREATE INDEX IF NOT EXISTS commissions_company_sale ON commissions(company_id,sale_id);
CREATE INDEX IF NOT EXISTS products_company_shop ON products(company_id,shop_id);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,company_id INTEGER REFERENCES companies,user_id INTEGER REFERENCES users,event TEXT,date TEXT);
''')
        saas.init(c)
        c.commit()
        c.execute('PRAGMA journal_mode=WAL')

def now(): return time.strftime('%Y-%m-%dT%H:%M:%S',time.gmtime())
def audit(c,u,event): c.execute('INSERT INTO audit(company_id,user_id,event,date) VALUES(?,?,?,?)',(u['company_id'],u['id'],event,now()))
def owned(c,table,pk,u):
    row=c.execute(f'SELECT * FROM {table} WHERE id=? AND company_id=?',(pk,u['company_id'])).fetchone()
    if not row: raise ValueError('Élément introuvable')
    sid=row['shop_id'] if 'shop_id' in row.keys() else row['id'] if table=='shops' else None
    if sid and u['role']!='owner' and not c.execute('SELECT 1 FROM user_shops WHERE user_id=? AND shop_id=?',(u['id'],sid)).fetchone(): raise ValueError('Boutique non autorisée')
    return row

def sale_create(c,u,d):
    owned(c,'shops',d['shop_id'],u)
    old=c.execute('SELECT id FROM sales WHERE company_id=? AND idempotency=?',(u['company_id'],d['key'])).fetchone()
    if old: return old['id']
    items=[]; subtotal=cost=0
    for line in d['lines']:
        if Decimal(str(line['quantity'])) != Decimal(str(line['quantity'])).to_integral_value(): raise ValueError('Quantité entière requise')
        q=int(line['quantity'])
        if q <= 0: raise ValueError('Quantité strictement positive requise')
        p=owned(c,'products',line['product_id'],u) if line.get('product_id') else None
        if p and (p['shop_id']!=int(d['shop_id']) or not p['active']): raise ValueError('Article indisponible dans cette boutique')
        price=money(line['price']); buy=p['cost'] if p else money(line.get('cost',0))
        name=p['name'] if p else str(line.get('name','')).strip()
        if not name: raise ValueError('Désignation obligatoire')
        items.append((p,name,q,price,buy)); subtotal+=price*q; cost+=buy*q
    if not items: raise ValueError('Ajoutez un article')
    discount=money(d.get('discount',0)); shipping=money(d.get('shipping',0)); bank=money(d.get('bank',0))
    if discount>subtotal: raise ValueError('La remise dépasse la vente')
    ht=subtotal-discount; tax=rate(ht,d.get('vat',0)); total=ht+tax; paid=money(d.get('paid',0))
    if paid>total: raise ValueError('Paiement supérieur au total')
    parts=d.get('commissions',[])
    sellers=[x for x in parts if x.get('kind')=='Vendeur']
    if any(x.get('method','percent')!=sellers[0].get('method','percent') or Decimal(str(x.get('value',0)))!=Decimal(str(sellers[0].get('value',0))) for x in sellers): raise ValueError('Les vendeurs doivent partager la même enveloppe de commission')
    if sellers and sum(Decimal(str(x.get('share',0))) for x in sellers)!=100: raise ValueError('La répartition des vendeurs doit totaliser 100 %')
    ident=c.execute('INSERT INTO sales(company_id,shop_id,user_id,client,date,status,subtotal,discount,tax,total,shipping,bank,cost,paid,idempotency) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(u['company_id'],d['shop_id'],u['id'],d.get('client','Client de passage'),now(),'Payée' if paid==total else 'Partielle' if paid else 'Validée',subtotal,discount,tax,total,shipping,bank,cost,paid,d['key'])).lastrowid
    for p,name,q,price,buy in items:
        if p:
            changed=c.execute('UPDATE products SET quantity=quantity-? WHERE id=? AND quantity>=?',(q,p['id'],q)).rowcount
            if not changed: raise ValueError('Stock insuffisant : '+name)
            c.execute('INSERT INTO movements(company_id,product_id,quantity,reason,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],p['id'],-q,f'Vente #{ident}',now(),u['id']))
        c.execute('INSERT INTO lines(sale_id,product_id,name,quantity,price,cost) VALUES(?,?,?,?,?,?)',(ident,p['id'] if p else None,name,q,price,buy))
    base=max(0,ht-shipping)
    # Allocate the seller pool once, using largest remainders to preserve every cent.
    seller_amounts={}
    if sellers:
        pool=rate(base,sellers[0].get('value',0)) if sellers[0].get('method','percent')=='percent' else money(sellers[0].get('value',0))
        exact=[]
        for x in sellers:
            share=Decimal(str(x.get('share',0)))
            if not share.is_finite() or not 0<=share<=100: raise ValueError('Part vendeur invalide')
            exact.append(Decimal(pool)*share/100)
        amounts=[int(x) for x in exact]
        for idx in sorted(range(len(exact)),key=lambda i:exact[i]-amounts[i],reverse=True)[:pool-sum(amounts)]:amounts[idx]+=1
        seller_amounts={id(x):a for x,a in zip(sellers,amounts)}
    for x in parts:
        if not str(x.get('name','')).strip(): raise ValueError('Bénéficiaire requis')
        value=x.get('value',0); method=x.get('method','percent')
        if method not in ['percent','fixed']: raise ValueError('Méthode de commission invalide')
        amount=rate(base,value) if method=='percent' else money(value)
        if x.get('kind')=='Vendeur': amount=seller_amounts[id(x)]
        uid=x.get('user_id') or None
        if uid: owned(c,'users',uid,u)
        c.execute('INSERT INTO commissions(company_id,shop_id,sale_id,partner,user_id,kind,base,method,value,amount) VALUES(?,?,?,?,?,?,?,?,?,?)',(u['company_id'],d['shop_id'],ident,x['name'],uid,x.get('kind','Guide'),base,method,str(value),amount))
    if paid: c.execute('INSERT INTO payments(company_id,entity,entity_id,amount,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],'sales',ident,paid,now(),u['id']))
    snapshot=invoice_data(c,dict(c.execute('SELECT * FROM sales WHERE id=?',(ident,)).fetchone()),u)
    c.execute('INSERT INTO invoices(sale_id,snapshot) VALUES(?,?)',(ident,json.dumps(snapshot)))
    audit(c,u,f'Vente #{ident} validée')
    return ident

def invoice_data(c,s,u):
    row=c.execute('SELECT snapshot FROM invoices WHERE sale_id=?',(s['id'],)).fetchone()
    if row:
        snapshot=json.loads(row['snapshot']); snapshot['sale']['paid']=s['paid'];snapshot['sale']['status']=s['status'];return snapshot
    company=dict(c.execute('SELECT * FROM companies WHERE id=?',(u['company_id'],)).fetchone())
    settings=c.execute('SELECT * FROM company_settings WHERE company_id=?',(u['company_id'],)).fetchone()
    if settings: company.update(dict(settings))
    return {'sale':dict(s),'lines':[dict(r) for r in c.execute('SELECT name,quantity,price FROM lines WHERE sale_id=?',(s['id'],))],'shop':dict(owned(c,'shops',s['shop_id'],u)),'company':company}

TABLES=['shops','products','clients','partners','expenses','employees','salaries','sales','commissions','movements','audit','users']
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,data,status=200,cookie=None):
        if isinstance(data,dict) and 'error' in data: data={**data,'error':translate(data['error'],self.headers.get('X-App-Language','fr'))}
        body=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(body)
    def do_GET(self): self.handle_request('GET')
    def do_POST(self): self.handle_request('POST')
    def handle_request(self,method):
        path=self.path.split('?')[0]
        if path=='/healthz' and method=='GET':
            with connect() as c: c.execute('SELECT 1').fetchone()
            return self.reply({'status':'ok'})
        if path=='/api/public-config' and method=='GET':
            config={'allow_signup':os.environ.get('BAZAR_ALLOW_SIGNUP')=='1'}
            if os.environ.get('BAZAR_DEMO_MODE')=='1': config['demo_mode']=True
            return self.reply(config)
        if not path.startswith('/api/'):
            if method!='GET': return self.reply({'error':'Introuvable'},404)
            file=ROOT/'static'/({'/':'index.html','/app.js':'app.js','/style.css':'style.css','/i18n.js':'i18n.js','/translations.json':'translations.json','/platform.js':'platform.js'}.get(path,'missing'))
            if not file.is_file(): return self.reply({'error':'Introuvable'},404)
            self.send_response(200); self.send_header('Content-Type',{'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8','json':'application/json; charset=utf-8'}[file.suffix[1:]])
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(file.read_bytes()); return
        try:
            length=int(self.headers.get('Content-Length',0))
            if length<0 or length>2000000: return self.reply({'error':'Requête trop volumineuse'},413)
            d=json.loads(self.rfile.read(length)) if method=='POST' else {}
            with connect() as c:
                if method=='POST' and path not in ['/api/invoice','/api/invoice-pdf','/api/invoice-email']: c.execute('BEGIN IMMEDIATE')
                if path=='/api/register' and method=='POST':
                    if os.environ.get('BAZAR_ALLOW_SIGNUP')!='1': return self.reply({'error':'Inscription sur invitation uniquement'},403)
                    if len(d['password'])<10: raise ValueError('Mot de passe : 10 caractères minimum')
                    if not d['email'].strip() or not d['company'].strip() or not d['name'].strip(): raise ValueError('Tous les champs sont obligatoires')
                    tid=c.execute('INSERT INTO companies(name) VALUES(?)',(d['company'],)).lastrowid
                    uid=c.execute('INSERT INTO users(company_id,name,email,password,role) VALUES(?,?,?,?,?)',(tid,d['name'],d['email'].strip().lower(),password(d['password']),'owner')).lastrowid
                    c.execute('INSERT INTO shops(company_id,name,address) VALUES(?,?,?)',(tid,'Boutique principale','Marrakech'))
                    saas.ensure_tenant(c,tid)
                    return self.login(c,uid)
                if path=='/api/login' and method=='POST':
                    email=str(d['email']).strip().lower()
                    key=hashlib.sha256((email+'|'+str(getattr(self,'client_address',('',))[0])).encode()).hexdigest()
                    attempt=c.execute('SELECT * FROM auth_attempts WHERE key=?',(key,)).fetchone()
                    if attempt and attempt['started_at']>time.time()-900 and attempt['failures']>=10: return self.reply({'error':'Trop de tentatives, réessayez dans 15 minutes'},429)
                    u=c.execute('SELECT * FROM users WHERE email=? AND active=1',(d['email'].strip().lower(),)).fetchone()
                    # Always perform the expensive comparison, including unknown accounts.
                    expected=u['password'] if u else password('unavailable')
                    if not hmac.compare_digest(password(d['password'],expected.split(':')[0]),expected) or not u:
                        if not attempt or attempt['started_at']<=time.time()-900: c.execute('INSERT INTO auth_attempts VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET failures=1,started_at=excluded.started_at',(key,time.time()))
                        else: c.execute('UPDATE auth_attempts SET failures=failures+1 WHERE key=?',(key,))
                        c.commit();return self.reply({'error':'Identifiants incorrects'},401)
                    c.execute('DELETE FROM auth_attempts WHERE key=?',(key,))
                    return self.login(c,u['id'])
                cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie',''))
                token=cookie.get('session'); session=c.execute('SELECT * FROM sessions WHERE token=? AND expires>?',(token.value if token else '',time.time())).fetchone()
                if not session: return self.reply({'error':'Connexion requise'},401)
                u=c.execute('SELECT * FROM users WHERE id=? AND active=1',(session['user_id'],)).fetchone()
                if not u: return self.reply({'error':'Compte désactivé'},401)
                if method=='POST' and self.headers.get('X-CSRF-Token')!=session['csrf']: return self.reply({'error':'Session invalide'},403)
                if path=='/api/logout':
                    c.execute('DELETE FROM sessions WHERE token=?',(session['token'],)); c.commit(); return self.reply({'ok':True},cookie='session=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict')
                if path=='/api/account/password' and method=='POST':
                    if not hmac.compare_digest(password(d['current_password'],u['password'].split(':')[0]),u['password']): raise ValueError('Mot de passe actuel incorrect')
                    if len(d['new_password'])<12 or d['new_password']==d['current_password']:raise ValueError('Choisissez un nouveau mot de passe de 12 caractères minimum')
                    c.execute('UPDATE users SET password=?,must_change_password=0 WHERE id=?',(password(d['new_password']),u['id']))
                    c.execute('DELETE FROM sessions WHERE user_id=? AND token!=?',(u['id'],session['token']));c.commit();return self.reply({'ok':True})
                identity={'user':{k:u[k] for k in ['id','name','email','role','must_change_password']},'csrf':session['csrf']}
                if u['must_change_password']:
                    if path=='/api/state': return self.reply({**identity,'password_required':True})
                    return self.reply({'error':'Vous devez changer votre mot de passe provisoire'},403)
                if u['role']=='platform_admin':
                    if path=='/api/state': return self.reply({**identity,**saas.platform_state(c,u)})
                    if path.startswith('/api/platform/') and method=='POST':
                        result=saas.routes(c,u,path,d,password,money);c.commit();return self.reply(result)
                    return self.reply({'error':'Accès réservé à l’espace éditeur'},403)
                if path.startswith('/api/platform/'):return self.reply({'error':'Accès réservé à l’éditeur SaaS'},403)
                subscription=saas.account(c,u['company_id'])
                if not subscription['accessible']:
                    if path=='/api/state':
                        company=c.execute('SELECT name FROM companies WHERE id=?',(u['company_id'],)).fetchone()['name']
                        public={key:subscription[key] for key in ['effective_status','period_end']}
                        return self.reply({**identity,'company':company,'blocked':True,'subscription':subscription if u['role']=='owner' else public})
                    return self.reply({'error':'Abonnement inactif : contactez votre fournisseur'},403)
                if path=='/api/state':
                    data={'user':{k:u[k] for k in ['id','name','email','role','must_change_password']},'csrf':session['csrf'],'company':c.execute('SELECT name FROM companies WHERE id=?',(u['company_id'],)).fetchone()['name']}
                    if u['role']=='owner':
                        data['subscription']=subscription
                        data['subscription_payments']=[dict(r) for r in c.execute('SELECT id,amount,currency,months,reference,method,paid_at,period_start,period_end FROM subscription_payments WHERE company_id=? ORDER BY id DESC',(u['company_id'],))]
                    allowed=TABLES if u['role']=='owner' else [t for t in TABLES if t!='users'] if u['role']=='manager' else ['shops','products','sales','commissions'] if u['role']=='seller' else ['shops','products']
                    for t in allowed:
                        cols='id,name,email,role,active' if t=='users' else '*'
                        query=f'SELECT {cols} FROM {t} WHERE company_id=?'; args=[u['company_id']]
                        if u['role']=='seller' and t=='commissions': query+=' AND user_id=?'; args.append(u['id'])
                        if u['role']=='seller' and t=='sales': query+=' AND (user_id=? OR id IN (SELECT sale_id FROM commissions WHERE user_id=?))'; args.extend([u['id'],u['id']])
                        if u['role']!='owner' and t in ['shops','products','sales','commissions','expenses','employees','salaries']:
                            query+=' AND '+('id' if t=='shops' else 'shop_id')+' IN (SELECT shop_id FROM user_shops WHERE user_id=?)'; args.append(u['id'])
                        rows=[dict(r) for r in c.execute(query+' ORDER BY id DESC',args)]
                        if u['role']=='manager' and t in ['clients','partners','movements','audit']:
                            rows=[] # Company-wide administrative histories are reserved to owners.

                        if u['role'] not in ['owner','manager'] and t=='products':
                            for row in rows: row.pop('cost',None)
                        if u['role']=='seller' and t=='sales':
                            for row in rows:
                                for field in ['cost','bank','shipping']: row.pop(field,None)
                        data[t]=rows
                    if u['role']=='owner':
                        settings=c.execute('SELECT * FROM company_settings WHERE company_id=?',(u['company_id'],)).fetchone(); data['settings']=dict(settings) if settings else {}
                    return self.reply(data)
                if path=='/api/sales' and method=='POST':
                    ident=sale_create(c,u,d); c.commit(); return self.reply({'id':ident})
                if path in ['/api/invoice','/api/invoice-pdf','/api/invoice-email'] and method=='POST':
                    s=owned(c,'sales',d['id'],u)
                    if u['role'] not in ['owner','manager'] and not (u['role']=='seller' and (s['user_id']==u['id'] or c.execute('SELECT 1 FROM commissions WHERE sale_id=? AND user_id=?',(s['id'],u['id'])).fetchone())): return self.reply({'error':'Accès interdit'},403)
                    selected=validate_language(d.get('language','fr'))
                    document=invoice_data(c,dict(s),u)
                    if path=='/api/invoice': return self.reply(document)
                    content=invoice_pdf(document,selected)
                    if path=='/api/invoice-pdf': return self.reply({'content':base64.b64encode(content).decode(),'filename':f'{"Invoice" if selected=="en" else "Facture"}-F-{s["id"]:06d}.pdf','language':selected})
                    if u['role'] not in ['owner','manager']: return self.reply({'error':'Accès interdit'},403)
                    if not os.environ.get('SMTP_HOST') or not os.environ.get('SMTP_FROM'): raise ValueError('Envoi non configuré : renseignez SMTP_HOST et SMTP_FROM sur le serveur')
                    address=str(d.get('email','')).strip()
                    if '@' not in address or '\n' in address or '\r' in address: raise ValueError('Adresse e-mail invalide')
                    message=EmailMessage();message['From']=os.environ['SMTP_FROM'];message['To']=address;message['Subject']=f'{"Your invoice" if selected=="en" else "Votre facture"} F-{s["id"]:06d} — {document["company"]["name"]}'
                    message.set_content('Hello,\nPlease find your invoice attached.\nThank you for your business.' if selected=='en' else 'Bonjour,\nVeuillez trouver votre facture en pièce jointe.\nMerci de votre confiance.')
                    message.add_attachment(content,maintype='application',subtype='pdf',filename=f'{"Invoice" if selected=="en" else "Facture"}-F-{s["id"]:06d}.pdf')
                    try:
                        with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.environ.get('SMTP_PORT','587')),timeout=15) as smtp:
                            smtp.starttls(context=ssl.create_default_context())
                            if os.environ.get('SMTP_USER'): smtp.login(os.environ['SMTP_USER'],os.environ.get('SMTP_PASSWORD',''))
                            smtp.send_message(message)
                    except (OSError,smtplib.SMTPException): raise ValueError('Envoi impossible : vérifiez la configuration SMTP')
                    audit(c,u,f'Facture #{s["id"]} envoyée par e-mail');c.commit();return self.reply({'ok':True})
                if u['role'] not in ['owner','manager']: return self.reply({'error':'Accès interdit'},403)
                if path=='/api/cancel' and method=='POST':
                    s=owned(c,'sales',d['id'],u)
                    if s['status']=='Annulée': return self.reply({'ok':True})
                    if c.execute('SELECT 1 FROM commissions WHERE sale_id=? AND paid>0',(s['id'],)).fetchone(): raise ValueError('Régularisez les commissions payées avant annulation')
                    for line in c.execute('SELECT * FROM lines WHERE sale_id=?',(s['id'],)).fetchall():
                        if line['product_id']:
                            c.execute('UPDATE products SET quantity=quantity+? WHERE id=?',(line['quantity'],line['product_id']))
                            c.execute('INSERT INTO movements(company_id,product_id,quantity,reason,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],line['product_id'],line['quantity'],f'Annulation #{s["id"]}',now(),u['id']))
                    c.execute("UPDATE sales SET status='Annulée' WHERE id=?",(s['id'],))
                    c.execute('UPDATE commissions SET amount=0 WHERE sale_id=?',(s['id'],)); audit(c,u,f'Annulation #{s["id"]}, encaissements à rembourser : {s["paid"]} centimes'); c.commit(); return self.reply({'ok':True})
                if path=='/api/pay' and method=='POST':
                    t=d['entity']
                    if t not in ['sales','commissions','expenses','salaries']: raise ValueError('Type invalide')
                    r=owned(c,t,d['id'],u); amount=money(d['amount']); due=r['total'] if t=='sales' else r['amount']
                    if amount<=0 or amount>due-r['paid'] or (t=='sales' and r['status']=='Annulée'): raise ValueError('Paiement invalide')
                    c.execute(f'UPDATE {t} SET paid=paid+? WHERE id=?',(amount,r['id']))
                    if t=='sales': c.execute('UPDATE sales SET status=? WHERE id=?',('Payée' if amount+r['paid']==due else 'Partielle',r['id']))
                    c.execute('INSERT INTO payments(company_id,entity,entity_id,amount,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],t,r['id'],amount,now(),u['id'])); audit(c,u,f'Règlement {t} #{r["id"]}'); c.commit(); return self.reply({'ok':True})
                if path=='/api/adjust' and method=='POST':
                    if Decimal(str(d['quantity']))!=Decimal(str(d['quantity'])).to_integral_value(): raise ValueError('Quantité entière requise')
                    p=owned(c,'products',d['id'],u); q=int(d['quantity'])
                    if q<0 or not d.get('reason','').strip(): raise ValueError('Quantité et motif requis')
                    c.execute('UPDATE products SET quantity=? WHERE id=?',(q,p['id']))
                    c.execute('INSERT INTO movements(company_id,product_id,quantity,reason,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],p['id'],q-p['quantity'],d['reason'],now(),u['id'])); audit(c,u,f'Ajustement stock #{p["id"]}'); c.commit(); return self.reply({'ok':True})
                if path=='/api/update' and method=='POST':
                    t=d['entity']; v=d['values']
                    fields={'products':['name','reference','category','cost','price','active'],'clients':['name','email','phone','address'],'partners':['name','kind'],'shops':['name','address'],'employees':['name','position','salary'],'users':['name','active','role','password']}
                    if t not in fields: raise ValueError('Modification non autorisée')
                    if t in ['users','shops'] and u['role']!='owner': return self.reply({'error':'Accès interdit'},403)
                    r=owned(c,t,d['id'],u); values={k:v[k] for k in fields[t] if k in v}
                    if 'name' in values and not str(values['name']).strip(): raise ValueError('Nom obligatoire')
                    for f in ['cost','price','salary']:
                        if f in values: values[f]=money(values[f])
                    if 'active' in values and values['active'] not in [0,1]: raise ValueError('Statut invalide')
                    if t=='users':
                        if values.get('active')==1 and not r['active']: saas.quota(c,u['company_id'],'users')
                        if r['id']==u['id'] and (values.get('active',1)==0 or values.get('role',u['role'])!='owner'): raise ValueError('Vous ne pouvez pas retirer votre propre accès administrateur')
                        if 'role' in values and values['role'] not in ['owner','manager','seller','operator']: raise ValueError('Rôle invalide')
                        if values.get('password'):
                            if len(values['password'])<10: raise ValueError('Mot de passe : 10 caractères minimum')
                            values['password']=password(values['password']); values['must_change_password']=1
                        else: values.pop('password',None)
                        if 'assigned_shop' in v:
                            owned(c,'shops',v['assigned_shop'],u);c.execute('DELETE FROM user_shops WHERE user_id=?',(r['id'],));c.execute('INSERT INTO user_shops VALUES(?,?)',(r['id'],v['assigned_shop']))
                        if 'password' in values or values.get('active')==0: c.execute('DELETE FROM sessions WHERE user_id=?',(r['id'],))
                    if not values: raise ValueError('Aucune modification')
                    if t=='products' and values.get('reference') and c.execute('SELECT 1 FROM products WHERE company_id=? AND shop_id=? AND reference=? AND id!=?',(u['company_id'],r['shop_id'],values['reference'],r['id'])).fetchone(): raise ValueError('Référence déjà utilisée')
                    c.execute(f'UPDATE {t} SET '+','.join(k+'=?' for k in values)+' WHERE id=?',list(values.values())+[r['id']]);audit(c,u,f'Modification {t} #{r["id"]}');c.commit();return self.reply({'ok':True})
                if path=='/api/company-settings' and method=='POST':
                    if u['role']!='owner': return self.reply({'error':'Accès interdit'},403)
                    logo=d.get('logo','')
                    if logo:
                        if not logo.startswith(('data:image/png;base64,','data:image/jpeg;base64,')) or len(logo)>700000: raise ValueError('Logo PNG ou JPEG, maximum 500 Ko')
                        from PIL import Image
                        try:
                            with Image.open(io.BytesIO(base64.b64decode(logo.split(',')[1],validate=True))) as image:
                                if image.width*image.height>16000000: raise ValueError('Logo trop grand')
                                image.verify()
                        except Exception: raise ValueError('Image invalide')
                    c.execute('INSERT INTO company_settings(company_id,address,ice,tax_id,logo) VALUES(?,?,?,?,?) ON CONFLICT(company_id) DO UPDATE SET address=excluded.address,ice=excluded.ice,tax_id=excluded.tax_id,logo=excluded.logo',(u['company_id'],d.get('address',''),d.get('ice',''),d.get('tax_id',''),logo))
                    audit(c,u,'Paramètres de facturation modifiés');c.commit();return self.reply({'ok':True})
                if path=='/api/import-preview' and method=='POST':
                    raw=base64.b64decode(d['content'],validate=True)
                    if d['filename'].lower().endswith('.xlsx'):
                        with zipfile.ZipFile(io.BytesIO(raw)) as z:
                            if sum(x.file_size for x in z.infolist())>20000000: raise ValueError('Classeur trop volumineux')
                            ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                            strings=[]
                            if 'xl/sharedStrings.xml' in z.namelist():
                                strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
                            sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml')); data=[]
                            for row in sheet.findall('.//m:sheetData/m:row',ns):
                                values=[]
                                for cell in row.findall('m:c',ns):
                                    letters=''.join(x for x in cell.get('r','A') if x.isalpha()); idx=0
                                    for letter in letters: idx=idx*26+ord(letter.upper())-64
                                    if idx>100: raise ValueError('Maximum 100 colonnes')
                                    while len(values)<idx: values.append('')
                                    value=cell.find('m:v',ns)
                                    text=value.text if value is not None else ''.join(cell.find('m:is',ns).itertext()) if cell.find('m:is',ns) is not None else ''
                                    values[idx-1]=strings[int(text)] if cell.get('t')=='s' else text
                                data.append(values)
                    else:
                        text=raw.decode('utf-8-sig'); dialect=csv.Sniffer().sniff(text[:4096],delimiters=',;\t'); data=list(csv.reader(io.StringIO(text),dialect))
                    if not data or len(data)>1001: raise ValueError('Import : 1 à 1000 lignes maximum')
                    return self.reply({'headers':data[0],'rows':data[1:]})
                if path=='/api/import' and method=='POST':
                    owned(c,'shops',d['shop_id'],u)
                    if not 0<len(d['rows'])<=1000: raise ValueError('Import : 1 à 1000 lignes maximum')
                    count=0; refs=set()
                    for row in d['rows']:
                        name=str(row.get('name','')).strip(); ref=str(row.get('reference','')).strip()
                        if not name or not ref: raise ValueError('Nom et référence obligatoires sur chaque ligne')
                        if ref in refs or c.execute('SELECT 1 FROM products WHERE company_id=? AND shop_id=? AND reference=?',(u['company_id'],d['shop_id'],ref)).fetchone(): raise ValueError('Référence en doublon : '+ref)
                        refs.add(ref); q=Decimal(str(row.get('quantity',0)))
                        if not q.is_finite() or q<0 or q!=q.to_integral_value(): raise ValueError('Quantité entière positive requise : '+ref)
                        ident=c.execute('INSERT INTO products(company_id,shop_id,name,reference,category,cost,price,quantity) VALUES(?,?,?,?,?,?,?,?)',(u['company_id'],d['shop_id'],name,ref,str(row.get('category','')),money(row.get('cost',0)),money(row.get('price',0)),int(q))).lastrowid
                        c.execute('INSERT INTO movements(company_id,product_id,quantity,reason,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],ident,int(q),'Import de stock',now(),u['id'])); count+=1
                    audit(c,u,f'Import de {count} articles'); c.commit(); return self.reply({'count':count})
                if path=='/api/create' and method=='POST':
                    t=d['entity']; v=d['values']; fields={
                        'shops':['name','address'],'products':['shop_id','name','reference','category','cost','price','quantity'],
                        'clients':['name','email','phone','address'],'partners':['name','kind'],
                        'expenses':['shop_id','date','name','category','amount'],'employees':['shop_id','name','position','salary'],
                        'salaries':['shop_id','employee_id','name','date','amount'],'users':['name','email','password','role']}
                    if t not in fields: raise ValueError('Type invalide')
                    if t in ['shops','users']: saas.quota(c,u['company_id'],t)
                    if t in ['users','shops'] and u['role']!='owner': return self.reply({'error':'Administration réservée au propriétaire'},403)
                    if t=='users' and v.get('role')!='owner': owned(c,'shops',v['assigned_shop'],u)
                    if not str(v.get('name','')).strip(): raise ValueError('Nom obligatoire')
                    if 'shop_id' in fields[t]: owned(c,'shops',v['shop_id'],u)
                    if t=='salaries':
                        employee=owned(c,'employees',v['employee_id'],u)
                        if int(v['shop_id'])!=employee['shop_id']: raise ValueError('Boutique incompatible')
                    if t=='users':
                        if v['role'] not in ['owner','manager','seller','operator']: raise ValueError('Rôle invalide')
                        if len(v['password'])<10: raise ValueError('Mot de passe trop court')
                        v['password']=password(v['password']); v['email']=v['email'].lower().strip()
                    for f in ['cost','price','amount','salary']:
                        if f in fields[t]: v[f]=money(v[f])
                    if t=='products':
                        if v.get('reference') and c.execute('SELECT 1 FROM products WHERE company_id=? AND shop_id=? AND reference=?',(u['company_id'],v['shop_id'],v['reference'])).fetchone(): raise ValueError('Référence déjà utilisée')
                        if Decimal(str(v['quantity']))!=Decimal(str(v['quantity'])).to_integral_value(): raise ValueError('Quantité entière requise')
                        v['quantity']=int(v['quantity'])
                        if v['quantity']<0: raise ValueError('Quantité invalide')
                    keys=['company_id']+fields[t]; vals=[u['company_id']]+[v.get(f,'') for f in fields[t]]
                    ident=c.execute(f'INSERT INTO {t}({",".join(keys)}) VALUES({",".join("?" for _ in keys)})',vals).lastrowid
                    if t=='users' and v['role']!='owner': c.execute('INSERT INTO user_shops(user_id,shop_id) VALUES(?,?)',(ident,v['assigned_shop']))
                    if t=='products': c.execute('INSERT INTO movements(company_id,product_id,quantity,reason,date,user_id) VALUES(?,?,?,?,?,?)',(u['company_id'],ident,v['quantity'],'Stock initial',now(),u['id']))
                    audit(c,u,f'Création {t} #{ident}'); c.commit(); return self.reply({'id':ident})
                return self.reply({'error':'Introuvable'},404)
        except PermissionError as e: self.reply({'error':str(e)},403)
        except sqlite3.IntegrityError: self.reply({'error':'Donnée déjà existante ou référence invalide'},400)
        except (ValueError,KeyError,TypeError,ArithmeticError) as e: self.reply({'error':str(e) or 'Données invalides'},400)
        except Exception:
            import traceback; traceback.print_exc(); self.reply({'error':'Erreur interne'},500)
    def login(self,c,uid):
        token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24)
        c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(token,uid,time.time()+43200,csrf)); c.commit()
        secure='; Secure' if os.environ.get('COOKIE_SECURE')=='1' else ''
        self.reply({'ok':True},cookie=f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200{secure}')

if __name__=='__main__':
    init()
    print('Bazar • serveur sur le port '+os.environ.get('PORT','3000'),flush=True)
    ThreadingHTTPServer((os.environ.get('HOST','0.0.0.0'),int(os.environ.get('PORT','3000'))),Handler).serve_forever()
