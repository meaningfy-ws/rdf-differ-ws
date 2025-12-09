# RDF Differ

RDF Differ is a schema-aware diff reporting tool for RDF vocabularies, designed to track and report meaingful changes—beyond the line- or word-based change detection of contemporary diff tools. RDF Differ helps you surface changes that impact interoperability, governance, and collaborative curation when developing and maintaining SKOS taxonomies or lightweight ontologies.

With application profile (AP) templates that can be reused, extended or created anew, RDF Differ provides:

- 🧠 **Semantic Change Detection:** SPARQL-based diffing technique inspired by [skos-history](https://github.com/jneubert/skos-history)
- 🧰 **Templated Reporting:** HTML/JSON report generation with the SPARQL-enabled [eds4jinja2](https://github.com/meaningfy-ws/eds4jinja2) Jinja extension
- 🎛️ **Configurable Templates:** Customizable AP templates and fully automated query generation using [diff-query-generator](https://github.com/meaningfy-ws/diff-query-generator) (dqgen)
- 🌐 **ReST API, GUI & CLI:** A fully qualified web service (WS) offering a web API and UI, plus a CLI wrapper script

RDF Differ comprises a set of tools that collectively follow a pipeline architecture:

![The RDF Differ Pipeline](docs/images/rdf-differ-pipeline.png)

But you needn't worry about all of that, so here's what a report looks like (for you to decide if it's worth moving on to the usage and installation instructions):

![An RDF Differ Report](docs/images/rdf-differ-report-example.png)

RDF Differ is modular, extensible, and built to bridge the gap between basic RDF comparison tools and heavyweight OWL diffing frameworks. If you need a _semantic_ RDF diff tool with a reporting feature that's as simple as possible, but not simpler, then look no more. <!-- We've even made it onto Copilot: -->

<!-- ![MS Copilot on RDF Diff Tools](docs/images/rdf-differ-copilot-answer.png) -->

## Overview

RDF Differ can be used via a ReST API, web UI, or command-line interface (CLI). The API and UI can be run locally or via Docker containers, while the CLI scripts can interact with any running instance of the API.

The key concepts to be aware of when using RDF Differ are:

- **Diff:** The process of comparing two RDF datasets (old vs. new) to identify changes. But in the tool's context, "creating a diff" simply means loading both datasets into the triplestore and preparing them for change detection.
- **Report:** A structured summary of the identified changes, generated based on a specified application profile (AP) and template format (e.g. HTML). One can produce different reports from the same diff by varying the AP and template.
- **Application Profile (AP):** A predefined set of SPARQL queries and templates that define how to detect and report changes for specific RDF vocabularies or use cases.

### Change Types

The currently detected change types are:

- Added resource
- Deleted resource
- Updated (property value change)
- Moved (property with value moved from one resource to another)
- Changed (value moved from one property to another within the same resource)

The _updated_, _moved_ and _changed_ types are essentially details about "modified resources", but they are reported separately to provide more granular insights into the nature of the changes. Therefore, modifications are currently not reported for the resource as a whole (with statistics), but rather for each property that has changed.

For the theory and a more technical description of the change types, see the README at [dqgen](https://github.com/meaningfy-ws/diff-query-generator/), or read our [SEMANTiCS '25 paper](https://ceur-ws.org/Vol-4064/PD-paper9.pdf).

> The term "resource" and "instance" are used interchangeably in the rdf-differ suite of tools to refer to the RDF subjects of change detection, i.e. in the case of an OWL ontology, the entities with T-Box declarations of `a owl:Class`, `a owl:DatatypeProperty` or `a owl:ObjectProperty`. Not to be confused with instance in the OWL A-Box sense (i.e. "individuals" of the aforementioned).

### Application Profiles and Report Templates

RDF Differ uses application profiles (APs) to define how to detect and report changes for specific RDF vocabularies or use cases. Each AP consists of a set of SPARQL queries and templates that are used to generate the diff reports. The AP itself has its own template structure, which is defined in [dqgen](https://github.com/meaningfy-ws/diff-query-generator/blob/main/dqgen/resources/aps/).

The currently suppported APs are:

- [owl-core](https://github.com/meaningfy-ws/diff-query-generator/blob/main/dqgen/resources/aps/owl-core.csv)-en-only: For OWL ontologies with English labels
- [shacl-core](https://github.com/meaningfy-ws/diff-query-generator/blob/main/dqgen/resources/aps/shacl-core.csv)-en-only: For SHACL shapes with English labels
- [skos-core](https://github.com/meaningfy-ws/diff-query-generator/blob/main/dqgen/resources/aps/skos-core.csv)-en-only: For SKOS vocabularies with English labels

The language for labels matter for display purposes only. If you have another language, you will just miss the human-readable labels in the report, but the diffing will still work.

The currently supported report templates are:

- `JSON`: A machine-readable format (based on [SPARQL Query Results JSON Format](https://www.w3.org/TR/sparql12-results-json/))
- `HTML`: The world's standard Web markup format (styled with CSS and interactive JavaScript tables)
- `AsciiDoc`: A human-readable plain-text markup format (opens various conversion possibilities including HTML)

All AP templates can be edited or extended, and new ones can be created as needed. See the section on [Customizing RDF Differ](#customizing-rdf-differ) for more details. For modifications beyond a few lines or files, we recommend updating the existing meta-templates or introducing new ones in [dqgen](https://github.com/meaningfy-ws/diff-query-generator/tree/main/dqgen/resources), which is used to generate the queries and templates for RDF Differ, aside from defining the AP itself (in [CSV files](https://github.com/meaningfy-ws/diff-query-generator/tree/main/dqgen/resources/aps)).

### Embedded SHACL in OWL TTL files

There is special support in RDF Differ for handling OWL files (in RDF format, Turtle syntax) that have embedded SHACL shapes. This is to facilitate the retrieval of certain advanced information from the SHACL shapes, such as property domains, ranges and cardinalities, mainly for _added instances of properties_. This would otherwise not be doable with the current OWL-core profile, which is geared towards _lightweight_ ontologies that typically do not involve such expressions, or are not consistent in how they do so (whereas SHACL has a consistent pattern for these).

The following information is currently retrieved when reporting added instances of properties:

- Property domain(s) via `sh:targetClass`, represented as `domain` in the report
- Property range(s) via `sh:datatype`, `sh:class` and `sh:node/sh:property/sh:hasValue`, represented as `range` in the report
- Property cardinality constraints (min/max) via `sh:minCount` and `sh:maxCount`, represented as `minCardinality` and `maxCardinality` in the report

To reiterate, this information is only _retrieved_, i.e. there is no support for change detection of these properties or the constraints themselves. The purpose is to enrich the report with additional context about the added resources.

> **NOTE:** This is supported for only Turtle syntax files (`.ttl` extension) at the moment. If you have another format, use a tool like [riot](https://jena.apache.org/documentation/tools/#riot-and-related) to convert it to Turtle first.

## Installation

> The specified installation instructions are for personal deployment purposes only on a *NIX operating system. _(Slight modifications are required for production use, including having production-level Fuseki and Redis servers available.)_

RDF Differ uses Fuseki (as the triplestore/database), Celery (for multithreading programming), Gunicorn (for serving), and Redis (for queue-based pesistent storage). For the corresponding Docker micro-services, it uses Traefik for the networking, _except when running tests_.

The applications are made available (by default) on ports [8030](http:localhost:8030) (ui), [4030](http:localhost:4030) (API; [4030/ui](http:localhost:4030/ui) for Swagger), [3030](http:localhost:3030) (triplestore), [6379](http:localhost:6379) (Redis), and [5555](http:localhost:5555) (Celery). This is configurable via `bash/.env` and `docker/.env`.

> For the docker services with Traefik, you have to access these differently, through their local domains instead, for e.g. <https://rdf.localhost/> (ui). See <https://monitor.localhost> > Routers > Explore (`Host(...)`).
>
> On Windows/WSL2 with Traefik, `curl` works only _outside_ WSL without SSL/TLS, e.g. via Git Bash `curl https://api.localhost/diffs --insecure`.

For all output except Fuseki, see the `logs` folder, e.g. `tail -f logs/api.log` to follow the API output. For Fuseki, run `docker logs fuseki` (add `-f` to follow).

> For the docker services with Traefik, you have to get to the logs from inside the container, for example, via `docker exec -it rdf-differ-api-dev tail -f logs/api.log` where `rdf-differ-api-dev` is the name of the API container (see `docker ps`).

### OS Prerequisites

For Red Hat derivative systems, make sure that the EPEL (Extra Packages for Enterprise Linux) repository is enabled and added to the server's package lists. This is not currently handled automatically and can usually be installed by running:

```bash
sudo yum install epel-release
```

For Debian derivative systems, no additional package repository should be needed, for at least Ubuntu 18.04. While we do not test for Windows/WSL2
or Mac (because of some limitations with GitHub CI), those platforms should work as well. Even Windows 10/11 alone should work as long as you don't use Make but Python and Docker commands directly, as the Makefile contains ASCII escape sequencies and *NIX commands which PowerShell cannot interpret.

#### Optional dependencies

If you would like to run the `bash/merge-owl-shacl.sh` script for merging OWL and SHACL files to report embedded constraint information, you need to have Apache Jena's `riot` command-line tool installed.

Download [Jena](https://jena.apache.org/download/) to get access to its CLI tools (you will want to [put them in your `PATH`](https://jena.apache.org/documentation/tools/#common-issues-with-running-the-tools) to be able to run them as commands). If you are looking to integrate this into your GitHub CI/CD pipelines, you can also use a [third-party GitHub Action](https://github.com/marketplace/actions/setup-apache-jena).

### Installation with Docker (recommended)

Run the following command to install all required dependencies on either a
Debian, Red Hat or compatible WSL system, start up required (Docker) services
-- including databases -- and run the application (API + UI):

```bash
make
```

By default, that runs the first build target, currently `make start`. You must
have `docker` and `docker-compose` installed if you would like to use the
micro-services to run everything, everywhere, all at once.

This creates the required local Docker images (and fetches some third-party ones from DockerHub), prerequisite volumes (for file storage in the containers), and finally runs all the containers.

To stop ALL docker services at any time:

```bash
make stop
```

> If at any time you think you are experiencing odd behaviour, such as a `500 Internal Server Error` or `404 Not Found`, use your preferred method to completely remove (purge) the docker containers, images and volumes related to this project, files inside `db`, `reports`, `fuseki-data` and `logs` (sometimes file permissions can differ when switching between normal and testing environments and this can prevent startup), and redo everything.
>
> **WARNING:** Do not create files or folders under `db` or `reports` yourself. The tests use these folders and there are certain assumptions the code makes about their structure, which your file or folder may not comply with.

### With local and system services

If you are running the project for the first time this would be the commands to run in sequence:

```bash
make install-os-dependencies
make install-python-dependencies
make run-system-redis
make run-local-api
make run-local-ui
make setup-local-fuseki # skip if you manage Fuseki
```

If you use the local Fuseki instance, in a separate terminal process remember
to run and keep open:

```bash
make run-local-fuseki
```

In this case be careful that you don't already have a Fuseki instance running
from other projects, especially with Docker, as the ports may conflict. Look
for port `3030`. If you do, you probably fall in the "you manage Fuseki"
category and probably can reuse the preexisting triplestore.

#### Prerequisites

To install prerequisite operating system (OS) software and dependencies, run:

```bash
make install # add -dev if you want to run tests
```

**WARNING:** Some commands are **run as root** with _sudo_.

If you install OS packages yourself (if in case you run an unsupported OS or
you don't want to run as root), run:

```bash
make install-python-dependencies # add -dev if you want to run tests
```

#### Fuseki

To run the triplestore database (Fuseki) server locally and not via Docker (on
first setup accept the default values):

```bash
make setup-local-fuseki
make run-local-fuseki
```

_leave this terminal session open._

That will fetch, install in and run Fuseki from the current working directory,
which can be run as a user _without requiring root_.

You can also choose to only run Fuseki with Docker, reusing the service used for tests:

```sh
make run-docker-fuseki-test
```

Alternatively, if you have a separately managed installation of Fuseki, you can
ignore this step. Simply ensure it is available at `localhost:3030`, or a
location/port as defined in `bash/.env`.

#### Redis

To set up and run a _system_ Redis server which _does_ need to be **run as root**:

```bash
make run-system-redis
```

**WARNING:** This runs as root and replaces a system configuration file. If you
get errors about configuration directives, you are likely running an older OS
with older Redis (e.g. Ubuntu 18.04 does not have the Redis version that's
required).

There is currently no local alternative to this to run as a user. If that is a concern, you can also choose to run Redis test service with Docker:

```sh
make run-docker-redis-test
```

#### Application

To run the API (including Celery) locally:

```bash
make run-local-api
```

To run the UI locally:

```bash
make run-local-ui
```

To stop both API and UI servers (leaving only Fuseki and the system Redis running, which you must control on your own):

```bash
make stop-local-applications
```

## Usage

### The Differ CLI

For users who would rather not deal with the web UI, RDF Differ offers an HTTP ReST API. However, the API is _asynchronous_, meaning that calls are processed in the background, and one needs to _poll_ for the status of diff creation and report generation.

It is for this reason that we provide `bash/rdf-differ.sh`, a CLI helper script with a rudimentary but sufficient polling mechanism, to make it easier to use the tool from the command line. The script wraps common API call sequences for creating diffs and generating reports, with parameters for the AP and report template.

The supported AP values are:

- `owl-core-en-only`
- `shacl-core-en-only`
- `skos-core-en-only`

And the supported template format values are:

- `json`
- `html`
- `asciidoc`

In adddition, there is the `bash/merge-owl-shacl.sh` script that can be used to merge an OWL file and a SHACL file into a single OWL file. Merge both old and new files before passing the new "combined" file to the tool for diffing, and to report advanced constraint information from the embedded SHACL shapes.

#### Examples

Full workflow (diff + report using default OWL AP in default JSON format)

```sh
./bash/rdf-differ.sh --old <first-file> --new <second-file>
```

Create a diff only (this is useful to reuse the ID to generate reports in different templates/formats)

```sh
./bash/rdf-differ.sh diff --old <first-file> --new <second-file>
```

Generate report for an existing diff (using default OWL AP in default JSON format)

```sh
./bash/rdf-differ.sh report --dataset-id <diff-uid>
```

Custom configuration

```sh
./bash/rdf-differ.sh \
  --base-url http://<host>:<port> \
  --old <old-file> \
  --new <new-file> \
  --ap <desired-profile> \
  --template <desired-template> \
  --output custom-dir \
  full
```

Merge an OWL and SHACL file into a combined OWL file with embedded SHACL shapes:

```sh
./bash/merge-owl-shacl.sh [input-owl-file] [input-shacl-file] <output-combined-file>
```

Notes:

- When running tests via `make test` the API is available at `http://localhost:4030` (no Traefik). The pytest integration uses the `RDF_DIFFER_BASE_URL` environment variable (defaulting to `http://localhost:4030`).
- The script accepts both `--ap` and `--profile` for the application profile. The `--template` value controls the report output format (e.g. `json` or `html`).
- By default the script writes reports to `diff-output/` or to the directory passed with `--output`.
- The report file is saved as `diff.<template>`, e.g. `diff.json` or `diff.html`. This is _not_ configurable at the moment.

#### Demo using sample data

- Create a diff and generate a HTML report saved in `diff-output/` (full workflow):

```bash
./bash/rdf-differ.sh --old tests/test_data/owl/ePO_sample-4.0.0.orig.ttl \
                     --new tests/test_data/owl/ePO_sample-4.0.0.upd.ttl \
                     --profile owl-core-en-only --template HTML
```

- Create only the diff (prints `dataset_name` and `uid`, the latter of which is needed for report generation):

```bash
./bash/rdf-differ.sh diff --old tests/test_data/owl/ePO_sample-4.0.0.orig.ttl \
                          --new tests/test_data/owl/ePO_sample-4.0.0.upd.ttl
```

- Request a report for an existing dataset ID (`uid`), and use a different base URL:

```bash
./bash/rdf-differ.sh report --dataset-id 64000b53-61ac-4b34-8abd-5f77a4cfa453 report --base-url http://localhost:4030
```

- List existing diffs (GET `/diffs`):

```bash
./bash/rdf-differ.sh list
```

- Merge the OWL and SHACL artefacts of an actual lightweight ontology (ePO):

```sh
./bash/merge-owl-shacl.sh \
  evaluation/vocabularies/ePO_core-4.2.0.ttl \
  evaluation/vocabularies/ePO_core_shapes-4.2.0.ttl \
  evaluation/vocabularies/ePO_core_combined-4.2.0.ttl
```

#### API endpoint configuration

If you have a different setup, say some Docker services and some local services, check if the API itself is available at localhost:

```sh
curl localhost:4030/diffs
```

If so, you will need to override the base URL inclusive of the port:

```sh
./bash/rdf-differ.sh --old <first-file> --new <second-file> --base-url localhost:4030
```

In the development/production environment where services are running behind Traefik, no such override is required, as the default base URL for the script is `api.localhost`, the Traefik route for the API+port.

### The Differ UI

To create a new diff, click on **Create diff** and fill in all of the metadata fields along with uploading the old and new RDF files to diff.

![Create diff page](docs/images/create-diff.png)

To list existing diffs, click on **List diffs** and select a diff to view its details and generate reports.

![List diffs page](docs/images/list-diffs.png)

To create reports, select an AP and report format from the two dropdowns, and then click on **Build report**.

![Create reports page](docs/images/create-reports.png)

To see running processes for diff creation and report generation, click on **List active tasks**.

![Create reports page](docs/images/list-tasks.png)

Depending on the size of your data and number of items in your AP, this may take a while (a few mins for 500KB, considered relatively large for text files). You may refresh the page to see if the report is ready.

Once ready (the task has disappeared), navigate back to the diff, and a new section for the selected AP with a download link will have now appeared.

![Download reports page](docs/images/download-reports.png)

> **Note:** If you see an error for any of the pages, your setup is not right. Please either check your local services, or rebuild the Docker services if you are using that (including deleting the associated volumes). Check also that Celery is running, which is needed for the asynchronous tasks.

### The Differ API

Using the API directly is not expected to be a common use case. For advanced users or developers intending to integrate the differ, [this file](curl-examples.md) contains a list of examples on how to use the API. You will have to translate the URLs accordingly for Traefik domains as mentioned in the [installation instructions](#installation).

## Testing

The test suite requires preexisting services _without_ Traefik, where access to
those specific services are directly through the localhost and respective
ports. These services can also be spun up with Docker, creating
development-specific containers. Run the following to start everything and also
remove the testing containers at the end:

```bash
make ENVIRONMENT=test start-services-test # run separately to avoid race conditions
make ENVIRONMENT=test test teardown-services
```

This creates the `subdiv` and `abc` dummy datasets once in a new Fuseki
container, and a `dataset{ID}` dataset (where `{ID}` is a short random ID) as
many times as the tests are run. The `db` folder is populated by the tests and
it is _not_ removed automatically. Omit `teardown-services` if you want to
inspect the test containers for any reason after the tests complete.

However, if you already had non-development containers running, for e.g. by
following our setup instructions and using the single `make` command, then
there will be conflicting ports for Fuseki. In such a case, you might want to
stop those containers temporarily, either through your Docker interface of
choice (like Docker Desktop or Podman), or with `make stop`, and then run the
tests.

Alternatively, if you had used a mixed setup, where you had used only some
Docker services like Fuseki, or already have a system Fuseki you manage and
control yourself, and/or are running a local API (not using Docker), you can
also run the tests directly in your Python environment bypassing Make:

```sh
pytest
```

That simply relies on being able to create and query a Fuseki service, usually
at `localhost:3030`.

> **Note:** Overriding `RDF_DIFFER_FUSEKI_PORT` currently does _not_ help with
having two running instances of Fuseki for this project (dev and non-dev) --
you need to stop one to run the other.

## Customizing RDF Differ

One can customize the existing application profiles (APs) and report templates, or create new ones as needed. For customizing templates, see [docs/customize-templates](docs/customization/customize-templates.md).

While it is possible to customize the APs by modifying the queries, this is going to become very unwieldy once you realize there are as many queries to write or update, as there are change types and the number of resource types in your vocabulary. For this reason, while more straightfoward, customizing the report templates also becomes unmanageable once you go beyond a few lines.

It is therefore recommended to customize the source meta-templates or define new ones through [dqgen](https://github.com/meaningfy-ws/diff-query-generator/), after which you can generate and copy over the templates with simple `make` commands.

## Contributing

You are more than welcome to help expand and mature this project. We adhere to the [Apache Code of Conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.

When contributing to this repository, you are welcome to fork and make a pull request, or discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository.

----
_Made with love by [Meaningfy](https://meaningfy.ws)._
