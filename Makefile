#!make
include ./docker/.env-dev

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

start-fuseki:
	@ echo 'Starting Fuseki on port $(if $(FUSEKI_PORT),$(FUSEKI_PORT),'3030')'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev up -d

stop-fuseki:
	@ echo "Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev down

build-test-dbs:
	@ echo  'Building dummy "subdiv" and "abc" datasets at http://localhost:$(FUSEKI_PORT)/$$/datasets'
	@ sleep 2
	@ curl --anyauth --user 'admin:admin' -i -d 'dbType=mem&dbName=subdiv'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -i -d 'dbType=mem&dbName=abc'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'

clean-data:
	@ echo 'Deleting the $(DATA_FOLDER)'
	@ sudo rm -rf $(DATA_FOLDER)

start-service: start-fuseki build-test-dbs

stop-service: stop-fuseki clean-data

generate-api:
	@echo "Generating API from OpenAPI 3.0 description using the standard openapitools/openapi-generator-cli"

all:
	install test
