import os
import multiprocessing

# Worker configuration
workers = 1  # Single worker to minimize memory usage
threads = 4  # Increased threads for better concurrent request handling
timeout = 30  # Match with internal app timeout
worker_class = 'gthread'  # Use threads for better I/O handling
max_requests = 2  # Restart worker after handling 2 requests to prevent memory leaks
max_requests_jitter = 1

# Connection configuration
keepalive = 65
worker_connections = 50

# Port configuration
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process Management
preload_app = True  # Preload app to share memory
graceful_timeout = 30  # Match with worker timeout
worker_tmp_dir = '/dev/shm'  # Use RAM for temp files

# Performance tuning
forwarded_allow_ips = '*'
proxy_protocol = True
proxy_allow_ips = '*'