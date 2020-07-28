.PHONY: test install lint start-services stop-services

include docker/.env-dev

BUILD_PRINT = \e[1;34mSTEP: \e[0m

install:
	@ echo -e "$(BUILD_PRINT)Installing the requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt

test:
	@ echo -e "$(BUILD_PRINT)Running the tests"
	@ pytest

lint:
	@ echo -e "$(BUILD_PRINT)Linting the code"
	@ flake8 || true

start-fuseki:
	@ echo '$(BUILD_PRINT)Starting Fuseki on port $(if $(FUSEKI_PORT),$(FUSEKI_PORT),'default port')'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev up -d

stop-fuseki:
	@ echo "$(BUILD_PRINT)Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev down

fuseki-create-test-dbs:
	@ echo  "$(BUILD_PRINT)Building dummy "subdiv" and "abc" datasets at http://localhost:$(if $(FUSEKI_PORT),$(FUSEKI_PORT),unknown port)/$$/datasets"
	@ sleep 2
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=subdiv'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -d 'dbType=mem&dbName=abc'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'

clean-data:
	@ echo "$(BUILD_PRINT)Deleting the $(DATA_FOLDER)"
	@ sudo rm -rf $(DATA_FOLDER)

start-service: start-fuseki fuseki-create-test-dbs

stop-service: stop-fuseki clean-data

FEATURES_FOLDER = test/features
STEPS_FOLDER = test/steps
FEATURE_FILES := $(wildcard $(FEATURES_FOLDER)/*.feature)
EXISTENT_TEST_FILES = $(wildcard $(STEPS_FOLDER)/*.py)
HYPOTHETICAL_TEST_FILES :=  $(addprefix $(STEPS_FOLDER)/test_, $(notdir $(FEATURE_FILES:.feature=.py)))
TEST_FILES := $(filter-out $(EXISTENT_TEST_FILES),$(HYPOTHETICAL_TEST_FILES))

generate-tests-from-features: $(TEST_FILES)
	@ echo -e '$(BUILD_PRINT) test files to be generated are: $(TEST_FILES)'
	@ echo -e '$(BUILD_PRINT)Done generating missing feature files'
	@ echo -e '$(BUILD_PRINT)Verifying if there are any missing step implementations'
	@ py.test --generate-missing --feature $(FEATURES_FOLDER)

$(addprefix $(STEPS_FOLDER)/test_, $(notdir $(STEPS_FOLDER)/%.py)): $(FEATURES_FOLDER)/%.feature
	@ echo -e '$(BUILD_PRINT)Generating the testfile "$@"  from "$<" feature file'
	@ pytest-bdd generate $< > $@
	@ sed -i  's|features|../features|' $@

all:
	install test