import os
import time
import uuid
import tempfile
import torchaudio
from fastapi import FastAPI, UploadFile, File, Form, Request, Depends
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from logger import init_logger, init_audit_logger
from auth import create_token, verify_token
from asr_service import WhisperASR
from metrics import *

logger = init_logger("whisper_asr_service", os.getenv("LOG_LEVEL", "INFO"))
audit_logger = init_audit_logger(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="Whisper ASR Service")
app.state.logger = logger
app.state.audit_logger = audit_logger

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

asr = WhisperASR(os.getenv("WHISPER_MODEL_PATH"), logger)


def get_trace_id(request: Request):
    return request.headers.get("X-Trace-Id") or uuid.uuid4().hex


@app.middleware("http")
async def access_middleware(request: Request, call_next):
    trace_id = get_trace_id(request)
    request.state.trace_id = trace_id

    start = time.time()
    status = "success"

    try:
        response = await call_next(request)
        return response
    except Exception:
        status = "error"
        logger.exception(
            "request_failed",
            extra={
                "trace_id": trace_id,
                "path": request.url.path
            }
        )
        raise
    finally:
        latency = round(time.time() - start, 3)

        REQUEST_TOTAL.labels(status=status).inc()
        REQUEST_LATENCY.observe(latency)

        logger.info(
            "access",
            extra={
                "trace_id": trace_id,
                "ip": request.client.host,
                "path": request.url.path,
                "status": status,
                "latency": latency
            }
        )

        audit_logger.info(
            "access",
            extra={
                "trace_id": trace_id,
                "ip": request.client.host,
                "path": request.url.path,
                "status": status,
                "latency": latency
            }
        )


@app.post("/auth/token")
def auth_token(request: Request):
    return create_token(request)


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


@app.post("/transcribe")
async def transcribe(
    request: Request,
    file: UploadFile = File(None),
    audio_url: str = Form(None),
    language: str = Form("fr"),
    chunk_length: int = Form(30),
    _: str = Depends(verify_token)
):
    trace_id = request.state.trace_id

    logger.info(
        "request_start",
        extra={
            "trace_id": trace_id,
            "ip": request.client.host,
            "language": language
        }
    )

    audit_logger.info(
        "asr_request",
        extra={
            "trace_id": trace_id,
            "ip": request.client.host,
            "upload_name": file.filename if file else None,
            "audio_url": audio_url
        }
    )

    audio_path = None

    try:
        if audio_url:
            audio_path = asr.download_audio(audio_url, trace_id)
        else:
            data = await file.read()
            size_mb = len(data) / (1024 * 1024)
            AUDIO_SIZE.observe(size_mb)

            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
                tmp.write(data)
                audio_path = tmp.name

            logger.info(
                "audio_uploaded",
                extra={
                    "trace_id": trace_id,
                    "upload_name": file.filename,
                    "size_mb": round(size_mb, 3)
                }
            )

        audio, sr = torchaudio.load(audio_path)
        segments = asr.transcribe(audio, sr, language, chunk_length, trace_id, audio_path)
        SEGMENTS.observe(len(segments))

        audit_logger.info(
            "asr_completed",
            extra={
                "trace_id": trace_id,
                "segments": len(segments)
            }
        )

        return {"language": language, "segments": segments}

    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
