"""Monthly management payroll: immutable identity snapshots and explicit payments."""
import json, re, base64
from decimal import Decimal, ROUND_HALF_UP
from documents import payroll_pdf

def init(c):
    c.execute('CREATE TABLE IF NOT EXISTS payroll_policy(company_id INTEGER PRIMARY KEY REFERENCES companies,config TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS payroll_profiles(employee_id INTEGER PRIMARY KEY REFERENCES employees,cin TEXT,cnss TEXT,dependants INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS payroll_details(salary_id INTEGER PRIMARY KEY REFERENCES salaries,base INTEGER,bonus INTEGER,deductions INTEGER,snapshot TEXT)')

def period(value):
    value=str(value)
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',value): raise ValueError('Période invalide')
    return value

def check_period(c,u,employee,date):
    month=period(str(date)[:7])
    if c.execute('SELECT 1 FROM salaries WHERE company_id=? AND employee_id=? AND substr(date,1,7)=?',(u['company_id'],employee,month)).fetchone(): raise ValueError('Le salaire de cet employé existe déjà pour ce mois')

def snapshot(c,u,e):
    company=dict(c.execute('SELECT * FROM companies WHERE id=?',(u['company_id'],)).fetchone())
    settings=c.execute('SELECT * FROM company_settings WHERE company_id=?',(u['company_id'],)).fetchone()
    if settings: company.update(dict(settings))
    return {'company':company,'employee':dict(e)}

def route(c,u,path,d,owned,money,audit):
    if path=='/api/payroll/policy':
        if u['role']!='owner': raise PermissionError('Accès interdit')
        policy=d['policy']; validate_policy(policy)
        c.execute('INSERT INTO payroll_policy VALUES(?,?) ON CONFLICT(company_id) DO UPDATE SET config=excluded.config',(u['company_id'],json.dumps(policy)))
        audit(c,u,'Paramètres de paie marocaine modifiés'); return {'ok':True}
    if path=='/api/payroll/profile':
        e=owned(c,'employees',d['id'],u); n=int(d.get('dependants',0))
        if not 0<=n<=6: raise ValueError('Personnes à charge : de 0 à 6')
        c.execute('INSERT INTO payroll_profiles VALUES(?,?,?,?) ON CONFLICT(employee_id) DO UPDATE SET cin=excluded.cin,cnss=excluded.cnss,dependants=excluded.dependants',(e['id'],str(d.get('cin','')),str(d.get('cnss','')),n))
        return {'ok':True}
    if path=='/api/payroll/prepare':
        month=period(d['month']); shop=d.get('shop_id')
        if shop: owned(c,'shops',shop,u)
        employees=c.execute('SELECT * FROM employees WHERE company_id=? ORDER BY id',(u['company_id'],)).fetchall()
        policy_row=c.execute('SELECT config FROM payroll_policy WHERE company_id=?',(u['company_id'],)).fetchone()
        policy=json.loads(policy_row['config']) if policy_row else None
        if d.get('morocco'):
            if not policy or not policy.get('validated') or str(policy['year'])!=month[:4]: raise ValueError('Validez les paramètres de paie pour cette année avant de générer les bulletins marocains')
        count=0
        for e in employees:
            if shop and e['shop_id']!=int(shop): continue
            if u['role']!='owner' and not c.execute('SELECT 1 FROM user_shops WHERE user_id=? AND shop_id=?',(u['id'],e['shop_id'])).fetchone(): continue
            if c.execute('SELECT 1 FROM salaries WHERE company_id=? AND employee_id=? AND substr(date,1,7)=?',(u['company_id'],e['id'],month)).fetchone(): continue
            snap=snapshot(c,u,e); base=e['salary']; amount=base; bonus=deductions=0
            if d.get('morocco'):
                profile=c.execute('SELECT * FROM payroll_profiles WHERE employee_id=?',(e['id'],)).fetchone()
                if not profile or not profile['cin'] or not profile['cnss']: raise ValueError('Complétez la CIN et le numéro CNSS de chaque employé')
                calculation=calculate(base,policy,profile['dependants'])
                amount=calculation['net']; deductions=base-amount
                snap.update({'regulatory':calculation,'policy':policy,'profile':dict(profile)})
            ident=c.execute('INSERT INTO salaries(company_id,shop_id,employee_id,name,date,amount) VALUES(?,?,?,?,?,?)',(u['company_id'],e['shop_id'],e['id'],e['name'],month+'-01',amount)).lastrowid
            c.execute('INSERT INTO payroll_details VALUES(?,?,0,0,?)',(ident,base,json.dumps(snap)))
            if deductions: c.execute('UPDATE payroll_details SET deductions=? WHERE salary_id=?',(deductions,ident))
            count+=1
        audit(c,u,f'Préparation salaires {month} : {count}')
        return {'created':count}
    r=dict(owned(c,'salaries',d['id'],u))
    details=c.execute('SELECT * FROM payroll_details WHERE salary_id=?',(r['id'],)).fetchone()
    if path=='/api/payroll/adjust':
        if r['paid']: raise ValueError('Un salaire déjà réglé ne peut plus être modifié')
        if details and json.loads(details['snapshot']).get('regulatory'): raise ValueError('Bulletin marocain figé : les éléments variables doivent être préparés avant génération')
        base=details['base'] if details else r['amount']; bonus=money(d.get('bonus',0)); deductions=money(d.get('deductions',0))
        if deductions>base+bonus: raise ValueError('Les retenues dépassent le salaire')
        snap=details['snapshot'] if details else json.dumps(snapshot(c,u,owned(c,'employees',r['employee_id'],u)))
        c.execute('INSERT INTO payroll_details VALUES(?,?,?,?,?) ON CONFLICT(salary_id) DO UPDATE SET bonus=excluded.bonus,deductions=excluded.deductions',(r['id'],base,bonus,deductions,snap))
        c.execute('UPDATE salaries SET amount=? WHERE id=?',(base+bonus-deductions,r['id']))
        audit(c,u,f'Ajustement salaire #{r["id"]}')
        return {'ok':True}
    if path=='/api/payroll/pdf':
        snap=json.loads(details['snapshot']) if details else snapshot(c,u,owned(c,'employees',r['employee_id'],u))
        amounts=dict(details) if details else {'base':r['amount'],'bonus':0,'deductions':0}
        content=payroll_pdf(snap,r,amounts,d.get('language','fr'))
        return {'content':base64.b64encode(content).decode(),'filename':f'Paie-{r["id"]}-{r["date"][:7]}.pdf'}
    raise ValueError('Action inconnue')


