FROM python:3.8.5-buster
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
EXPOSE $RDF_DIFFER_UI_PORT

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#CMD flask run --host=0.0.0.0 --port=${UI_PORT}
CMD gunicorn -w 2 --bind 0.0.0.0:${RDF_DIFFER_UI_PORT} --reload rdf_differ.entrypoints.ui.run:app