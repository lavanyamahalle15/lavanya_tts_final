import os

workers = int(os.environ.get('MAX_WORKERS', 4))
threads = 2
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 300))
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"
worker_class = "sync"
accesslog = "-"
errorlog = "-"
preload_app = True