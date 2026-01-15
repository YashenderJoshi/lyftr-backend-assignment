import json
import logging
from datetime import datetime

logger = logging.getLogger("lyftr")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


def log_event(**kwargs):
    log = {
        "ts": datetime.utcnow().isoformat() + "Z",
        **kwargs,
    }
    logger.info(json.dumps(log))

