import os
import multiprocessing

# Get port from environment variable with fallback to 4005 (for local development only)
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"

# Worker configuration - minimal for faster startup
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
threads = int(os.environ.get('PYTHON_MAX_THREADS', 1))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 60))

# Server configuration
worker_class = 'sync'
preload_app = False  # Disable preloading to reduce memory usage during startup
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 60
keepalive = 5

# Startup configuration
timeout = 60  # Reduced timeout since we're not loading models on startup
check_config = False  # Disable config checking to speed up startup

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Add startup notification
def on_starting(server):
    print("Starting up Gunicorn server...")