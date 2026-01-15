from fastapi import FastAPI, status, Request, HTTPException, Query
from fastapi.responses import Response
import hmac
import hashlib
import time
import uuid

from app.config import settings
from app.models import init_db, get_connection
from app.storage import insert_message, list_messages, get_stats
from app.logging_utils import log_event
from app.metrics import (
    http_requests_total,
    webhook_requests_total,
    request_latency_ms,
    metrics_response,
)

app = FastAPI(title="Lyftr Webhook API")


# -------------------------
# MIDDLEWARE (logs + metrics)
# -------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()

    response = await call_next(request)

    latency_ms = int((time.time() - start) * 1000)

    # Metrics
    http_requests_total.labels(
        path=request.url.path,
        status=str(response.status_code)
    ).inc()

    request_latency_ms.observe(latency_ms)

    # Logs
    log_event(
        level="INFO",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency_ms,
    )

    return response


# -------------------------
# STARTUP
# -------------------------
@app.on_event("startup")
def startup():
    init_db()


# -------------------------
# HEALTH
# -------------------------
@app.get("/health/live")
def live():
    return {"status": "alive"}


@app.get("/health/ready")
def ready():
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()

        if not settings.WEBHOOK_SECRET:
            raise RuntimeError("WEBHOOK_SECRET missing")

        return {"status": "ready"}
    except Exception:
        return status.HTTP_503_SERVICE_UNAVAILABLE


# -------------------------
# WEBHOOK (WITH METRICS)
# -------------------------
@app.post("/webhook")
async def webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Signature")

    if not signature:
        webhook_requests_total.labels(result="invalid_signature").inc()
        log_event(
            level="ERROR",
            method="POST",
            path="/webhook",
            status=401,
            result="invalid_signature",
        )
        raise HTTPException(status_code=401, detail="invalid signature")

    expected_signature = hmac.new(
        key=settings.WEBHOOK_SECRET.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        webhook_requests_total.labels(result="invalid_signature").inc()
        log_event(
            level="ERROR",
            method="POST",
            path="/webhook",
            status=401,
            result="invalid_signature",
        )
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()
    message_id = payload.get("message_id")

    result = insert_message(payload)

    # 🔹 STEP 3: webhook outcome metric
    webhook_requests_total.labels(result=result).inc()

    log_event(
        level="INFO",
        method="POST",
        path="/webhook",
        status=200,
        message_id=message_id,
        dup=(result == "duplicate"),
        result=result,
    )

    return {"status": "ok"}


# -------------------------
# MESSAGES
# -------------------------
@app.get("/messages")
def get_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_msisdn: str | None = Query(None, alias="from"),
    since: str | None = None,
    q: str | None = None,
):
    return list_messages(
        limit=limit,
        offset=offset,
        from_msisdn=from_msisdn,
        since=since,
        q=q,
    )


# -------------------------
# STATS
# -------------------------
@app.get("/stats")
def stats():
    return get_stats()


# -------------------------
# METRICS ENDPOINT (STEP 4)
# -------------------------
@app.get("/metrics")
def metrics():
    data, content_type = metrics_response()
    return Response(content=data, media_type=content_type)
