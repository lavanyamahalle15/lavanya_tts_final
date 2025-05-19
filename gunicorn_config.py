import os
import multiprocessing

# Gunicorn configuration for production
workers = multiprocessing.cpu_count() * 2 + 1
threads = 4
timeout = 600  # Increased timeout to 10 minutes
worker_class = 'sync'
keepalive = 65
worker_connections = 1000
max_requests = 100
max_requests_jitter = 50

# Port configuration
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# SSL Configuration for production
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Add startup notification
def on_starting(server):
    print("Starting up Gunicorn server...")