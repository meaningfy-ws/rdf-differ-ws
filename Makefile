.PHONY: test install lint start-services stop-services

BUILD_PRINT = \e[1;34mSTEP: \e[0m

install:
	@ echo -e "$(BUILD_PRINT)Installing the requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt

test:
	@ echo -e "$(BUILD_PRINT)Running the tests"
	@ pytest || true

lint:
	@ echo -e "$(BUILD_PRINT)Linting the code"
	@ flake8 || true

start-services:
	@ echo -e "$(BUILD_PRINT)Starting Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev up -d

stop-services:
	@ echo -e "$(BUILD_PRINT)Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env-dev down

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


