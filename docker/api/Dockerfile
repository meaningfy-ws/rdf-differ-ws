FROM python:3.8.5-buster
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
EXPOSE $RDF_DIFFER_API_PORT

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD gunicorn --timeout ${RDF_DIFFER_GUNICORN_TIMEOUT} --workers ${RDF_DIFFER_GUNICORN_API_WORKERS} --bind 0.0.0.0:${RDF_DIFFER_API_PORT} --reload rdf_differ.entrypoints.api.run:app --log-file ${RDF_DIFFER_API_LOGS} --log-level ${RDF_LOG_LEVEL}