# eds4jinja2
An easy way to reports generation with Jinja2 templates. 

With Embedded Datasource Specifications inside Jinja2 templates, you can fetch the data you need on the spot. 

![test](https://github.com/meaningfy-ws/eds4jinja2/workflows/test/badge.svg)
[![codecov](https://codecov.io/gh/meaningfy-ws/eds4jinja2/branch/master/graph/badge.svg)](https://codecov.io/gh/meaningfy-ws/eds4jinja2)
[![Documentation Status](https://readthedocs.org/projects/eds4jinja2/badge/?version=latest)](https://eds4jinja2.readthedocs.io/en/latest/?badge=latest)

![PyPI](https://img.shields.io/pypi/v/eds4jinja2?color=teal&label=version)
![PyPI - Status](https://img.shields.io/pypi/status/eds4jinja2)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/eds4jinja2)
![PyPI - License](https://img.shields.io/pypi/l/eds4jinja2?color=green)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/eds4jinja2)

Specify the data sources in your JINJA templates directly.

```jinja2
{% set content, error = from_file(path).fetch_tree() %} \n
content:  {{ content }}\n
error: {{ error }}\n
```

```jinja2
{% set content, error =
    from_endpoint(endpoint).with_query(query_string).fetch_tabular() %}
content:  {{ content }} \n
error: {{ error }} \n
```

# Installation

```shell script
pip install eds4jinja2
```

# Usage

[Read the docs here](https://eds4jinja2.readthedocs.io/en/latest/)  

## Contributing
You are more than welcome to help expand and mature this project. We adhere to [Apache code of conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.   
When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository before making a change.

## Licence 
This project is licensed under [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
Powered by [Meaningfy](https://github.com/meaningfy-ws).
