"""Publisher administration, tenant subscriptions and centrally enforced quotas."""
import calendar
import datetime as dt
import hashlib
import json
import secrets
from decimal import Decimal

UTC=dt.timezone.utc

def whole(value):
    number=Decimal(str(value))
    if not number.is_finite() or number!=number.to_integral_value():raise ValueError('Nombre entier requis')
    return int(number)

def current(): return dt.datetime.now(UTC)
def stamp(value): return value.astimezone(UTC).isoformat(timespec='seconds')
def parse(value): return dt.datetime.fromisoformat(value).astimezone(UTC)
def month_after(value,months):
    total=value.year*12+value.month-1+months
    year,month=divmod(total,12);month+=1
    return value.replace(year=year,month=month,day=min(value.day,calendar.monthrange(year,month)[1]))

def init(c):
    c.executescript('''
CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY,name TEXT NOT NULL,price INTEGER NOT NULL CHECK(price>=0),max_shops INTEGER NOT NULL CHECK(max_shops>0),max_users INTEGER NOT NULL CHECK(max_users>0),active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS tenant_accounts(company_id INTEGER PRIMARY KEY REFERENCES companies,enabled INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS subscriptions(company_id INTEGER PRIMARY KEY REFERENCES companies,plan_id INTEGER NOT NULL REFERENCES plans,status TEXT NOT NULL,period_start TEXT NOT NULL,period_end TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS subscription_payments(id INTEGER PRIMARY KEY,company_id INTEGER NOT NULL REFERENCES companies,plan_id INTEGER NOT NULL REFERENCES plans,amount INTEGER NOT NULL,currency TEXT NOT NULL DEFAULT 'MAD',months INTEGER NOT NULL,reference TEXT NOT NULL,method TEXT NOT NULL,paid_at TEXT NOT NULL,period_start TEXT NOT NULL,period_end TEXT NOT NULL,actor_id INTEGER REFERENCES users,idempotency TEXT NOT NULL UNIQUE,fingerprint TEXT NOT NULL,UNIQUE(company_id,reference));
CREATE TABLE IF NOT EXISTS platform_audit(id INTEGER PRIMARY KEY,actor_id INTEGER REFERENCES users,company_id INTEGER REFERENCES companies,event TEXT NOT NULL,date TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS auth_attempts(key TEXT PRIMARY KEY,failures INTEGER NOT NULL,started_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS subscription_payments_company ON subscription_payments(company_id,paid_at);
''')
    columns={r[1] for r in c.execute('PRAGMA table_info(users)')}
    if 'must_change_password' not in columns:c.execute('ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0')
    c.execute("INSERT OR IGNORE INTO plans(id,name,price,max_shops,max_users) VALUES(1,'Essai / Trial',0,3,10)")
    for row in c.execute('SELECT id FROM companies').fetchall():ensure_tenant(c,row['id'])

def ensure_tenant(c,company_id):
    start=current();end=start+dt.timedelta(days=14)
    c.execute('INSERT OR IGNORE INTO tenant_accounts(company_id,created_at) VALUES(?,?)',(company_id,stamp(start)))
    c.execute("INSERT OR IGNORE INTO subscriptions VALUES(?,1,'trial',?,?)",(company_id,stamp(start),stamp(end)))

def log(c,actor,company,event):
    c.execute('INSERT INTO platform_audit(actor_id,company_id,event,date) VALUES(?,?,?,?)',(actor,company,event,stamp(current())))

def account(c,company_id):
    row=c.execute('SELECT s.*,p.name AS plan_name,p.price,p.max_shops,p.max_users,a.enabled FROM subscriptions s JOIN plans p ON p.id=s.plan_id JOIN tenant_accounts a ON a.company_id=s.company_id WHERE s.company_id=?',(company_id,)).fetchone()
    if not row:raise ValueError('Abonnement introuvable')
    result=dict(row);expired=parse(result['period_end'])<=current()
    result['effective_status']='suspended' if not result['enabled'] else 'expired' if expired else result['status']
    result['accessible']=bool(result['enabled'] and not expired and result['status'] in ['trial','active'])
    result['shops_used']=c.execute('SELECT COUNT(*) FROM shops WHERE company_id=?',(company_id,)).fetchone()[0]
    result['users_used']=c.execute('SELECT COUNT(*) FROM users WHERE company_id=? AND active=1',(company_id,)).fetchone()[0]
    return result

def quota(c,company_id,entity):
    a=account(c,company_id)
    if not a['accessible']:raise PermissionError('Abonnement inactif : contactez votre fournisseur')
    if entity=='shops' and a['shops_used']>=a['max_shops']:raise ValueError('Limite de boutiques atteinte pour cette formule')
    if entity=='users' and a['users_used']>=a['max_users']:raise ValueError('Limite d’utilisateurs atteinte pour cette formule')

def validate_identity(email,name,raw):
    email=str(email).strip().lower();name=str(name).strip()
    if '@' not in email or any(x.isspace() for x in email) or len(email)>254:raise ValueError('Adresse e-mail invalide')
    if not name:raise ValueError('Nom obligatoire')
    if len(raw)<12:raise ValueError('Mot de passe : 12 caractères minimum')
    return email,name

