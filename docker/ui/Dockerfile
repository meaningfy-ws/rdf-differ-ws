FROM python:3.8.18-bullseye
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
EXPOSE $RDF_DIFFER_UI_PORT

WORKDIR /usr/src/app

COPY requirements requirements/
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

CMD gunicorn --timeout ${RDF_DIFFER_GUNICORN_TIMEOUT} --workers ${RDF_DIFFER_GUNICORN_UI_WORKERS} --bind 0.0.0.0:${RDF_DIFFER_UI_PORT} --reload rdf_differ.entrypoints.ui.run:app --log-file ${RDF_DIFFER_UI_LOGS} --log-level ${RDF_DIFFER_LOG_LEVEL}