#  RDF Differ

A service for calculating the difference between versions of a given RDF dataset. Current implementation is based on the [skos-history tool](https://github.com/eu-vocabularies/skos-history).
See the [Wiki page of the original repository](https://github.com/jneubert/skos-history/wiki/Tutorial) for more technical details.

![RDF differ test](https://github.com/eu-vocabularies/rdf-differ/workflows/RDF%20differ%20test%20and%20lint/badge.svg)
[![codecov](https://codecov.io/gh/eu-vocabularies/rdf-differ/branch/master/graph/badge.svg)](https://codecov.io/gh/eu-vocabularies/rdf-differ)

# Installation

Make sure that you are running `Docker` and have the correct permissions set. If not, run the following lines to install it. 

```bash
sudo apt -y install docker.io docker-compose

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

To build and the containers run:
```bash
make build
```

Install test/dev dependencies:

```bash
make install
```

To run the tests:
> Make sure that fuseki is running: `make fuseki-create-test-dbs`. (This command will create 2 dummy datasets.)
```bash
make fuseki-create-test-dbs
make test
```

# Usage

## Start services
To run the docker containers for the `rdf-differ` `api` and `ui`, and `fuseki`:

```bash
make start-services
```

The diffing services are split into:

service | URL | info
------- | ------- | ----
`differ-api` | [localhost:4030](http://localhost:4030) | _access [localhost:4030/ui](http://localhost:4030/ui) for the swagger interface_ 
`differ-ui` | [localhost:8030](http://localhost:8030)

## Differ API

> Go to this link [localhost:4030/ui](http://localhost:4010/ui) to access the online definition of the API.
![list of diffs page](docs/images/api-swagger-2020-10.png)

## Differ UI

> To create a new diff you can access [http://localhost:8030/create-diff](http://localhost:8030/create-diff)
![list of diffs page](docs/images/create-diff-2020-10.png)

> To list the existent diffs you can access [http://localhost:8030](http://localhost:8030/)
![list of diffs page](docs/images/list-diffs-202010.png)

## Stop services
To stop the containers run:
```bash
make stop-services
```

## Performance estimates

Environment: AWS EC2 p2.medium and running the operations with Fuseki triple store.

* Calculating the diff for two versions of a large NAL (used Corporate Bodies) ~ 58s
* Generating the diff report for two versions of a large NAL (used Corporate Bodies)  ~  12 min

# Contributing
You are more than welcome to help expand and mature this project. We adhere to [Apache code of conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.   

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository before making a change.

## Licence 
This project is licensed under [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) licence. 

Powered by [Meaningfy](https://github.com/meaningfy-ws).

