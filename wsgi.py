"""Gunicorn-compatible transport for the shared, tested ERP request handler."""
import io
import os
from email.message import Message
from http import HTTPStatus
import server

class WSGIHandler(server.Handler):
    def __init__(self,environ):
        self.path=environ.get('PATH_INFO','/')
        self.headers=Message()
        for key,value in environ.items():
            if key.startswith('HTTP_'):self.headers[key[5:].replace('_','-')]=value
        self.headers['Content-Length']=environ.get('CONTENT_LENGTH') or '0'
        self.headers['Content-Type']=environ.get('CONTENT_TYPE','')
        self.client_address=(environ.get('REMOTE_ADDR',''),0)
        self.rfile=environ['wsgi.input'];self.wfile=io.BytesIO()
        self.response_headers=[];self.status=500
    def send_response(self,code,message=None):self.status=code
    def send_header(self,key,value):self.response_headers.append((key,str(value)))
    def end_headers(self):pass

def application(environ,start_response):
    handler=WSGIHandler(environ)
    method=environ.get('REQUEST_METHOD','GET')
    origin=environ.get('HTTP_ORIGIN')
    public=os.environ.get('PUBLIC_BASE_URL','').rstrip('/')
    if method not in ['GET','HEAD','POST']:
        handler.reply({'error':'Méthode non autorisée'},405)
    elif public and handler.path!='/healthz' and environ.get('HTTP_HOST')!=public.split('://',1)[-1]:
        handler.reply({'error':'Hôte non autorisé'},400)
    elif public and method=='POST' and origin and origin!=public:
        handler.reply({'error':'Origine non autorisée'},403)
    elif method=='POST' and not environ.get('CONTENT_LENGTH'):
        handler.reply({'error':'Taille de requête requise'},411)
    else:
        handler.handle_request('GET' if method=='HEAD' else method)
    body=handler.wfile.getvalue()
    headers=handler.response_headers+[
        ('Content-Length',str(len(body))),('X-Frame-Options','DENY'),
        ('Referrer-Policy','same-origin'),('X-Content-Type-Options','nosniff'),
    ]
    if os.environ.get('COOKIE_SECURE')=='1':headers.append(('Strict-Transport-Security','max-age=31536000'))
    start_response(f'{handler.status} {HTTPStatus(handler.status).phrase}',headers)
    return [b'' if method=='HEAD' else body]
