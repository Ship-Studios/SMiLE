"""extract_called_capabilities: statically finds which registered
capabilities a script actually calls, without running it.

Used to cross-check the agent's stated `intent` against what the code
really does -- self-reported intent alone is exactly the kind of thing
this project doesn't trust blindly (see the output-budget design: an
oversized result gets a note, not a silent slice). AST-walking is cheap
and safe to run before the sandbox call, unlike executing the script
first to find out.
"""

from __future__ import annotations

import typing
from collections.abc import Mapping

from smile.server.called_names_in_code import called_names_in_code

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry


def extract_called_capabilities(
    code: str,
    registry: "CapabilityRegistry",
    saved_sources: Mapping[str, str] | None = None,
) -> list[str]:
    """Return the sorted, deduplicated names of registered capabilities
    (and saved scripts) that `code` calls, e.g. ["crm.get_customer",
    "list_orders", "scripts.paid_total"].

    Matches both flat calls (`list_orders(...)`) and namespaced calls
    (`crm.get_customer(...)`, `scripts.paid_total(...)`) against
    `registry`'s known exposed names plus the keys of `saved_sources`.
    Only call *sites* are considered -- a capability merely referenced
    without being called (e.g. passed as a value) is not counted, since
    what matters here is what the script actually did.

    Saved-script calls are expanded transitively: if the script calls
    `scripts.paid_total` and that function's source calls `list_orders`,
    both names appear. The walk is cycle-safe so mutually recursive
    saved scripts cannot loop the extractor.

    Returns an empty list rather than raising on unparseable code --
    execute_script's own error path (via run_script) is the place a
    syntax error gets reported to the agent, not this helper.
    """
    sources = dict(saved_sources or {})
    known = registry.capability_names() | frozenset(sources)

    seen: set[str] = set()
    stack = list(called_names_in_code(code, known))
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in sources:
            stack.extend(called_names_in_code(sources[name], known))

    return sorted(seen)
