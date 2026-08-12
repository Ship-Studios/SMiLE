"""_HttpCapability.__call__ implementation. Attached to the
_HttpCapability class in http_capability.py."""

from __future__ import annotations

import json
import typing
from typing import Any

if typing.TYPE_CHECKING:
    from smile.capabilities.http_capability import _HttpCapability


def http_capability_call(self: "_HttpCapability", **kwargs: Any) -> Any:
    import urllib.parse
    import urllib.request

    url = self._url_template.format(**{k: kwargs[k] for k in self._template_params})
    body_params = {k: v for k, v in kwargs.items() if k not in self._template_params}

    req_headers = dict(self._headers)
    data = None
    if self._method in ("GET", "DELETE"):
        if body_params:
            url += "?" + urllib.parse.urlencode(body_params)
    else:
        data = json.dumps(body_params).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(url, data=data, headers=req_headers, method=self._method)
    with urllib.request.urlopen(request, timeout=self._timeout_s) as resp:
        raw = resp.read().decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw
