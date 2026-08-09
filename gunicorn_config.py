import os
from dotenv import load_dotenv
from uvicorn_worker import UvicornWorker
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

chdir = str(PROJECT_ROOT)

load_dotenv()

bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")

workers = 2
worker_class = UvicornWorker

keepalive = 5

max_requests = 2000
max_requests_jitter = 200

timeout = 30
graceful_timeout = 30

accesslog = "-"
errorlog = "-"
loglevel = "info"

access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" '
    '%(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)

wsgi_app = "app.main:app"
