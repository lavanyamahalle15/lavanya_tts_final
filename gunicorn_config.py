import os
import multiprocessing

# Worker configuration
workers = 2  # Increased for Standard plan's 2GB RAM
threads = 4  # Optimal thread count for TTS processing
timeout = 180  # Increased timeout for longer processing time
worker_class = 'gthread'  # Use threads for better I/O handling
max_requests = 10  # Increased for better throughput
max_requests_jitter = 3

# Connection configuration
keepalive = 65
worker_connections = 100  # Increased for more concurrent connections

# Port configuration
port = int(os.environ.get('PORT', 4005))
bind = f"0.0.0.0:{port}"

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process Management
preload_app = True  # Preload app to share memory
graceful_timeout = 60  # Match with worker timeout
worker_tmp_dir = '/dev/shm'  # Use RAM for temp files

# Performance tuning
forwarded_allow_ips = '*'
proxy_protocol = True
proxy_allow_ips = '*'