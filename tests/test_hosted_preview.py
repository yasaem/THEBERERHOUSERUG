import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import server

spec=importlib.util.spec_from_file_location('hosted_preview',Path(__file__).resolve().parents[1]/'scripts/start_web.py')
hosted=importlib.util.module_from_spec(spec);spec.loader.exec_module(hosted)

class HostedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.original_db=server.DB;server.DB=self.tmp.name+'/preview.sqlite3'
        self.old_umask=os.umask(0o077)
    def tearDown(self):
        server.DB=self.original_db;self.tmp.cleanup();os.umask(self.old_umask)
    def test_secure_bootstrap_once_and_no_password_in_worker_environment(self):
        with patch.dict(os.environ,{'PUBLIC_BASE_URL':'','RENDER_EXTERNAL_URL':'https://preview.onrender.com','BAZAR_PUBLISHER_EMAIL':'publisher@example.test','BAZAR_PUBLISHER_NAME':'Fixture','BAZAR_PUBLISHER_PASSWORD':'Fixture-password-123'}):
            hosted.prepare_web()
            self.assertNotIn('BAZAR_PUBLISHER_PASSWORD',os.environ)
            self.assertEqual(os.environ['PUBLIC_BASE_URL'],'https://preview.onrender.com')
            self.assertEqual(os.environ['COOKIE_SECURE'],'1')
            self.assertEqual(os.environ['BAZAR_ALLOW_SIGNUP'],'0')
            with server.connect() as c:before=c.execute("SELECT password FROM users WHERE role='platform_admin'").fetchone()[0]
            os.environ['BAZAR_PUBLISHER_PASSWORD']='Another-password-123';hosted.prepare_web()
            with server.connect() as c:
                rows=c.execute("SELECT password FROM users WHERE role='platform_admin'").fetchall()
                self.assertEqual(len(rows),1);self.assertEqual(rows[0][0],before)
    def test_no_default_admin_or_public_signup_on_missing_credentials(self):
        with patch.dict(os.environ,{'PUBLIC_BASE_URL':'','RENDER_EXTERNAL_URL':'','BAZAR_PUBLISHER_EMAIL':'','BAZAR_PUBLISHER_PASSWORD':''}):
            with self.assertRaisesRegex(ValueError,'BAZAR_PUBLISHER_EMAIL'):hosted.prepare_web()
        with server.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM users').fetchone()[0],0)
    def test_insecure_or_path_origins_rejected(self):
        for origin in ['http://preview.example.test','https://example.test/path','https://user:password@example.test','https://example.test?x=1']:
            with patch.dict(os.environ,{'PUBLIC_BASE_URL':origin}):
                with self.assertRaises(ValueError):hosted.prepare_web()
