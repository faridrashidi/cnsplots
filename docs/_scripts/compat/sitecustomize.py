"""Compatibility patches for versioned docs subprocesses."""

from __future__ import annotations

import inspect

from sphinx.config import Config
from sphinx.util.tags import Tags

_config_read = Config.read.__func__
_signature = inspect.signature(_config_read)


def _needs_keyword_compatibility() -> bool:
    parameter = _signature.parameters.get("overrides")
    return parameter is not None and parameter.kind is inspect.Parameter.KEYWORD_ONLY


if _needs_keyword_compatibility():

    def _compat_read(cls, confdir, overrides=None, tags=None, **kwargs):
        if overrides is None:
            overrides = kwargs.pop("overrides", {})
        if tags is None:
            tags = kwargs.pop("tags", None)
        if tags is None:
            tags = Tags()
        return _config_read(cls, confdir, overrides=overrides, tags=tags)

    Config.read = classmethod(_compat_read)
