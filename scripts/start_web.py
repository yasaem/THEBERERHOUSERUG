"""Start a hosted preview; publisher credentials come only from secure settings."""
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import saas


def prepare_web():
    os.umask(0o077)
    external = os.environ.get('PUBLIC_BASE_URL') or os.environ.get('RENDER_EXTERNAL_URL')
    if external:
        parts = urlsplit(external)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.path not in ('', '/') or parts.query or parts.fragment:
            raise ValueError('PUBLIC_BASE_URL doit être une origine HTTPS valide')
        os.environ['PUBLIC_BASE_URL'] = external.rstrip('/')
    os.environ['BAZAR_ALLOW_SIGNUP'] = '0'
    os.environ['COOKIE_SECURE'] = '1'
    server.init()
    with server.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        existing = c.execute("SELECT 1 FROM users WHERE role='platform_admin' LIMIT 1").fetchone()
        if not existing:
            email = os.environ.get('BAZAR_PUBLISHER_EMAIL', '')
            raw = os.environ.get('BAZAR_PUBLISHER_PASSWORD', '')
            name = os.environ.get('BAZAR_PUBLISHER_NAME', 'Administrateur')
            if not email or not raw:
                raise ValueError('Configurez BAZAR_PUBLISHER_EMAIL et BAZAR_PUBLISHER_PASSWORD dans les paramètres sécurisés de l’hébergeur')
            email, name = saas.validate_identity(email, name, raw)
            if c.execute('SELECT 1 FROM users WHERE email=?', (email,)).fetchone():
                raise ValueError('Adresse de compte éditeur déjà utilisée ; aucune promotion automatique effectuée')
            uid = c.execute("INSERT INTO users(company_id,name,email,password,role) VALUES(NULL,?,?,?,'platform_admin')", (name, email, server.password(raw))).lastrowid
            saas.log(c, uid, None, 'Compte éditeur initialisé depuis les paramètres sécurisés')
    # Do not pass the bootstrap password to Gunicorn workers.
    os.environ.pop('BAZAR_PUBLISHER_PASSWORD', None)


if __name__ == '__main__':
    try:
        prepare_web()
    except ValueError as error:
        raise SystemExit(str(error))
    os.execv(sys.executable, [sys.executable, '-m', 'gunicorn', '--config', 'gunicorn.conf.py', 'wsgi:application'])
