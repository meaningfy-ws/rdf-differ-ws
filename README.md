![RDF differ test and lint](https://github.com/eu-vocabularies/rdf-differ/workflows/RDF%20differ%20test%20and%20lint/badge.svg)
[![codecov](https://codecov.io/gh/eu-vocabularies/rdf-differ/branch/master/graph/badge.svg)](https://codecov.io/gh/eu-vocabularies/rdf-differ)

# rdf-differ
A service for calculating the difference between versions of a given RDF dataset. 

## to run the development environment through docker
To create the containers run:
```bash
make build-dev
```
To run the docker containers (both `rdf-differ` and `fuseki`):
```bash
make run-dev
```
To stop the containers run:
```bash
make stop-dev
```

## to run the triple store (fuseki only)
To build and run: 
```bash
    make run-fuseki
```

To stop fuseki:
```bash
    make stop-fuseki
``` 

## to run the tests
To install test/dev dependencies
```bash
    make install-dev
```

To run the tests (make sure that fuseki is running `make run-fuseki`)
```bash
    make test
```


## to run without docker

Install dev requirements

```bash
make install-dev
```

Install production requirements
```bash
make install-prod
```

* Docker

```bash
sudo apt -y install docker.io docker-compose

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

## Source code structure

Please refer to [this](https://meaningfy.atlassian.net/l/c/bK0uVdG7) page.


