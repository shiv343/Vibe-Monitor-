New Features:

Multiple test endpoints (/hello, /slow, /error, /health)
Structured logging with JSON format
Enhanced tracing with better span attributes
Cross-service correlation in Grafana
Production-ready configuration with retries, timeouts, and volumes
Improved traffic generator with threading and realistic patterns
Quick setup -
Run docker-compose up --build -d
Wait for services to start (check with docker-compose logs -f)
Run python traffic.py to generate test traffic
Open Grafana at http://localhost:3000 (admin/admin123)
