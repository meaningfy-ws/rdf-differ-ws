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
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d

stop-services:
	@ echo "Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env down

all:
	install test


