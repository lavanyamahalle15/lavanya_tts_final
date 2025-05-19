import os
import multiprocessing

# Minimal configuration for Render free tier
workers = 1  # Single worker to minimize memory usage
threads = 2
timeout = 120  # Reduced timeout to avoid Render's 30s limit killing the process
worker_class = 'sync'
max_requests = 1  # Restart worker after each request to free memory
max_requests_jitter = 0

# Port configuration
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process Management
preload_app = True
graceful_timeout = 120
keepalive = 5