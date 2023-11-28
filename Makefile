include docker/.env

BUILD_PRINT = \e[1;34mSTEP: \e[0m

DEB_OS=$(shell command -v apt > /dev/null && echo 1)
RPM_OS=$(shell command -v yum > /dev/null && echo 1)

#-----------------------------------------------------------------------------
# Install dev environment
#-----------------------------------------------------------------------------

# how to set envs to local
# set -o allexport; source docker/.env; set +o allexport

setup: | install build-volumes start-services
	@ echo "$(BUILD_PRINT)Docker-based services started; make stop-services to stop"

setup-dev: | install-dev build-volumes start-services
	@ echo "$(BUILD_PRINT)Docker-based services started; make stop-services to stop"

install: | install-os-dependencies install-python-dependencies
	@ echo "$(BUILD_PRINT)To use docker instead of local system services, run make setup"

install-dev: | install-os-dependencies install-python-dependencies-dev
	@ echo "$(BUILD_PRINT)To use docker instead of local system services, run make setup-dev"

install-os-dependencies:
ifeq ($(DEB_OS), 1)
	@ sudo apt install redis-server default-jre
else ifeq ($(RPM_OS), 1)
	@ sudo yum install redis java-11-openjdk
else
	@ echo "$(BUILD_PRINT)Operating system not supported"
	false
endif

install-python-dependencies:
	@ echo "$(BUILD_PRINT)Installing the production requirements"
	@ python -m pip install --upgrade pip
	@ python -m pip install -r requirements/prod.txt

install-python-dependencies-dev:
	@ echo "$(BUILD_PRINT)Installing the development requirements"
	@ python -m pip install --upgrade pip
	@ python -m pip install -r requirements/dev.txt

setup-local-fuseki:
	@ ./bash/setup_fuseki.sh

run-local-fuseki:
	@ ./fuseki/fuseki-server -q

run-local-api:
	@ ./bash/run_api.sh

run-local-ui:
	@ ./bash/run_ui.sh

run-local-redis:
ifeq ($(DEB_OS), 1)
# running as root, and replacing a system config, are both bad practices!
	@ echo "$(BUILD_PRINT)WARNING: Backing up and replacing a system config as root!"
	@ sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.rdf_differ.bak -v
	@ sudo cp docker/redis.conf /etc/redis/redis.conf -v
	@ sudo systemctl restart redis.service
else ifeq ($(RPM_OS), 1)
	@ sudo systemctl enable redis --now
else
	@ echo "$(BUILD_PRINT)Operating system not supported"
	false
endif

stop-local-gunicorn:
	@ ./bash/stop_gunicorn.sh

#-----------------------------------------------------------------------------
# Service commands
#-----------------------------------------------------------------------------
build-volumes:
	@ docker volume create rdf-differ-template

build-services:
	@ echo -e '$(BUILD_PRINT)Building the RDF Differ micro-services'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env build

start-services:
	@ echo -e '$(BUILD_PRINT)Starting the RDF Differ micro-services'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d

stop-services:
	@ echo -e '$(BUILD_PRINT)Stopping the dev services'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env stop


#-----------------------------------------------------------------------------
# Fuseki control for github actions
#-----------------------------------------------------------------------------
setup-docker-fuseki: | build-volumes
	@ echo -e '$(BUILD_PRINT)Building the Fuseki service'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env build fuseki

run-docker-fuseki:
	@ echo -e '$(BUILD_PRINT)Starting the Fuseki service'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d fuseki

#-----------------------------------------------------------------------------
# Test commands
#-----------------------------------------------------------------------------

test-data-fuseki: | setup-docker-fuseki run-docker-fuseki
	@ echo "$(BUILD_PRINT)Building dummy "subdiv" and "abc" test datasets at http://localhost:$(if $(RDF_DIFFER_FUSEKI_PORT),$(RDF_DIFFER_FUSEKI_PORT),unknown port)/$$/datasets"
	@ sleep 5
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=subdiv'  'http://localhost:$(RDF_DIFFER_FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=abc'  'http://localhost:$(RDF_DIFFER_FUSEKI_PORT)/$$/datasets'

run-docker-redis:
	@ echo -e '$(BUILD_PRINT)Starting redis'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d redis

run-docker-api:
	@ echo -e '$(BUILD_PRINT)Starting api'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d rdf-differ-api

run-docker-ui:
	@ echo -e '$(BUILD_PRINT)Starting ui'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d rdf-differ-ui

test: | install-python-dependencies-dev test-data-fuseki run-docker-redis run-docker-api
	@ echo "$(BUILD_PRINT)Running the tests using docker services"
	@ pytest

lint:
	@ echo "$(BUILD_PRINT)Linting the code"
	@ flake8 || true

#-----------------------------------------------------------------------------
# Template commands
#-----------------------------------------------------------------------------

set-report-template:
	@ echo "$(BUILD_PRINT)Copying custom template"
	@ docker rm temp | true
	@ docker volume rm rdf-differ-template | true
	@ docker volume create rdf-differ-template
	@ docker container create --name temp -v rdf-differ-template:/data busybox
	@ docker cp $(location). temp:/data
	@ docker rm temp

#-----------------------------------------------------------------------------
# Run UI dev environment
#-----------------------------------------------------------------------------

run-dev-ui:
	@ export FLASK_APP=rdf_differ.entrypoints.ui.run
	@ export FLASK_ENV=development
	@ flask run

#-----------------------------------------------------------------------------
# Gherkin feature and acceptance test generation commands
#-----------------------------------------------------------------------------

FEATURES_FOLDER = tests/features
STEPS_FOLDER = tests/steps
FEATURE_FILES := $(wildcard $(FEATURES_FOLDER)/*.feature)
EXISTENT_TEST_FILES = $(wildcard $(STEPS_FOLDER)/*.py)
HYPOTHETICAL_TEST_FILES :=  $(addprefix $(STEPS_FOLDER)/test_, $(notdir $(FEATURE_FILES:.feature=.py)))
TEST_FILES := $(filter-out $(EXISTENT_TEST_FILES),$(HYPOTHETICAL_TEST_FILES))

generate-tests-from-features: $(TEST_FILES)
	@ echo "$(BUILD_PRINT)The following test files should be generated: $(TEST_FILES)"
	@ echo "$(BUILD_PRINT)Done generating missing feature files"
	@ echo "$(BUILD_PRINT)Verifying if there are any missing step implementations"
	@ py.test --generate-missing --feature $(FEATURES_FOLDER)

$(addprefix $(STEPS_FOLDER)/test_, $(notdir $(STEPS_FOLDER)/%.py)): $(FEATURES_FOLDER)/%.feature
	@ echo "$(BUILD_PRINT)Generating the testfile "$@"  from "$<" feature file"
	@ pytest-bdd generate $< > $@
	@ sed -i  's|features|../features|' $@
