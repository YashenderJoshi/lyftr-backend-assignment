# Lyftr AI — Backend Assignment  
Containerized Webhook API (FastAPI)

## Overview
This project implements a production-style backend service using **FastAPI** that ingests inbound WhatsApp-like webhook messages **exactly once**, validates **HMAC-SHA256 signatures**, exposes health probes, analytics, metrics, and structured logs, and runs fully containerized using **Docker Compose** with **SQLite** for storage.

The service follows **12-factor app principles** and is designed for correctness, idempotency, and observability.

---

## Tech Stack
- Python 3.11
- FastAPI
- SQLite
- Docker & Docker Compose
- Prometheus Client (metrics)

---

## Project Structure
app/
main.py # FastAPI app, routes, middleware
config.py # Environment configuration
models.py # DB initialization
storage.py # DB operations
logging_utils.py # Structured JSON logging
metrics.py # Prometheus metrics
tests/
Dockerfile
docker-compose.yml
Makefile
requirements.txt
README.md

yaml
Copy code

---

## How to Run

### Prerequisites
- Docker Desktop
- Docker Compose v2

### Environment Variables
```bash
export WEBHOOK_SECRET="testsecret"
export DATABASE_URL="sqlite:////data/app.db"
Start the Service
bash
Copy code
make up
# or
docker compose up -d --build
The API will be available at:

arduino
Copy code
http://localhost:8000
Health Checks
Liveness Probe
http
Copy code
GET /health/live
Always returns 200 if the application is running.

Readiness Probe
http
Copy code
GET /health/ready
Returns 200 only if:

Database is reachable

WEBHOOK_SECRET is set

Otherwise returns 503.

Webhook Ingestion
Endpoint
http
Copy code
POST /webhook
Headers
makefile
Copy code
Content-Type: application/json
X-Signature: <hex HMAC-SHA256>
Signature Verification
The signature is computed as:

python
Copy code
hex(HMAC_SHA256(
  secret=WEBHOOK_SECRET,
  message=<raw request body bytes>
))
Missing or invalid signature → 401 {"detail":"invalid signature"}

Valid signature → payload is processed

Idempotency
Messages are stored with message_id as the primary key.

Duplicate message_id requests:

Are not inserted again

Still return 200 {"status":"ok"}

Message Listing
Endpoint
http
Copy code
GET /messages
Query Parameters
limit (default: 50, max: 100)

offset (default: 0)

from (filter by sender)

since (ISO-8601 UTC timestamp)

q (case-insensitive substring search on text)

Ordering
pgsql
Copy code
ORDER BY ts ASC, message_id ASC
Response
Includes:

data

total (ignores limit/offset)

limit

offset

Analytics
Endpoint
http
Copy code
GET /stats
Returns
total_messages

senders_count

messages_per_sender (top 10 senders)

first_message_ts

last_message_ts

Metrics
Endpoint
http
Copy code
GET /metrics
Prometheus-compatible text format

Includes:

http_requests_total{path,status}

webhook_requests_total{result}

Request latency histogram

Logging
Structured JSON logs

One log line per request

Fields include:

ts

level

request_id

method

path

status

latency_ms

Webhook logs additionally include:
message_id

dup

result

Logs are suitable for inspection using tools like jq.

Design Decisions
HMAC verification uses raw request body bytes to avoid JSON re-serialization issues.

Idempotency is enforced using a database-level primary key constraint.

SQLite is used with a Docker volume for persistence and simplicity.

Observability is implemented via structured logs and Prometheus metrics.

The application fails fast if required configuration is missing.

Constraints & Use of AI
No external services were used beyond Docker and Python.

SQLite is the only database used.

All configuration is provided via environment variables.

The system runs fully locally using Docker Compose.

Setup Used
VS Code

Docker Desktop

Occasional ChatGPT assistance for guidance, debugging, and validation