def validate_policy(p):
    if not isinstance(p,dict) or not isinstance(p.get('year'),int) or not 2025<=p['year']<=2100: raise ValueError('Année de paie invalide')
    for key in ['cnss_rate','amo_rate','professional_low_rate','professional_high_rate']:
        v=Decimal(str(p[key]))
        if not v.is_finite() or not 0<=v<=100: raise ValueError('Pourcentage invalide')
    for key in ['cnss_ceiling','professional_threshold','professional_cap','family_annual']:
        v=Decimal(str(p[key]))
        if not v.is_finite() or not 0<=v<=10000000: raise ValueError('Montant invalide')
    previous=-1
    if not isinstance(p['brackets'],list) or not 1<=len(p['brackets'])<=20: raise ValueError('Barème IR invalide')
    for threshold,tax_rate,offset in p['brackets']:
        if not all(Decimal(str(v)).is_finite() for v in [threshold,tax_rate,offset]) or threshold<=previous or not 0<=tax_rate<=100 or offset<0: raise ValueError('Barème IR invalide')
        previous=threshold
    if p['brackets'][0][0]!=0 or p.get('validated') is not True: raise ValueError('Validation du barème requise')

def calculate(gross,p,dependants):
    validate_policy(p)
    def cents(v): return int(Decimal(str(v)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    def pct(base,r): return cents(Decimal(base)*Decimal(str(r))/100)
    social=pct(min(gross,cents(Decimal(str(p['cnss_ceiling']))*100)),p['cnss_rate'])
    amo=pct(gross,p['amo_rate'])
    annual=gross*12
    expense=min(pct(annual,p['professional_low_rate'] if annual<=Decimal(str(p['professional_threshold']))*100 else p['professional_high_rate']),cents(Decimal(str(p['professional_cap']))*100))
    taxable=max(0,annual-(social+amo)*12-expense)
    bracket=p['brackets'][0]
    for b in p['brackets']:
        if taxable>=Decimal(str(b[0]))*100: bracket=b
    annual_tax=max(0,pct(taxable,bracket[1])-cents(Decimal(str(bracket[2]))*100)-cents(Decimal(str(p['family_annual']))*100)*dependants)
    tax=cents(Decimal(annual_tax)/12)
    return {'gross':gross,'cnss':social,'amo':amo,'professional_annual':expense,'taxable_annual':taxable,'ir':tax,'net':max(0,gross-social-amo-tax)}
