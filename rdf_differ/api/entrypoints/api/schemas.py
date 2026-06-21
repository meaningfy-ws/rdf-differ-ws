"""Request models for the REST API entrypoint.

Response models live in ``rdf_differ.api.domain.model``; these cover request bodies
that arrive as JSON. Multipart form fields are declared inline on the route.
"""

from pydantic import BaseModel


class ReportRequest(BaseModel):
    """Body of ``POST /diffs/report``."""

    dataset_id: str
    application_profile: str
    template_type: str
    rebuild: str = "false"
