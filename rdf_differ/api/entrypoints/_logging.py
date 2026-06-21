"""Status-class request logging shared by the API and UI entrypoints.

Every handled request is logged at a level chosen by its response status class —
2xx/3xx at INFO, 4xx at WARNING, 5xx at ERROR — with method, path, status and
latency, plus the dataset/task id when present in the path. Lives in the
entrypoint layer only; never imported by ``domain`` or ``adapters``.
"""

import logging
import time

from fastapi import FastAPI, Request

_CONTEXT_KEYS = ("dataset_id", "task_id")


def level_for_status(status_code: int) -> int:
    """Map an HTTP status code to a logging level by its class."""
    if status_code >= 500:
        return logging.ERROR
    if status_code >= 400:
        return logging.WARNING
    return logging.INFO


def _context(request: Request) -> str:
    params = request.path_params or {}
    bits = [f"{key}={params[key]}" for key in _CONTEXT_KEYS if key in params]
    return (" " + " ".join(bits)) if bits else ""


def add_request_logging(app: FastAPI, logger: logging.Logger) -> None:
    """Register the status-class request-logging middleware on ``app``."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "%s %s -> 500 (%.1f ms)%s",
                request.method,
                request.url.path,
                elapsed_ms,
                _context(request),
                exc_info=True,
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.log(
            level_for_status(response.status_code),
            "%s %s -> %s (%.1f ms)%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            _context(request),
        )
        return response
