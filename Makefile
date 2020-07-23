.PHONY: test

install:
	@ echo "Installing the requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt

test:
	@ echo "Running the tests"
	@ pytest || true

lint:
	@ echo "Linting the code"
	@ flake8 || true

start-services:
	@ echo "Starting Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev up -d

stop-services:
	@ echo "Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev down

generate-api:
	@echo "Generating API from OpenAPI 3.0 description using the standard openapitools/openapi-generator-cli"


all:
	install test


