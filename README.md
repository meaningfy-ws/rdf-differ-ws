# RDF Differ

A service for calculating the difference between versions of a given RDF dataset. Current implementation is based on the [skos-history tool](https://github.com/eu-vocabularies/skos-history). See the [wiki page of the original repository](https://github.com/jneubert/skos-history/wiki/Tutorial) for more technical details.

![RDF differ test](https://github.com/eu-vocabularies/rdf-differ/workflows/RDF%20differ%20test%20and%20lint/badge.svg)
[![codecov](https://codecov.io/gh/eu-vocabularies/rdf-differ/branch/master/graph/badge.svg)](https://codecov.io/gh/eu-vocabularies/rdf-differ)

## Installation
> **NOTE**: The specified installation instructions are for development purposes only on a GNU/Linux operating system. _(Slight modifications are required for production use, including having a production level Fuseki server and Redis service available.)_

For Red Hat derivative systems, make sure that the EPEL (Extra Packages for Enterprise Linux) repository is enabled and added to the server's package lists. This is not currently handled automatically and can usually be installed by running:

```bash
sudo yum install epel-release
```

For Debian derivative systems, no additional package repository should be needed, for at least Ubuntu 18.04. While we do not test for Windows/WSL2
or Mac (because of some limitations with GitHub CI), those platforms should work as well.

RDF Differ uses fuseki (as the triplestore/database), celery (for multithreading programming), gunicorn (for serving), and redis (for queue-based pesistent storage). For the corresponding Docker micro-services, it uses traefik for the networking, _except when running tests_.

The applications are made available (by default) on ports [8030](http:localhost:8030) (ui), [4030](http:localhost:4030) (api), [3030](http:localhost:3030) (triplestore), [6379](http:localhost:6379) (redis), and [5555](http:localhost:5555) (celery). This is configurable via `bash/.env` and `docker/.env`.

> For the docker services with traefik, you have to access these differently, through their local domains instead, for e.g. https://rdf.localhost/ (ui). See https://monitor.localhost > Routers > Explore (`Host(...)`).

> For the docker services with traefik, on Windows/WSL2, `curl` works only _outside_ WSL without SSL/TLS, e.g. via Git Bash `curl https://api.localhost/diffs --insecure`.

For all output except fuseki, see the `logs` folder, e.g. `tail -f logs/api.log` to follow the API output. For fuseki, run `docker logs fuseki` (add `-f` to follow).

> For the docker services with traefik, you have to get to the logs from inside the container, for example, via ` docker exec -it rdf-differ-api-dev tail -f logs/api.log` where `rdf-differ-api-dev` is the name of the API container (see `docker ps`).

[This file](curl-examples.md) contains a list of examples on how to use the api. (please translate the URLs accordingly for traefik domains as mentioned above)

### With docker micro-services

Run the following command to install all required dependencies on either a Debian or Red Hat system, start up required (docker) services -- including databases -- and run the application (api + ui):

```bash
make
```

By default, that runs the first build target, currently `make setup`. You must have `docker` and `docker-compose` installed if you would like to use the micro-services to run everything, everywhere, all at once.

If you only want to install prerequisite software and dependencies without starting any service or database, run:

```bash
make install
```

**WARNING:** Some commands are **run as root** with _sudo_.

If you install operating system (OS) packages yourself (if in case you run an unsupported OS or you don't want to run as root), run:

```bash
make install-python-dependencies # add -dev if you want to run tests
```

If you only want to start up ALL the prerequisite docker services (in case you have already run `install`):

```bash
make start
```

This creates the required local docker images (and fetches some third-party ones from DockerHub), prerequisite volumes (for file storage in the containers), and finally runs all the containers.

To stop ALL docker services at any time:

```bash
make stop
```

> If at any time you think you are experiencing odd behaviour, such as a `500 Internal Server Error` or `404 Not Found`, use your preferred method to completely remove (purge) the docker containers, images and volumes related to this project, files inside `reports` and `fuseki-data`, and redo everything.

### With local and system services

To run the triplestore database (fuseki) server locally and not via docker (on first setup accept the default values):

```bash
make setup-local-fuseki
make run-local-fuseki
```
_leave this terminal session open_

That will fetch, install in and run fuseki from the current working directory, which can be run as a user _without requiring root_.

To set up and run a _system_ redis server which _does_ need to be **run as root**:

```bash
make run-system-redis
```

There is currently no local alternative to this to run as a user. If that is a concern, please use the docker micro-services approach.

**WARNING:** Like `setup` and to some extent `install`, this runs as root and additionally replaces a system configuration file. If you get errors about configuration directives, you are likely running an older OS with older redis (e.g. Ubuntu 18.04 does not have the redis version that's required).

To run the api (including celery) locally:

```bash
make run-local-api
```

To run the ui locally:

```bash
make run-local-ui
```

To stop both api and ui servers (leaving only fuseki and the system redis running, which you must control on your own):

```bash
make stop-local-applications
```

To reiterate, if you are running the project for the first time this would be the commands to run in sequence:

```bash
make install-os-dependencies
make install-python-dependencies
make run-system-redis
make run-local-api
make run-local-ui
make setup-local-fuseki
```

In a separate terminal process remember to run and keep open:

```bash
make run-local-fuseki
```

## Testing

The test suite spins up certain duplicate docker services _without_ traefik, so
access to those specific services are directly through the localhost and respective
ports. Run the following to run everything:

```bash
make test
```

This creates the `subdiv` and `abc` dummy datasets once in the running fuseki service, and a `dataset{ID}` dataset (where `{ID}` is a short random ID) as many times as the tests are run. The `db` folder is populated by the tests.

## Adding a new Application Profile template
For adding a new Application Profile (AP) create a new folder under [resources/templates](resources/templates) with the name
of your new AP, following the structure explained below.

Folder structure needed for adding a new AP:

```
resources/templates
│   
└───<new_application_profile>
│   │
│   └───queries          <--- folder that contains SPARQL queries
│   │    │   query1.rq
│   │    │   query2.rq
│   │    │   ...
│   │    
│   └───template_variants
│       │
│       └───html        <--- folder that contains files needed for a html template
│       │
│       │  
│       └───json        <--- folder that contains files needed for a json template
```

### Html template variant

```
html                 <--- the template_variants subfolder 
│
└───config.json      <--- configuration file
│   
└───templates        <--- this is the folder that contains the jinja html templates
   │
   │  file1.html
   │  file2.html
   │  main.html

```

*Note* Make sure that in the templates folder there is an entrypoint file named the same as the one defined in the config.json file (i.e `"template": "main.html"`)

### HTML template structure

The HTML template is built be combining four major parts as layout, main, macros and sections. The layout file (layout.html)
will have the rules of how the report will look like in terms of positioning and styling. Macros will contain all the 
jinja2 macros used across the template. A section represents the result of a query that was run with additional html and
will be used to build the report.
As the name suggest the main file of the html template is main.html. Here is where every other file that are a different 
section in the report are included and will form the HTML report. 

Example of including a section in the main html file:

`{% include "conceptscheme/added_instance_concept_scheme.html" with context %}`

Each section file has one or more variables where the SPARQL query result is saved 
as a pandas dataframe.

Example

`{% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["added_instance_concept.rq"]).fetch_tabular() %})`

*Note* The system has in place an autodiscover process for the SPARQL queries in the queries folder. Make sure that the file 
name added for the variable above (`added_instance_concept.rq`) exists in the queries folder.

### Adjusting an existing Html template

**Adding a new query/section**

To add a query a new file needs to be created and added into the queries folder as the system will autodiscover
this. After this is done a new html file that will represent a new section needs to be created. The content of this is 
similar to the existing ones and the only thing that needs to be adjusted will be the query file name in the content
variable definition as presented below:

```
{% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["new_query_file.rq"]).fetch_tabular() %})
```

As a final step, the created html file needs to be included in the report and to do this it has to be included in the 
main.html file by using the include block.

```
       --- relative path to the new html path
      {% include "conceptscheme/labels/new file name.html" with context %}
```

For adding a count query that will be used in the statistics 
section the steps are a bit different. First, will need to add the new query file following the naming conventions and 
adding the prefix count_ to the file name in queries folder. After this, the statistics.html will need to be modified as follows:

1. Create a new row in the existing table by using `<tr>` tag.
2. Create the necessary columns for the newly created row. Each row should have 7 values as this is the defined table 
structure (Property group, Property ,Added, Deleted, Updated, Moved, Changed) and each of them should be included by 
using a `<td>` tag if you are not using the block below to autogenerate this. 

```
    {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["new_count_query_file_name.rq"]).fetch_tabular() %}
    
    {% call mc.render_fetch_results(content, error) %}

    {{ mc.count_value(content) }}
    {% endcall %}
```

*Note* The order of the cells is important. If you don't want to include a type of operation just create a `<td>` with a
desired value (i.e `<td>N/A</td>`). To avoid confusions, count queries should be added for all type of operations.
The example below will show how to add a complete row in the statistics section of the report

```
<tr>
    <td>Name of the property group</td>
    <td>Name of the property</td>
    --- this will bring the number generated from the SPARQL query for added occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_added_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for deleted occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_deleted_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for updated occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_updated_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for moved occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_moved_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for changed occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_changed_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}

</tr>
```

**Removing a query/section**

To remove a section from the existing report you just need to delete or comment the include statement from the main.html
file. If you decide to delete the include statement it's recommended to delete the query from the queries folder to avoid 
confusions later on.

```
      Include statement
            {% include "conceptscheme/labels/added_property_concept_scheme_pref_label.html" with context %}
```

To remove a row from the statistics section just delete or comment the `<tr>` bloc from the statistics.html file 

```
<tr>
    <td>Labels</td>
    <td>skos:prefLabel</td>
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_added_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_deleted_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_updated_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_moved_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_changed_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
</tr>
```

## Json template variant

### Folder structure

```
json                 <--- the template_variants subfolder
│
└───config.json      <--- configuration file
│   
└───templates        <--- this is the folder that contains the jinja json templates
   │
   │  main.json

```

*Note* Make sure that in the templates folder there is an entrypoint file named the same as the one defined in the config.json file (i.e `"template": "main.json"`)

### Template structure
The Json report is automatically built by running all queries that are found in the queries folder as the system has 
autodiscover process for this. In the beginning of this report there will be 3 keys that will show the metadata of the 
report like dataset used, created time and application profile used.  Each query result can be identified in the report 
by the filename and will contain a results key that will represent the result set brought back by the query

```
{
   --- Metadata
   
    "dataset_name": "name of dataset",
    "timestamp": "time",
    "application_profile": "application profile namme",
    
    --- Query result set
    
    "count_changed_property_concept_definition.rq":
    {
        "head":
        {
            "vars":
            [
                "entries"
            ]
        },
        "results":
        {
            "bindings":
            [
                {
                    "entries":
                    {
                        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                        "type": "literal",
                        "value": "0"
                    }
                }
            ]
        }
    }
}
```

### Adjusting an existing Json template

**Removing a query/section**
To remove a query result set from the report simply remove the query from the queries folder. 
*Note* Doing this will also affect the html template and it's recommended to ajust the html template, if this exists as
a template variant for the application profile that you are working with, following the 
instruction above to avoid errors when generating the hmtl template variant. 

# Usage

The diffing services are split into:

service | URL | info
------- | ------- | ----
`differ-api` | [localhost:4030](http://localhost:4030) | _access [localhost:4030/ui](http://localhost:4030/ui) for the swagger interface_ 
`differ-ui` | [localhost:8030](http://localhost:8030)

## Differ UI

> To create a new diff you can access [http://localhost:8030/create-diff](http://localhost:8030/create-diff)
![list of diffs page](docs/images/create-diff-2020-10.png)

> To list the existent diffs you can access [http://localhost:8030](http://localhost:8030/)
![list of diffs page](docs/images/list-diffs-202010.png)

Note: If you see an error for any of the pages, your setup is not right. Please either check your local services, or rebuild the docker services if you are using that (including deleting the created volume). Check also the celery is running, which is needed for the asynchronous tasks.

# Change type inventory

This section provides a change type inventory along with the patterns captured by each change type. We model the change as state transition operator between old (on the left) and teh new (on the right). The transition operator is denoted by the arrow symbol (-->). On each sides of the transition operator, we use a compact notation following SPARQL triple patterns. 

We use a set of conventions for each variable in the triple pattern, ascribing meaning to each of them and a few additional notations. These conventions are presented in teh table below.

| Notation                   | Meaning                                                                                                                                                    | Example                 |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------|
| triple pattern < _s p o_ >   | each item in the triple represents a SPARQL variable or an URI. For brevity we omit the question mark prefix (?) otherwise the SPARQL reading shall apply. | i p v                   |
| arrow (_ --> _)              | state transition operator (from one version to the next)                                                                                                   | i1 p o  -->  i2 p o     |
| _i_ - in the triple pattern  | the instance subject (assuming class instantiation)                                                                                                        | i p v                   |
| _p_ - in the triple pattern  | the main predicate                                                                                                                                         | i p v                   |
| _op_ - in the triple pattern | the secondary predicate in a property chain (/)                                                                                                            | i p/op v                |
| _v_ - in the triple pattern  | the value of interest, which is object of the main or secondary predicate                                                                                  | i p v                   |
| _@l_ - in the triple pattern | the language tag of the value, if any                                                                                                                      | v@l                     |
| slash (_/_)                  | the property chaining operation.                                                                                                                           | p1/p2/p3/p4             |
| number (_#_)                 | the numeric suffixes help distinguish variables of teh same type                                                                                           | i1 p1 o1  -->  i2 p2 o2 |
| zero (_0_)                   | denotes "empty set" or "not applicable"                                                                                                                    | 0                       |


The table below presents the patterns of change likely to occur in the context of maintaining SKOS vocabularies, but the abstraction proposed here may be useful way beyond this use case. The table represents a power product between the four types of change relevant to the current diffing context and the possible triple patterns in which they can occur. Cells that are marked with zero (0) mean that no check shall be performed for such a change type as it is included in onw of its siblings. The last two columns indicate whether quantification assumptions apply on either side of the transition operator.  

| change type / pattern    | instance  | property value free  | property value language dependent | reified property value    | property value langauge dependent | reification object | Left condition checking | Right condition checking |
|---------------------------|-----------|----------------------|-----------------------------------|---------------------------|-----------------------------------|--------------------|-------------------------|--------------------------|
| Addition                  | 0  -->  i | 0  -->  i p v        | 0 --> i p v@l                                | 0  -->  i p/op v          | 0                                 | 0                  |                       0 | x                        |
| Deletion                  | i  -->  0 | i p v  -->  0        | i p v@l  -->  0                   | i p/op v  -->  0          |                                   | 0                  | x                       |                        0 |
| Value update              | 0         | i p v1  -->  i p v2  | i p v1@l  -->  i p v2@l           | i p/op v1  -->  i p/op v2 | i p/op v1@l  -->  i p/op v2@l     | 0                  | x                       | x                        |
| Movement (cross instance) | 0         | i1 p v  -->  i2 p v  | 0                                 | i1 p/op v  -->  i2 p/op v | 0                                 | 0                  | x                       | x                        |
| Movement (cross property) | 0         | i p1 v  -->  i p2 v  | 0                                 | i p1/op v  -->  i p2/op v | 0                                 | 0                  | x                       | x                        |

The state transition patterns presented in the table above can be translated to SPARQL queries. The last two columns, referring to the quantification assumptions, are useful precisely for this purpose indicating what filters shall be used in the SPARQL query.  


Before we introduce the quantification assumptions, we need to mention that the current diffing is performed by subtracting teh new version of the dataset from the old one resulting in the set of deletions between the two and, conversely, subtracting the old version of the dataset from the new one resulting in a set of insertions between the two. Therefore we conceptualise four content graphs: _OldVersion_, _NewVersion_, _Insertions_ and _Deletions_. Below is the table that summarises the quantification assumptions as conditions that apply to either left or right side of the transition operator and involve one of the four graphs introduced here.  


| Conditions on the left side of the transition operator                                                                                                                              | Conditions on the right side of the transition operator                                                                                                                            |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| does NOT exist in the Insertion graph 				| exists in the Insertion graph 	|
| does NOT exist in the NewVersion graph [redundant]	| exists in the NewVersion graph [redundant]		|
| exists in the Deletions graph						| does NOT exist in the Deletions graph [redundant]		|
| exists in the OldVersion graph [redundant] 			| does NOT exist in the OldVersion graph 	|


# Contributing
You are more than welcome to help expand and mature this project. We adhere to [Apache code of conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.   

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository before making a change.

----
_Made with love by [Meaningfy](https://meaningfy.ws)._
