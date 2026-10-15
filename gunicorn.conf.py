import os
bind='0.0.0.0:'+os.environ.get('PORT','3000')
workers=int(os.environ.get('WEB_WORKERS','2'))
threads=int(os.environ.get('WEB_THREADS','4'))
umask=0o077
timeout=60
graceful_timeout=30
max_requests=2000
max_requests_jitter=200
accesslog='-'
errorlog='-'
# Session state, subscriptions and quotas are persisted in the database.
# Initialise once in the master before workers fork to avoid migration races.
def on_starting(server):
    import server as application_server
    application_server.init()
