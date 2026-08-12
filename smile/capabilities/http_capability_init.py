"""_HttpCapability.__init__ implementation. Attached to the
_HttpCapability class in http_capability.py."""

from __future__ import annotations

import re
import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.http_capability import _HttpCapability


def http_capability_init(
    self: "_HttpCapability",
    *,
    name: str,
    description: str,
    method: str,
    url_template: str,
    headers: dict[str, str],
    timeout_s: float,
) -> None:
    self.__name__ = name
    self.__doc__ = description
    self._method = method
    self._url_template = url_template
    self._headers = headers
    self._timeout_s = timeout_s
    self._template_params = set(re.findall(r"\{(\w+)\}", url_template))
