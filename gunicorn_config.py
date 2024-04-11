workers = 4
bind = "0.0.0.0:8002"
worker_class = 'sync'  # Worker class
worker_connections = 1000  # Maximum number of simultaneous clients
timeout = 240

reload = True
accesslog = "/app/access.log"
errorlog = "/app/error.log"
