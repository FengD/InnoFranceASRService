import logging
from logging.handlers import RotatingFileHandler


class ContextFormatter(logging.Formatter):
    def format(self, record):
        base = super().format(record)
        extras = []

        for k, v in record.__dict__.items():
            if k.startswith("_"):
                continue
            if k in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName",
                "processName", "process", "message"
            ):
                continue
            extras.append(f"{k}={v}")

        if extras:
            return base + " | " + " ".join(extras)
        return base


def _create_logger(name: str, file: str, level: str, console: bool):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = ContextFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    fh = RotatingFileHandler(
        file,
        maxBytes=50 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    logger.propagate = False
    return logger


def init_logger(name: str, level: str):
    logger = _create_logger(name, f"{name}.log", level, True)
    logger.info("logger initialized")
    logger.info(f"log_file=./{name}.log")
    return logger


def init_audit_logger(level: str):
    logger = _create_logger("audit", "audit.log", level, False)
    logger.info("audit logger initialized")
    logger.info("audit_file=./audit.log")
    return logger
