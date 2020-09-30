![RDF differ test and lint](https://github.com/eu-vocabularies/rdf-differ/workflows/RDF%20differ%20test%20and%20lint/badge.svg)
[![codecov](https://codecov.io/gh/eu-vocabularies/rdf-differ/branch/master/graph/badge.svg)](https://codecov.io/gh/eu-vocabularies/rdf-differ)

# rdf-differ
A service for calculating the difference between versions of a given RDF dataset. 

## to run the development environment *with docker*

Make sure that you are running `Docker` and have the correct permissions set.

```bash
sudo apt -y install docker.io docker-compose

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```
---
To create the containers run:
```bash
make build-dev
```
To run the docker containers for the `rdf-differ` `api` and `ui`, and `fuseki` container:
```bash
make start-dev
```

The default ports for accessing:

service | URL | info
------- | ------- | ----
`fuseki`| [localhost:3030](http://localhost:3030) | username: `admin` password: `admin`
`api` | [localhost:3040](http://localhost:3040) | _access [localhost:3040/ui](http://localhost:3040/ui) for the swagger interface_ 
`ui` | [localhost:3050](http://localhost:3050)


To stop the containers run:
```bash
make stop-dev
```

## to run only the triple store (`fuseki`)
To build: 
```bash
make build-fuseki
```

To run: 
```bash
make start-fuseki
```

To stop fuseki:
```bash
make stop-fuseki
``` 

## to run the tests and linting
Install test/dev dependencies:
```bash
make install-dev
```

To run the tests:
> Make sure that fuseki is running: `make start-bootstrap-fuseki`. (This command will create 2 dummy datasets.)
```bash
make test
```

To run linting:
```bash
make lint
```

## to run *without docker*

Install dev requirements:

```bash
make install-dev
```

Run dev servers:
> Make sure the python dev environment is activated.

service | commands 
------- | ------- 
`api` | ```export FLASK_APP=rdf_differ.entrypoints.api.run``` <br> ```export FLASK_ENV=development``` <br> ```flask run --host=0.0.0.0 --port=3040```  
`ui` | ```export FLASK_APP=rdf_differ.entrypoints.ui.run``` <br> ```export FLASK_ENV=development``` <br> ```flask run --host=0.0.0.0 --port=3050```  


## Miscellaneous
Populate `fuseki` database with 5 datasets (`subdiv`, `eurovoc-fragment`, `countries-fragment`, `cob-fragment`, and `treaty-fragment` )
> Make sure that fuseki is running: `make start-fuseki`
```bash
make populate-fuseki
```

Generate feature steps:
```bash
make generate-tests-from-features
```

## Source code structure

Please refer to [this](https://meaningfy.atlassian.net/l/c/bK0uVdG7) page.


