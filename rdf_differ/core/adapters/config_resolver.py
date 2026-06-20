"""Configuration resolution (Meaningfy canonical settings pattern).

A pluggable mechanism for resolving configuration values from a named source. The
``env_property`` decorator turns a method into a ``@property`` whose value is
resolved by name (the method's own name) through a ``ConfigResolverABC``; the
method then casts/normalises the resolved string. Config classes group related
settings and are aggregated into one resolver instantiated in the root package
``__init__`` (see ``rdf_differ.config``).

This resolver lives in ``core/adapters`` (it performs environment I/O); the
accepted DIP nuance is that config classes consume it from the root package.
"""

import inspect
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class ConfigResolverABC(ABC):
    """Abstraction for resolving a configuration value by name from some source."""

    def config_resolve(self, default_value: str | None = None) -> str | None:
        """Resolve the configuration named after the *calling* method."""
        config_name = inspect.stack()[1][3]
        return self.concrete_config_resolve(config_name, default_value)

    @abstractmethod
    def concrete_config_resolve(
        self, config_name: str, default_value: str | None = None
    ) -> str | None:
        """Resolve ``config_name`` from the concrete source, or ``default_value``."""
        raise NotImplementedError


class EnvConfigResolver(ConfigResolverABC):
    """Resolve configurations from environment variables."""

    def concrete_config_resolve(
        self, config_name: str, default_value: str | None = None
    ) -> str | None:
        value = os.environ.get(config_name, default=default_value)
        logger.debug("[ENV] %s = %r (default %r)", config_name, value, default_value)
        return value


def env_property(
    config_resolver_class: type[ConfigResolverABC] = EnvConfigResolver,
    default_value: str | None = None,
) -> Callable[[Callable[..., Any]], property]:
    """Decorate a method as a config-resolving ``@property``.

    The configuration name is the method's own name; the resolved (string) value
    is passed to the method as ``config_value`` so it can cast/normalise it.
    """

    def wrap(func: Callable[..., Any]) -> property:
        def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
            config_value = config_resolver_class().concrete_config_resolve(
                config_name=func.__name__, default_value=default_value
            )
            return func(self, config_value, *args, **kwargs)

        return property(wrapped)

    return wrap
