"""Unit tests for the status-class request-logging middleware."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from rdf_differ.api.entrypoints._logging import add_request_logging, level_for_status


def test_level_for_status_classes():
    assert level_for_status(200) == logging.INFO
    assert level_for_status(302) == logging.INFO
    assert level_for_status(404) == logging.WARNING
    assert level_for_status(422) == logging.WARNING
    assert level_for_status(500) == logging.ERROR


def _app() -> FastAPI:
    app = FastAPI()
    add_request_logging(app, logging.getLogger("test.requests"))

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/missing")
    def missing():
        raise HTTPException(404, "nope")

    return app


def test_2xx_logs_at_info(caplog):
    client = TestClient(_app())
    with caplog.at_level(logging.INFO, logger="test.requests"):
        client.get("/ok")
    record = next(r for r in caplog.records if "/ok" in r.getMessage())
    assert record.levelno == logging.INFO
    assert "200" in record.getMessage()


def test_4xx_logs_at_warning(caplog):
    client = TestClient(_app())
    with caplog.at_level(logging.INFO, logger="test.requests"):
        client.get("/missing")
    record = next(r for r in caplog.records if "/missing" in r.getMessage())
    assert record.levelno == logging.WARNING
    assert "404" in record.getMessage()
