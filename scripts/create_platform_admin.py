"""Local-only publisher bootstrap. Never pass passwords as command-line arguments."""
import getpass
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
import saas

def main():
    server.init()
    name=input('Nom / Name : ').strip()
    email=input('E-mail : ').strip().lower()
    raw=getpass.getpass('Mot de passe / Password (12+): ')
    confirmation=getpass.getpass('Confirmation : ')
    if raw!=confirmation:raise ValueError('Les mots de passe ne correspondent pas')
    email,name=saas.validate_identity(email,name,raw)
    with server.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        uid=c.execute("INSERT INTO users(company_id,name,email,password,role) VALUES(NULL,?,?,?,'platform_admin')",(name,email,server.password(raw))).lastrowid
        saas.log(c,uid,None,'Compte éditeur initialisé depuis le terminal')
    print('Compte éditeur créé. Connectez-vous depuis l’application. / Publisher account created.')

if __name__=='__main__':
    try:main()
    except (ValueError,sqlite3.IntegrityError) as e:raise SystemExit(str(e))
