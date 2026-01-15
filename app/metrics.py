from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# HTTP request counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["path", "status"]
)

# Webhook outcome counter
webhook_requests_total = Counter(
    "webhook_requests_total",
    "Webhook processing results",
    ["result"]
)

# Simple latency histogram (milliseconds)
request_latency_ms = Histogram(
    "request_latency_ms",
    "Request latency in milliseconds",
    buckets=(50, 100, 250, 500, 1000, float("inf"))
)


def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST

