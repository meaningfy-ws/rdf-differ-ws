#!/usr/bin/python3

"""RDF Differ — root package.

Project-wide configuration follows the Meaningfy settings pattern: related
settings are grouped into config classes whose env-backed members use the
``env_property`` decorator (the member name is the env-var name), and everything
is aggregated into a single ``RdfDifferConfigResolver`` instance exported as
``config``. Consumers do ``from rdf_differ import config`` and read
``config.RDF_DIFFER_<NAME>``.
"""

import json
import os
from pathlib import Path

import dotenv

from rdf_differ.core.adapters.config_resolver import env_property
from rdf_differ.core.domain import strtobool

dotenv.load_dotenv(verbose=True, override=os.environ.get("IS_PRIME_ENV") != "true")

REPO_ROOT = Path(__file__).parents[1]
TEMPLATES_FOLDER_PATH = REPO_ROOT / "resources" / "templates"
SPARQL_PREFIXES_PATH = REPO_ROOT / "resources" / "prefixes.json"


class FusekiConfig:
    @env_property(default_value="http://localhost")
    def RDF_DIFFER_FUSEKI_LOCATION(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="3030")
    def RDF_DIFFER_FUSEKI_PORT(self, config_value: str) -> int:
        return int(config_value)

    @env_property(default_value="admin")
    def RDF_DIFFER_FUSEKI_USERNAME(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="admin")
    def RDF_DIFFER_FUSEKI_PASSWORD(self, config_value: str) -> str:
        return config_value

    @property
    def RDF_DIFFER_FUSEKI_SERVICE(self) -> str:
        return f"{self.RDF_DIFFER_FUSEKI_LOCATION}:{self.RDF_DIFFER_FUSEKI_PORT}"


class ApiConfig:
    @env_property(default_value="http://localhost")
    def RDF_DIFFER_API_LOCATION(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="4030")
    def RDF_DIFFER_API_PORT(self, config_value: str) -> int:
        return int(config_value)

    @property
    def RDF_DIFFER_API_SERVICE(self) -> str:
        return f"{self.RDF_DIFFER_API_LOCATION}:{self.RDF_DIFFER_API_PORT}"

    @env_property(default_value="secret key api")
    def RDF_DIFFER_SECRET_KEY_API(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="true")
    def SHOW_SWAGGER_UI(self, config_value: str) -> bool:
        return strtobool(config_value)


class UiConfig:
    @env_property(default_value="8030")
    def RDF_DIFFER_UI_PORT(self, config_value: str) -> int:
        return int(config_value)

    @env_property(default_value="secret key ui")
    def RDF_DIFFER_SECRET_KEY_UI(self, config_value: str) -> str:
        return config_value


class RedisConfig:
    @env_property(default_value="redis://localhost")
    def RDF_DIFFER_REDIS_LOCATION(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="6379")
    def RDF_DIFFER_REDIS_PORT(self, config_value: str) -> int:
        return int(config_value)

    @property
    def RDF_DIFFER_REDIS_SERVICE(self) -> str:
        return f"{self.RDF_DIFFER_REDIS_LOCATION}:{self.RDF_DIFFER_REDIS_PORT}"


class StorageConfig:
    @env_property(default_value="file")
    def RDF_DIFFER_FILENAME(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="meta.json")
    def RDF_DIFFER_META_NAME(self, config_value: str) -> str:
        return config_value

    @property
    def RDF_DIFFER_FILE_DB(self) -> str:
        return os.environ.get("RDF_DIFFER_FILE_DB", str(REPO_ROOT / "db"))

    @property
    def RDF_DIFFER_REPORTS_DB(self) -> str:
        # NB: historical env-var name is RDF_DIFFER_REPORT_DB (singular).
        return os.environ.get("RDF_DIFFER_REPORT_DB", str(REPO_ROOT / "reports"))

    @property
    def APPLICATION_PROFILES_ROOT_FOLDER(self) -> str:
        location = os.environ.get("RDF_DIFFER_TEMPLATE_LOCATION")
        if location and Path(location).exists() and any(Path(location).iterdir()):
            return location
        return str(TEMPLATES_FOLDER_PATH)


class LoggingConfig:
    # Not env-driven: the gunicorn error logger is the project-wide logger.
    RDF_DIFFER_LOGGER = "gunicorn.error"

    @env_property(default_value="%d-%b-%YT%H:%M:%S")
    def RDF_DIFFER_TIME_FORMAT(self, config_value: str) -> str:
        return config_value

    @env_property(default_value="Europe/Paris")
    def RDF_DIFFER_TIMEZONE(self, config_value: str) -> str:
        return config_value


class SparqlConfig:
    @property
    def SPARQL_PREFIXES(self) -> dict[str, str]:
        """Namespace prefix → IRI bindings, managed centrally in prefixes.json."""
        data = json.loads(SPARQL_PREFIXES_PATH.read_text(encoding="utf-8"))
        return dict(data["prefix_definitions"])


class LoaderConfig:
    # Cutover flag: when true, the diff is created by the Python RDF Loading
    # Module instead of the legacy load_versions.sh subprocess.
    @env_property(default_value="false")
    def RDF_DIFFER_USE_PYTHON_LOADER(self, config_value: str) -> bool:
        return strtobool(config_value)


class RdfDifferConfigResolver(
    FusekiConfig,
    ApiConfig,
    UiConfig,
    RedisConfig,
    StorageConfig,
    LoggingConfig,
    SparqlConfig,
    LoaderConfig,
):
    """Aggregates every config group into the single project configuration."""


config = RdfDifferConfigResolver()
