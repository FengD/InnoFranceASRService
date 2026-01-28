import os

class Settings:
    APP_NAME = "Whisper ASR Service"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    MODEL_PATH = os.getenv("WHISPER_MODEL_PATH", "openai/whisper-large-v3")
    DEVICE = "cuda"
    DEFAULT_LANGUAGE = "fr"
    MAX_AUDIO_MB = int(os.getenv("MAX_AUDIO_MB", "200"))

    API_TOKENS = {
        token.strip(): True
        for token in os.getenv("API_TOKENS", "").split(",")
        if token.strip()
    }

    RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute")

    S3_ENDPOINT = os.getenv("S3_ENDPOINT")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
    S3_PREFIX = os.getenv("S3_PREFIX", "asr-audio")

settings = Settings()

if not settings.MODEL_PATH:
    raise RuntimeError("WHISPER_MODEL_PATH must be set")
