.PHONY: test

install:
	@ echo "Installing the requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt

test:
	@ echo "Running the tests"
	@ pytest || true

#format:
#	black rdf_differ

lint:
	@echo "Installing the requirements"
	#	# stop the build if there are Python syntax errors or undefined names
	#	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	@ flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

start-services:
	@ echo "Starting Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d

stop-services:
	@ echo "Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env down

all:
	install test


