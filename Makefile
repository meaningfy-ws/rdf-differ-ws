include docker/.env

BUILD_PRINT = \e[1;34mSTEP: \e[0m
MSG_PRINT = \e[1;34mINFO: \e[0m
WARN_PRINT = \e[1;34mWARNING: \e[0m

DEB_OS=$(shell command -v apt > /dev/null && echo 1)
RPM_OS=$(shell command -v yum > /dev/null && echo 1)
OS_DOCKER=$(shell command -v docker > /dev/null && echo 1)
OS_DOCKERC=$(shell command -v docker compose > /dev/null && echo 1)

#-----------------------------------------------------------------------------
# Install dev environment
#-----------------------------------------------------------------------------

# how to set envs to local
# set -o allexport; source docker/.env; set +o allexport

start: | start-traefik start-services
	@ echo "$(MSG_PRINT)Docker-based services started; make stop to stop"

stop: | stop-traefik stop-services
	@ echo "$(MSG_PRINT)Docker-based services stopped; make start to restart"

install: | install-os-dependencies install-python-dependencies
	@ echo "$(MSG_PRINT)To get started quickly with docker, make start"
	@ echo "$(MSG_PRINT)To run tests, make install-python-dependencies-dev"

install-dev: | install-os-dependencies install-python-dependencies-dev
	@ echo "$(MSG_PRINT)To get started quickly with docker, make start"

install-os-dependencies:
ifeq ($(DEB_OS), 1)
	@ sudo apt install redis-server default-jre
else ifeq ($(RPM_OS), 1)
	@ sudo yum install redis java-11-openjdk
else
	@ echo "$(MSG_PRINT)Operating system not supported"
	@ echo "$(MSG_PRINT)Install Java 11+ and Redis 6+"
	@ echo "$(MSG_PRINT)Then make install-python-dependencies"
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

run-system-redis:
ifeq ($(DEB_OS), 1)
# running as root, and replacing a system config, are both bad practices!
	@ echo "$(WARN_PRINT)Backing up and replacing a system config as root!"
	@ sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.rdf_differ.bak -v
	@ sudo cp docker/redis.conf /etc/redis/redis.conf -v
	@ sudo systemctl restart redis.service
else ifeq ($(RPM_OS), 1)
	@ sudo systemctl enable redis --now
else
	@ echo "$(MSG_PRINT)Operating system not supported"
	@ echo "$(MSG_PRINT)Please start the Redis server yourself"
	@ echo "$(MSG_PRINT)Refer also to docker/redis.conf"
	false
endif

stop-local-applications:
	@ ./bash/stop_gunicorn.sh

#-----------------------------------------------------------------------------
# Service commands
#-----------------------------------------------------------------------------
build-volumes:
ifeq ($(OS_DOCKER), 1)
	@ echo -e '$(BUILD_PRINT)Creating a shared volume for micro-services'
	@ docker volume create rdf-differ-template-${ENVIRONMENT}
	@ docker volume create rdf-differ-template
else
	@ echo "$(MSG_PRINT)Docker not found"
	@ echo "$(MSG_PRINT)Please see README for other ways of starting up"
	false
endif

build-services:
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Building the RDF Differ micro-services'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose.yml --env-file docker/.env build
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

build-externals:
	@ echo -e "$(BUILD_PRINT)Creating the necessary volumes, networks and folders and setting the special rights"
	@ docker network create proxy-net || true

start-traefik: build-externals
	@ echo -e "$(BUILD_PRINT)Starting the Traefik services $(END_BUILD_PRINT)"
	@ docker compose -p common --file ./docker/traefik/docker-compose.yml --env-file docker/.env up -d

stop-traefik:
	@ echo -e "$(BUILD_PRINT)Stopping the Traefik services $(END_BUILD_PRINT)"
	@ docker compose -p common --file ./docker/traefik/docker-compose.yml --env-file docker/.env down

start-services: build-volumes
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Starting the RDF Differ micro-services'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose.yml --env-file docker/.env up -d
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

stop-services:
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Stopping the RDF Differ micro-services'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose.yml --env-file docker/.env stop
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

teardown-services:
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Tearing down the microservice environment'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose.yml --env-file docker/.env down --volumes --remove-orphans
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

#-----------------------------------------------------------------------------
# Fuseki control for github actions
#-----------------------------------------------------------------------------
setup-docker-fuseki: | build-volumes
	@ echo -e '$(BUILD_PRINT)Building the Fuseki service'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose-tests.yml --env-file docker/.env build rdf-differ-fuseki

run-docker-fuseki:
	@ echo -e '$(BUILD_PRINT)Starting the Fuseki service'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose-tests.yml --env-file docker/.env up -d rdf-differ-fuseki

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
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose-tests.yml --env-file docker/.env up -d rdf-differ-redis

run-docker-api:
	@ echo -e '$(BUILD_PRINT)Starting api'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose-tests.yml --env-file docker/.env up -d rdf-differ-api

run-docker-ui:
	@ echo -e '$(BUILD_PRINT)Starting ui'
	@ docker compose --file docker/docker-compose-tests.yml --env-file docker/.env up -d rdf-differ-ui

run-docker-celery:
	@ echo -e '$(BUILD_PRINT)Starting celery worker'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file docker/docker-compose-tests.yml --env-file docker/.env up -d rdf-differ-celery-worker

test: | install-python-dependencies-dev test-data-fuseki run-docker-redis run-docker-api run-docker-celery
	@ echo "$(BUILD_PRINT)Running tests using Docker services"
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
# Template update commands
#-----------------------------------------------------------------------------

# Default values for environment variables
TEMPLATE_SRC_DIR ?= ../diff-query-generator
TEMPLATE_OUTPUT_DIR ?= $(TEMPLATE_SRC_DIR)/output
TEMPLATE_AP ?= owl-core
TEMPLATE_TYPE ?= html

# Derived paths
TEMPLATE_SRC_BASE = $(TEMPLATE_OUTPUT_DIR)/$(TEMPLATE_AP)
TEMPLATE_QUERIES_SRC = $(TEMPLATE_SRC_BASE)/queries
TEMPLATE_HTML_SRC = $(TEMPLATE_SRC_BASE)/$(TEMPLATE_TYPE)

TEMPLATE_DEST_BASE = resources/templates/$(TEMPLATE_AP)-en-only
TEMPLATE_QUERIES_DEST = $(TEMPLATE_DEST_BASE)/queries
TEMPLATE_HTML_DEST = $(TEMPLATE_DEST_BASE)/template_variants/$(TEMPLATE_TYPE)/templates

update_template:
	@ echo "$(BUILD_PRINT)Updating templates from $(TEMPLATE_SRC_BASE)"
	@ mkdir -p $(TEMPLATE_QUERIES_DEST)
	@ mkdir -p $(TEMPLATE_HTML_DEST)
	@ echo "$(MSG_PRINT)Copying queries from $(TEMPLATE_QUERIES_SRC) to $(TEMPLATE_QUERIES_DEST)"
	@ cp -r $(TEMPLATE_QUERIES_SRC)/* $(TEMPLATE_QUERIES_DEST)/
	@ echo "$(MSG_PRINT)Copying $(TEMPLATE_TYPE) templates from $(TEMPLATE_HTML_SRC) to $(TEMPLATE_HTML_DEST)"
	@ cp -r $(TEMPLATE_HTML_SRC)/* $(TEMPLATE_HTML_DEST)/
	@ echo "$(MSG_PRINT)Template update completed"

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
