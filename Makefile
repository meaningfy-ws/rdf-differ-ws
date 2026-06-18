# Optional: a fresh clone has no infra/.env yet — copy infra/.env.example first.
-include infra/.env

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
# set -o allexport; source infra/.env; set +o allexport

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
	@ echo "$(BUILD_PRINT)Installing the runtime dependencies (Poetry)"
	@ poetry install --only main

install-python-dependencies-dev:
	@ echo "$(BUILD_PRINT)Installing all dependency groups (Poetry)"
	@ poetry install --with dev,test,lint,docs

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
	@ sudo cp infra/redis.conf /etc/redis/redis.conf -v
	@ sudo systemctl restart redis.service
else ifeq ($(RPM_OS), 1)
	@ sudo systemctl enable redis --now
else
	@ echo "$(MSG_PRINT)Operating system not supported"
	@ echo "$(MSG_PRINT)Please start the Redis server yourself"
	@ echo "$(MSG_PRINT)Refer also to infra/redis.conf"
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
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose.yml --env-file infra/.env build
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

build-externals:
	@ echo -e "$(BUILD_PRINT)Creating the necessary volumes, networks and folders and setting the special rights"
	@ docker network create proxy-net || true

start-traefik: build-externals
	@ echo -e "$(BUILD_PRINT)Starting the Traefik services $(END_BUILD_PRINT)"
	@ docker compose -p common --file ./infra/traefik/docker-compose.yml --env-file infra/.env up -d

stop-traefik:
	@ echo -e "$(BUILD_PRINT)Stopping the Traefik services $(END_BUILD_PRINT)"
	@ docker compose -p common --file ./infra/traefik/docker-compose.yml --env-file infra/.env down

start-services: build-volumes
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Starting the RDF Differ micro-services'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose.yml --env-file infra/.env up -d
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

stop-services:
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Stopping the RDF Differ micro-services'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose.yml --env-file infra/.env stop
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

teardown-services:
ifeq ($(OS_DOCKERC), 1)
	@ echo -e '$(BUILD_PRINT)Tearing down the microservice environment'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose.yml --env-file infra/.env down --volumes --remove-orphans
else
	@ echo "$(MSG_PRINT)Docker not found, please see README"
	false
endif

#-----------------------------------------------------------------------------
# Fuseki control for github actions
#-----------------------------------------------------------------------------
build-docker-fuseki-test: | build-volumes
	@ echo -e '$(BUILD_PRINT)Building the Fuseki service'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose-tests.yml --env-file infra/.env build rdf-differ-fuseki

run-docker-fuseki-test: | build-docker-fuseki-test
	@ echo -e '$(BUILD_PRINT)Starting the Fuseki service'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose-tests.yml --env-file infra/.env up -d rdf-differ-fuseki

#-----------------------------------------------------------------------------
# Test commands
#-----------------------------------------------------------------------------

test-data-fuseki:
	@ echo "$(BUILD_PRINT)Building dummy "subdiv" and "abc" test datasets at http://localhost:$(if $(RDF_DIFFER_FUSEKI_PORT),$(RDF_DIFFER_FUSEKI_PORT),unknown port)/$$/datasets"
	@ sleep 5
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=subdiv'  'http://localhost:$(RDF_DIFFER_FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=abc'  'http://localhost:$(RDF_DIFFER_FUSEKI_PORT)/$$/datasets'

run-docker-redis-test:
	@ echo -e '$(BUILD_PRINT)Starting redis'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose-tests.yml --env-file infra/.env up -d rdf-differ-redis

run-docker-api-test:
	@ echo -e '$(BUILD_PRINT)Starting api'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose-tests.yml --env-file infra/.env up -d rdf-differ-api

run-docker-ui-test:
	@ echo -e '$(BUILD_PRINT)Starting ui'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose-tests.yml --env-file infra/.env up -d rdf-differ-ui

run-docker-celery-test:
	@ echo -e '$(BUILD_PRINT)Starting celery worker'
	@ docker compose -p rdf-differ-${ENVIRONMENT} --file infra/docker-compose-tests.yml --env-file infra/.env up -d rdf-differ-celery-worker

# it is advisable to run this separately before and not as a dependency of the test to ensure no race condition occurs (tests starting before services are ready)
start-services-test: | run-docker-fuseki-test run-docker-redis-test run-docker-celery-test run-docker-api-test
	@ echo "$(BUILD_PRINT)All docker services for testing started; waiting 5s for them to stabilize"
	@ sleep 5

test: | install-python-dependencies-dev test-data-fuseki
	@ echo "$(BUILD_PRINT)Running tests using Docker services"
	@ poetry run pytest --cov=rdf_differ --cov-report=term-missing --cov-report=xml

