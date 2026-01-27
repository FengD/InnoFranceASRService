import time
import uuid
import hmac
import hashlib
from fastapi import Header, HTTPException, Request

SECRET_KEY = b"whisper-asr-secret"
TOKEN_TTL = 3600

TOKENS = {}


def create_token(request: Request):
    logger = request.app.state.logger
    audit = request.app.state.audit_logger
    trace_id = request.state.trace_id

    raw = f"{uuid.uuid4()}-{time.time()}".encode()
    token = hmac.new(SECRET_KEY, raw, hashlib.sha256).hexdigest()
    expire = time.time() + TOKEN_TTL

    TOKENS[token] = {
        "expire": expire,
        "ip": request.client.host
    }

    logger.info(
        "token_created",
        extra={
            "trace_id": trace_id,
            "ip": request.client.host,
            "token_prefix": token[:8]
        }
    )

    audit.info(
        "token_created",
        extra={
            "trace_id": trace_id,
            "ip": request.client.host,
            "token_prefix": token[:8],
            "expire_at": int(expire)
        }
    )

    return {"token": token, "expire_at": expire}


def verify_token(
    request: Request,
    authorization: str = Header(...)
):
    logger = request.app.state.logger
    audit = request.app.state.audit_logger
    trace_id = request.state.trace_id

    if not authorization.startswith("Bearer "):
        logger.warning(
            "auth_failed",
            extra={"trace_id": trace_id, "reason": "bad_header"}
        )
        audit.warning(
            "auth_failed",
            extra={"trace_id": trace_id, "reason": "bad_header"}
        )
        raise HTTPException(401, "invalid authorization header")

    token = authorization.replace("Bearer ", "")
    data = TOKENS.get(token)

    if not data:
        logger.warning(
            "auth_failed",
            extra={"trace_id": trace_id, "reason": "invalid_token"}
        )
        audit.warning(
            "auth_failed",
            extra={"trace_id": trace_id, "reason": "invalid_token"}
        )
        raise HTTPException(403, "invalid token")

    if time.time() > data["expire"]:
        TOKENS.pop(token, None)
        logger.warning(
            "auth_failed",
            extra={"trace_id": trace_id, "reason": "expired"}
        )
        audit.warning(
            "auth_failed",
            extra={"trace_id": trace_id, "reason": "expired"}
        )
        raise HTTPException(403, "token expired")

    return token
