# RDF Differ UI — Python 3.12, Poetry, non-root.
# The UI is a plain Flask (WSGI) app → served by gunicorn directly.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/src/app \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /usr/src/app

RUN pip install "poetry==${POETRY_VERSION}"

# Install runtime deps first so this layer caches until the lockfile changes.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

# Application code (overridden by a bind-mount in the dev compose for --reload).
COPY . .

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /usr/src/app
USER appuser

EXPOSE ${RDF_DIFFER_UI_PORT}

CMD gunicorn \
    --timeout ${RDF_DIFFER_GUNICORN_TIMEOUT} \
    --workers ${RDF_DIFFER_GUNICORN_UI_WORKERS} \
    --bind 0.0.0.0:${RDF_DIFFER_UI_PORT} \
    --reload \
    --log-level ${RDF_DIFFER_LOG_LEVEL} \
    rdf_differ.entrypoints.ui.run:app
