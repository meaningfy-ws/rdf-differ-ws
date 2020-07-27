.PHONY: test install lint start-services stop-services

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
	@ echo 'Starting Fuseki on port $(if $(FUSEKI_PORT),$(FUSEKI_PORT),'3030')'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev up -d

stop-fuseki:
	@ echo "Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev down

fuseki-create-test-dbs:
	@ echo  'Building dummy "subdiv" and "abc" datasets at http://localhost:$(FUSEKI_PORT)/$$/datasets'
	@ sleep 2
	@ curl --anyauth --user 'admin:admin' -i -d 'dbType=mem&dbName=subdiv'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'
	@ curl --anyauth --user 'admin:admin' -i -d 'dbType=mem&dbName=abc'  'http://localhost:$(FUSEKI_PORT)/$$/datasets'

clean-data:
	@ echo 'Deleting the $(DATA_FOLDER)'
	@ sudo rm -rf $(DATA_FOLDER)

start-service: start-fuseki fuseki-create-test-dbs

stop-service: stop-fuseki clean-data

#generate-api:
#	@echo "Generating API from OpenAPI 3.0 description using the standard openapitools/openapi-generator-cli"

FEATURES_FOLDER = test/features
STEPS_FOLDER = test/steps
FEATURE_FILES := $(wildcard $(FEATURES_FOLDER)/*.feature)
TEST_FILES :=  $(addprefix $(STEPS_FOLDER)/test_, $(notdir $(FEATURE_FILES:.feature=.py)))

generate-tests-from-features: $(TEST_FILES)
	@ echo -e '$(BUILD_PRINT)Done generating missing feature files'
	@ echo -e '$(BUILD_PRINT)Verifying if there are any missing step implementations'
	@ py.test --generate-missing --feature $(FEATURES_FOLDER)

$(addprefix $(STEPS_FOLDER)/test_, $(notdir $(STEPS_FOLDER)/%.py)): $(FEATURES_FOLDER)/%.feature
	@ echo -e '$(BUILD_PRINT)Generating the testfile "$@"  from "$<" feature file'
	@ pytest-bdd generate $< > $@
	@ sed -i  's|features|../features|' $@

all:
	install test