from prometheus_client import Counter, Histogram

REQUEST_TOTAL = Counter(
    "asr_request_total",
    "Total ASR requests",
    ["status"]
)

REQUEST_LATENCY = Histogram(
    "asr_request_latency_seconds",
    "ASR request latency"
)

AUDIO_SIZE = Histogram(
    "asr_audio_size_mb",
    "Audio size MB"
)

SEGMENTS = Histogram(
    "asr_segments_count",
    "Segments count"
)
