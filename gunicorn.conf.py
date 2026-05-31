# Gunicorn configuration for Render deployment
workers = 1
worker_class = "sync"
timeout = 120          # 2 minutes — prevents WORKER TIMEOUT on slow DB/SMTP ops
keepalive = 5
bind = "0.0.0.0:10000"
