workers = 3  # Adjust based on your CPU cores
bind = "0.0.0.0:8002"
worker_class = 'gevent'  # Consider using 'gevent' for I/O-bound applications
worker_connections = 1000  # Maximum number of simultaneous clients
timeout = 60

reload = True
accesslog = "/app/access.log"
errorlog = "/app/error.log"

max_requests = 100  # Force workers to restart after handling 1000 requests
max_requests_jitter = 50  # Add randomness to max_requests to avoid simultaneous restarts