def create_company(c,d,password,actor):
    email,name=validate_identity(d['email'],d['owner_name'],d['password'])
    title=str(d['company_name']).strip();shop=str(d['shop_name']).strip()
    if not title or not shop:raise ValueError('Entreprise et boutique obligatoires')
    plan=c.execute('SELECT * FROM plans WHERE id=? AND active=1',(d['plan_id'],)).fetchone()
    if not plan:raise ValueError('Formule introuvable')
    company=c.execute('INSERT INTO companies(name) VALUES(?)',(title,)).lastrowid
    c.execute('INSERT INTO users(company_id,name,email,password,role,must_change_password) VALUES(?,?,?,?,?,1)',(company,name,email,password(d['password']),'owner'))
    c.execute('INSERT INTO shops(company_id,name,address) VALUES(?,?,?)',(company,shop,d.get('address','')))
    ensure_tenant(c,company)
    c.execute('UPDATE subscriptions SET plan_id=? WHERE company_id=?',(plan['id'],company))
    log(c,actor,company,'Entreprise créée, essai de 14 jours')
    return {'id':company}

def platform_state(c,u):
    tenants=[]
    for company in c.execute('SELECT * FROM companies ORDER BY id DESC'):
        a=account(c,company['id']);owner=c.execute("SELECT id,name,email FROM users WHERE company_id=? AND role='owner' ORDER BY id LIMIT 1",(company['id'],)).fetchone()
        tenants.append({**dict(company),'owner_name':owner['name'] if owner else '', 'email':owner['email'] if owner else '', 'owner_id':owner['id'] if owner else None, 'subscription':a})
    return {'platform':True,'companies':tenants,'plans':[dict(r) for r in c.execute('SELECT * FROM plans ORDER BY id')],
            'subscription_payments':[dict(r) for r in c.execute('SELECT p.*,co.name AS company_name FROM subscription_payments p JOIN companies co ON co.id=p.company_id ORDER BY p.id DESC LIMIT 200')],
            'platform_audit':[dict(r) for r in c.execute('SELECT * FROM platform_audit ORDER BY id DESC LIMIT 100')]}

def routes(c,u,path,d,password,money):
    if u['role']!='platform_admin':raise PermissionError('Accès réservé à l’éditeur SaaS')
    if path=='/api/platform/companies':return create_company(c,d,password,u['id'])
    if path=='/api/platform/plans':
        name=str(d['name']).strip();price=money(d['price']);shops=whole(d['max_shops']);users=whole(d['max_users'])
        if not name or price<=0 or not 1<=shops<=1000 or not 1<=users<=10000:raise ValueError('Paramètres de formule invalides')
        ident=c.execute('INSERT INTO plans(name,price,max_shops,max_users) VALUES(?,?,?,?)',(name,price,shops,users)).lastrowid
        log(c,u['id'],None,f'Formule #{ident} créée');return {'id':ident}
    company=int(d['company_id']);a=account(c,company)
    if path=='/api/platform/reset-owner':
        owner=c.execute("SELECT * FROM users WHERE id=? AND company_id=? AND role='owner'",(d['owner_id'],company)).fetchone()
        if not owner:raise ValueError('Administrateur client introuvable')
        if len(d['password'])<12:raise ValueError('Mot de passe : 12 caractères minimum')
        c.execute('UPDATE users SET password=?,must_change_password=1 WHERE id=?',(password(d['password']),owner['id']))
        c.execute('DELETE FROM sessions WHERE user_id=?',(owner['id'],))
        log(c,u['id'],company,'Accès de l’administrateur client réinitialisé');return {'ok':True}
    if path=='/api/platform/access':
        if not isinstance(d['enabled'],bool):raise ValueError('Statut invalide')
        c.execute('UPDATE tenant_accounts SET enabled=? WHERE company_id=?',(int(d['enabled']),company))
        log(c,u['id'],company,'Accès réactivé' if d['enabled'] else 'Accès suspendu');return {'ok':True}
    if path=='/api/platform/plan':
        p=c.execute('SELECT * FROM plans WHERE id=? AND active=1',(d['plan_id'],)).fetchone()
        if not p:raise ValueError('Formule introuvable')
        if a['shops_used']>p['max_shops'] or a['users_used']>p['max_users']:raise ValueError('La formule ne couvre pas l’utilisation actuelle')
        c.execute('UPDATE subscriptions SET plan_id=? WHERE company_id=?',(p['id'],company))
        log(c,u['id'],company,f'Formule #{p["id"]} affectée');return {'ok':True}
    if path=='/api/platform/payment':
        months=whole(d['months']);amount=money(d['amount']);reference=str(d['reference']).strip();method=d['method'];key=str(d['key'])
        if not 1<=months<=24 or amount<=0 or not reference or len(key)<16:raise ValueError('Règlement d’abonnement invalide')
        if method not in ['bank_transfer','cash','other']:raise ValueError('Moyen de paiement invalide')
        fingerprint=hashlib.sha256(json.dumps([company,months,amount,reference,method],separators=(',',':')).encode()).hexdigest()
        old=c.execute('SELECT id,fingerprint FROM subscription_payments WHERE idempotency=?',(key,)).fetchone()
        if old:
            if old['fingerprint']!=fingerprint:raise ValueError('Clé de règlement déjà utilisée avec des données différentes')
            return {'id':old['id']}
        if amount!=a['price']*months:raise ValueError('Le montant doit correspondre à la formule et à la durée')
        start=max(current(),parse(a['period_end']));end=month_after(start,months)
        ident=c.execute('INSERT INTO subscription_payments(company_id,plan_id,amount,months,reference,method,paid_at,period_start,period_end,actor_id,idempotency,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(company,a['plan_id'],amount,months,reference,method,stamp(current()),stamp(start),stamp(end),u['id'],key,fingerprint)).lastrowid
        c.execute("UPDATE subscriptions SET status='active',period_start=?,period_end=? WHERE company_id=?",(stamp(start),stamp(end),company))
        log(c,u['id'],company,f'Règlement d’abonnement #{ident} enregistré');return {'id':ident}
    raise ValueError('Action SaaS inconnue')
