# Optional: a fresh clone has no infra/.env yet — copy infra/.env.example first.
-include infra/.env

.DEFAULT_GOAL := help

BUILD_PRINT = \e[1;34mSTEP: \e[0m
MSG_PRINT   = \e[1;34mINFO: \e[0m
WARN_PRINT  = \e[1;34mWARNING: \e[0m

DEB_OS  = $(shell command -v apt > /dev/null && echo 1)
RPM_OS  = $(shell command -v yum > /dev/null && echo 1)

# DRY docker-compose invocations (prod stack, test stack, traefik).
COMPOSE      = docker compose -p rdf-differ-$(ENVIRONMENT) --file infra/docker-compose.yml --env-file infra/.env
COMPOSE_TEST = docker compose -p rdf-differ-$(ENVIRONMENT) --file infra/docker-compose-tests.yml --env-file infra/.env
TRAEFIK      = docker compose -p common --file ./infra/traefik/docker-compose.yml --env-file infra/.env

.PHONY: help install install-dev \
        format lint typecheck check-architecture check-quality check check-all ci \
        test test-unit test-feature \
        start stop status start-services-test teardown-services \
        local-deps local-fuseki-setup local-fuseki local-api local-ui local-redis local-stop \
        generate-models set-report-template run-dev-ui \
        _test-data-fuseki

help:
	@ echo "RDF Differ — make targets:"
	@ echo ""
	@ echo "  Setup     install              Python runtime deps (Poetry; no sudo)"
	@ echo "            install-dev          + dev/test/lint/docs groups (no sudo)"
	@ echo "  Quality   check                lint + types + architecture (the gate)"
	@ echo "            format               auto-format (Ruff, writes)"
	@ echo "            lint typecheck check-architecture   run one in isolation"
	@ echo "  Tests     test-unit            unit only — fast, no services needed"
	@ echo "            test-feature         BDD only (needs the stack — see Docker)"
	@ echo "            test                 full suite + coverage (needs the stack)"
	@ echo "            ci                   check + full test suite"
	@ echo "  Docker    start / stop         full stack (traefik + services) up/down"
	@ echo "            status               pretty live panel: what's up and where"
	@ echo "            start-services-test  bring up + seed the test stack (run before 'test')"
	@ echo "            teardown-services    stop + remove the stack and volumes"
	@ echo "  Local     local-deps           apt/yum install Java + Redis (sudo; only for no-Docker)"
	@ echo "            local-redis local-fuseki-setup local-fuseki local-api local-ui local-stop"
	@ echo "  Other     generate-models  set-report-template  run-dev-ui"

#-----------------------------------------------------------------------------
# Setup
#-----------------------------------------------------------------------------
install:
	@ echo "$(BUILD_PRINT)Installing runtime dependencies (Poetry)"
	@ poetry install --only main
	@ echo "$(MSG_PRINT)Quick start with Docker: make start  |  run tests: make install-dev"

install-dev:
	@ echo "$(BUILD_PRINT)Installing all dependency groups (Poetry)"
	@ poetry install --with dev,test,lint,docs

# Opt-in: only needed to run Fuseki/Redis natively (the Local targets). Docker users
# never need this. Requires sudo and installs Java + Redis.
local-deps:
ifeq ($(DEB_OS), 1)
	@ sudo apt install redis-server default-jre
else ifeq ($(RPM_OS), 1)
	@ sudo yum install redis java-11-openjdk
else
	@ echo "$(WARN_PRINT)Unsupported OS — install Java 11+ and Redis 6+ yourself."
	false
endif

#-----------------------------------------------------------------------------
# Quality gate
#-----------------------------------------------------------------------------
format:
	@ echo "$(BUILD_PRINT)Formatting (Ruff)"
	@ poetry run ruff format rdf_differ tests

lint:
	@ echo "$(BUILD_PRINT)Linting (Ruff)"
	@ poetry run ruff check rdf_differ tests

typecheck:
	@ echo "$(BUILD_PRINT)Type-checking (mypy)"
	@ poetry run mypy rdf_differ

check-architecture:
	@ echo "$(BUILD_PRINT)Checking architecture boundaries (import-linter)"
	@ poetry run lint-imports --config .importlinter

check-quality:
	@ echo "$(BUILD_PRINT)Checking formatting (Ruff)"
	@ poetry run ruff format --check rdf_differ tests
	@ $(MAKE) lint typecheck check-architecture

check-all: check-quality
	@ $(MAKE) test

# Convention aliases (Meaningfy standard names).
check: check-quality
ci: check-all

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
test-unit:
	@ echo "$(BUILD_PRINT)Running unit tests"
	@ poetry run pytest tests/unit -m unit

test-feature:
	@ echo "$(BUILD_PRINT)Running BDD feature tests"
	@ poetry run pytest tests/feature -m feature

test:
	@ echo "$(BUILD_PRINT)Running the full suite with coverage"
	@ echo "$(MSG_PRINT)Needs the stack — run 'make start-services-test' first if it isn't up."
	@ poetry run pytest --cov=rdf_differ --cov-report=term-missing --cov-report=xml

#-----------------------------------------------------------------------------
# Docker stack
#-----------------------------------------------------------------------------
start:
	@ echo "$(BUILD_PRINT)Starting Traefik + RDF Differ services"
	@ docker network create proxy-net || true
	@ docker volume create rdf-differ-template-$(ENVIRONMENT)
	@ docker volume create rdf-differ-template
	@ $(TRAEFIK) up -d
	@ $(COMPOSE) up -d
	@ sleep 2
	@ ./infra/scripts/show_stack.sh infra/.env

status:
	@ ./infra/scripts/show_stack.sh infra/.env

stop:
	@ echo "$(BUILD_PRINT)Stopping Traefik + RDF Differ services"
	@ $(COMPOSE) stop
	@ $(TRAEFIK) down
	@ echo "$(MSG_PRINT)Stopped. Restart with: make start"

# CI/e2e test stack — one compose up brings up every test service (build on demand).
start-services-test:
	@ echo "$(BUILD_PRINT)Bringing up the test stack (fuseki, redis, celery, api)"
	@ docker network create proxy-net || true
	@ docker volume create rdf-differ-template-$(ENVIRONMENT)
	@ $(COMPOSE_TEST) up -d --build \
		rdf-differ-fuseki rdf-differ-redis rdf-differ-celery-worker rdf-differ-api
	@ echo "$(BUILD_PRINT)Waiting 5s for services to stabilise"
	@ sleep 5
	@ $(MAKE) _test-data-fuseki

teardown-services:
	@ echo "$(BUILD_PRINT)Tearing down the stack (containers + volumes)"
	@ $(COMPOSE_TEST) down --volumes --remove-orphans

_test-data-fuseki:
	@ echo "$(BUILD_PRINT)Creating dummy 'subdiv' and 'abc' test datasets on Fuseki :$(RDF_DIFFER_FUSEKI_PORT)"
	@ sleep 5
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=subdiv' 'http://localhost:$(RDF_DIFFER_FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=abc'    'http://localhost:$(RDF_DIFFER_FUSEKI_PORT)/$$/datasets'

#-----------------------------------------------------------------------------
# Local services (no Docker) — run each in its own shell
#-----------------------------------------------------------------------------
local-redis:
ifeq ($(DEB_OS), 1)
	@ echo "$(WARN_PRINT)Backing up and replacing the system redis.conf as root!"
	@ sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.rdf_differ.bak -v
	@ sudo cp infra/redis.conf /etc/redis/redis.conf -v
	@ sudo systemctl restart redis.service
else ifeq ($(RPM_OS), 1)
	@ sudo systemctl enable redis --now
else
	@ echo "$(WARN_PRINT)Unsupported OS — start Redis yourself (see infra/redis.conf)."
	false
endif

local-fuseki-setup:
	@ ./infra/scripts/setup_fuseki.sh

local-fuseki:
	@ ./fuseki/fuseki-server -q

local-api:
	@ ./infra/scripts/run_api.sh

local-ui:
	@ ./infra/scripts/run_ui.sh

local-stop:
	@ ./infra/scripts/stop_gunicorn.sh

#-----------------------------------------------------------------------------
# Other
#-----------------------------------------------------------------------------
generate-models:
	@ echo "$(BUILD_PRINT)Generating Pydantic models from model/schema.yaml (LinkML seam — DEC-6, not authoritative)"
	@ poetry run python -c "import linkml" 2>/dev/null || { echo "$(WARN_PRINT)linkml not installed: poetry add --group model 'linkml>=1.7' (see model/README.md)"; exit 1; }
	@ poetry run gen-pydantic model/schema.yaml > rdf_differ/diffing/domain/_generated_model.py
	@ echo "$(MSG_PRINT)Wrote rdf_differ/diffing/domain/_generated_model.py (preview — not wired in)"

set-report-template:
	@ echo "$(BUILD_PRINT)Copying custom template into the shared volume"
	@ docker rm temp | true
	@ docker volume rm rdf-differ-template | true
	@ docker volume create rdf-differ-template
	@ docker container create --name temp -v rdf-differ-template:/data busybox
	@ docker cp $(location). temp:/data
	@ docker rm temp

run-dev-ui:
	@ FLASK_APP=rdf_differ.api.entrypoints.ui.run FLASK_DEBUG=1 poetry run flask run
