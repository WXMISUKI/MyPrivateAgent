"""Structured JSON logging with request ID correlation."""

from __future__ import annotations

import logging
import os

from pythonjsonlogger import jsonlogger


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from agent_server.middleware import get_request_id
        except ModuleNotFoundError:
            from backend.agent_server.middleware import get_request_id
        record.request_id = get_request_id() or "-"
        return True


def setup_logging() -> logging.Logger:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json")

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s")

    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    root_logger.addHandler(handler)

    return root_logger