test-unit:
	@ echo "$(BUILD_PRINT)Running unit tests"
	@ poetry run pytest tests/unit -m unit

test-feature:
	@ echo "$(BUILD_PRINT)Running BDD feature tests"
	@ poetry run pytest tests/feature -m feature

generate-models:
	@ echo "$(BUILD_PRINT)Generating Pydantic models from model/schema.yaml (LinkML seam — DEC-6, not yet authoritative)"
	@ poetry run python -c "import linkml" 2>/dev/null || { echo "$(WARN_PRINT)linkml not installed. Run: poetry add --group model 'linkml>=1.7'  (see model/README.md)"; exit 1; }
	@ poetry run gen-pydantic model/schema.yaml > rdf_differ/domain/_generated_model.py
	@ echo "$(MSG_PRINT)Wrote rdf_differ/domain/_generated_model.py (preview — not wired in; see model/README.md)"

lint:
	@ echo "$(BUILD_PRINT)Linting the code (Ruff)"
	@ poetry run ruff check rdf_differ tests

format:
	@ echo "$(BUILD_PRINT)Formatting the code (Ruff)"
	@ poetry run ruff format rdf_differ tests

typecheck:
	@ echo "$(BUILD_PRINT)Type-checking (mypy)"
	@ poetry run mypy rdf_differ

check-architecture:
	@ echo "$(BUILD_PRINT)Checking architecture boundaries (import-linter)"
	@ poetry run lint-imports --config .importlinter

# Aggregate quality gate: lint + types + architecture (all green).
check-quality: lint typecheck check-architecture

check-all: check-quality
	@ $(MAKE) test

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
DEFAULT_PROFILE ?= owl-core
DEFAULT_TEMPLATE ?= html
PREFERRED_PROFILES ?= owl-core shacl-core skos-core
PREFERRED_TEMPLATES ?= html asciidoc

# Derived paths
TEMPLATE_SRC_BASE = $(TEMPLATE_OUTPUT_DIR)/$(DEFAULT_PROFILE)
TEMPLATE_QUERIES_SRC = $(TEMPLATE_SRC_BASE)/queries
TEMPLATE_HTML_SRC = $(TEMPLATE_SRC_BASE)/$(DEFAULT_TEMPLATE)

TEMPLATE_DEST_BASE = resources/templates/$(DEFAULT_PROFILE)-en-only
TEMPLATE_QUERIES_DEST = $(TEMPLATE_DEST_BASE)/queries
TEMPLATE_HTML_DEST = $(TEMPLATE_DEST_BASE)/template_variants/$(DEFAULT_TEMPLATE)/templates

update_template:
	@ echo "$(BUILD_PRINT)Updating templates from $(TEMPLATE_SRC_BASE)"
	@ mkdir -p $(TEMPLATE_QUERIES_DEST)
	@ mkdir -p $(TEMPLATE_HTML_DEST)
	@ echo "$(MSG_PRINT)Copying queries from $(TEMPLATE_QUERIES_SRC) to $(TEMPLATE_QUERIES_DEST)"
	@ cp -r $(TEMPLATE_QUERIES_SRC)/* $(TEMPLATE_QUERIES_DEST)/
	@ echo "$(MSG_PRINT)Copying $(DEFAULT_TEMPLATE) templates from $(TEMPLATE_HTML_SRC) to $(TEMPLATE_HTML_DEST)"
	@ cp -r $(TEMPLATE_HTML_SRC)/* $(TEMPLATE_HTML_DEST)/
	@ echo "$(MSG_PRINT)Template update completed"

update_all_templates:
	@ for profile in $(PREFERRED_PROFILES); do \
		for type in $(PREFERRED_TEMPLATES); do \
			echo "$(BUILD_PRINT)Updating $$type templates for $$profile"; \
			src_base=$(TEMPLATE_OUTPUT_DIR)/$$profile; \
			queries_src=$$src_base/queries; \
			type_src=$$src_base/$$type; \
			dest_base=resources/templates/$$profile-en-only; \
			queries_dest=$$dest_base/queries; \
			type_dest=$$dest_base/template_variants/$$type/templates; \
			mkdir -p $$queries_dest; \
			mkdir -p $$type_dest; \
			echo "$(MSG_PRINT)Copying queries from $$queries_src to $$queries_dest"; \
			cp -r $$queries_src/* $$queries_dest/; \
			echo "$(MSG_PRINT)Copying $$type templates from $$type_src to $$type_dest"; \
			cp -r $$type_src/* $$type_dest/; \
			echo "$(MSG_PRINT)Template update for $$profile ($$type) completed"; \
		done \
	done

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
