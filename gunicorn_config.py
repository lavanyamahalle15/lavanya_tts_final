import os

# Get port from environment variable with fallback to 4005
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = int(os.environ.get('WEB_CONCURRENCY', 4))
threads = int(os.environ.get('PYTHON_MAX_THREADS', 2))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 300))

# Server configuration
worker_class = 'sync'
preload_app = True
forwarded_allow_ips = '*'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'