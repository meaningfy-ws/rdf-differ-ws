"""API response models (DTOs) — endpoints return these, never ad-hoc dicts.

Connexion serialises JSON at the boundary, so handlers return ``Model(...).model_dump()``:
the model is the single, typed source of each response shape.
"""

from pydantic import BaseModel


class CreateDiffResponse(BaseModel):
    uid: str
    dataset_name: str


class ReportTaskResponse(BaseModel):
    task_id: str
    application_profile: str


class MessageResponse(BaseModel):
    message: str
