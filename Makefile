.PHONY: test install lint start-services stop-services docker-stop-dev docker-start-dev docker-build-dev

include .env-dev

BUILD_PRINT = \e[1;34mSTEP: \e[0m

#-----------------------------------------------------------------------------
# Basic commands
#-----------------------------------------------------------------------------
env-export: .env-dev
	@ $(shel SHELL $(sed -ne '/^export / {p;d}; /.*=/ s/^/export / p' .env-dev))

install:
	@ echo "$(BUILD_PRINT)Installing the requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt

test: env-export
	@ echo "$(BUILD_PRINT)Running the tests"
	@ pytest

lint:
	@ echo "$(BUILD_PRINT)Linting the code"
	@ flake8 || true

#-----------------------------------------------------------------------------
# Fuseki related commands
#-----------------------------------------------------------------------------

start-fuseki:
	@ echo "$(BUILD_PRINT)Starting Fuseki on port $(if $(FUSEKI_PORT),$(FUSEKI_PORT),'default port')"
	@ docker-compose --file docker-compose.yml --env-file .env-dev up -d fuseki

stop-fuseki:
	@ echo "$(BUILD_PRINT)Stopping Fuseki"
	@ docker-compose --file docker-compose.yml --env-file .env-dev down

fuseki-create-test-dbs:
	@ echo "$(BUILD_PRINT)Building dummy "subdiv" and "abc" datasets at http://localhost:$(if $(FUSEKI_PORT),$(FUSEKI_PORT),unknown port)/$$/datasets"
	@ sleep 2
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=subdiv'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=abc'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'

clean-data:
	@ echo "$(BUILD_PRINT)Deleting the $(DATA_FOLDER)"
	@ sudo rm -rf $(DATA_FOLDER)

start-service: start-fuseki fuseki-create-test-dbs

stop-service: stop-fuseki clean-data

#-----------------------------------------------------------------------------
# Gherkin feature and acceptance test generation commands
#-----------------------------------------------------------------------------

FEATURES_FOLDER = test/features
STEPS_FOLDER = test/steps
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

#-----------------------------------------------------------------------------
# Docker commands
#-----------------------------------------------------------------------------

docker-build-dev:
	@ echo -e '$(BUILD_PRINT)Building the Docker container locally'
	@ docker-compose --file docker-compose.yml --env-file .env-dev build

docker-start-dev:
	@ echo -e '$(BUILD_PRINT)Starting the docker services (dev environment)'
	@ docker-compose --file docker-compose.yml --env-file .env-dev up -d rdf-differ

docker-stop-dev:
	@ echo -e '$(BUILD_PRINT)Stopping the docker services (prod environment)'
	@ docker-compose down

#-----------------------------------------------------------------------------
# Default
#-----------------------------------------------------------------------------
all:
	install test