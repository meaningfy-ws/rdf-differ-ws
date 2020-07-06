.PHONY: test

install:
	@echo "installing the necessary stuff"
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	@echo "running the tests"
	pytest

#format:
#	black rdf_differ

#lint:
#	pylint --disable=R,C hello.py

all:
	install test


