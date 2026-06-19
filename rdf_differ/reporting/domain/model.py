"""Reporting domain models."""

from pydantic import BaseModel


class ReportMeta(BaseModel):
    """The diff report meta record persisted as ``meta.json``.

    ``uid`` is the Celery task id; it is ``None`` when a diff is produced outside a
    task context (the historical dict allowed this), so it stays optional.
    """

    uid: str | None = None
    dataset_name: str
    created_at: str
