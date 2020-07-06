![RDF differ test and lint](https://github.com/eu-vocabularies/rdf-differ/workflows/RDF%20differ%20test%20and%20lint/badge.svg)
[![codecov](https://codecov.io/gh/eu-vocabularies/rdf-differ/branch/master/graph/badge.svg)](https://codecov.io/gh/eu-vocabularies/rdf-differ)

# rdf-differ
A service for calculating the difference between versions of a given RDF dataset. 


## starting the triple store 
    make start-services

## stopping the triple store 
    make stop-services

## running the tests
    make test



## Install

* Required libs

```
make install
```

* Docker

```bash
echo "--------------------------------------------------------------"
echo "Installing Docker"
echo "--------------------------------------------------------------"
sudo apt -y install docker.io docker-compose

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

