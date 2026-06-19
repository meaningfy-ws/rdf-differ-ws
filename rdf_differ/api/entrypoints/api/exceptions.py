"""HTTP error mapping for the REST API entrypoint (EPIC api-ui-fastapi-modernization,
DEC-1/DEC-8).

Emits a problem-style ``{status, title, detail}`` JSON body (the shape the UI parses)
for every error, and logs unhandled exceptions at ERROR with a traceback.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

INTERNAL_ERROR_DETAIL = (
    "The server encountered an internal error and was unable to complete your request."
)


def problem(status_code: int, detail: str) -> JSONResponse:
    """Build a problem-style JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_code,
            "title": HTTPStatus(status_code).phrase,
            "detail": detail,
        },
    )


def register_exception_handlers(app: FastAPI, logger: logging.Logger) -> None:
    """Register problem-style handlers for HTTP, validation and unhandled errors."""

    @app.exception_handler(HTTPException)
    async def _http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        return problem(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        detail = "; ".join(error["msg"] for error in exc.errors()) or "Validation error"
        return problem(HTTPStatus.UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(Exception)
    async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=True)
        return problem(HTTPStatus.INTERNAL_SERVER_ERROR, INTERNAL_ERROR_DETAIL)
