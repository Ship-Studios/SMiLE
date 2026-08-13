"""build_execute_script_description: renders the tool description an agent
reads before writing a script, against the registry actually being served.

The description is generated rather than hardcoded because the served
capability set is configurable (see load_registry.py: SMILE_CAPABILITIES /
SMILE_CAPABILITY_SPEC). A static docstring can only name one capability
set -- the bundled demo one -- so any consumer supplying their own would
ship an agent-facing example calling functions that don't exist for them.
Rendering registry.stub_file() here is what makes the documented promise
("the capability catalog is pushed into the tool description") true for
every consumer, not just the demo.
"""

from __future__ import annotations

import typing

from smile.server.render_worked_example import render_worked_example

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry

_PREAMBLE = """Execute a Python script in a sandboxed environment.

The functions listed below (and by list_capabilities()) are available
directly in the global namespace -- call them like local functions, no
imports or client setup needed. Standard control flow (loops,
conditionals, comprehensions, exception handling) all work normally.

To return a value from the script, assign it to a variable named
__result__ at any point in your script. Whatever __result__ holds at the
end of execution is returned as `return_value`. If you never set it,
`return_value` is null and only stdout/stderr are returned.

The sandbox has no filesystem or network access beyond the injected
functions, and no import statement is available -- only the capabilities
below and a restricted set of Python builtins.

AGGREGATE INSIDE THE SCRIPT. The whole point of this tool is that the
script runs next to the data and only the answer travels back. Assign a
summary to __result__ -- a count, a total, a filtered shortlist -- not a
raw dump of everything you fetched. Do the sum(), len(), max(), sorting
and filtering in the script.

Returning a large collection is a bug, not a fallback: results over a
size limit are NOT returned in full. You get a small sample plus a note
saying how many items were omitted, and a `full_result_uri` you can read
as an MCP resource if you truly need every row. Never infer a count or a
total from a truncated sample -- it is a preview, not the data. Re-run
with the aggregation done in the script instead.

    # Wrong -- ships 10,000 rows back just to count them:
    __result__ = list_orders(customer_id)

    # Right -- ships one number:
    __result__ = len(list_orders(customer_id))

The same applies to print(): stdout is capped too, so avoid printing
inside loops. Use it for a few lines of diagnostics, not as the result
channel.
"""

_EXAMPLE = """
Example of the shape a script should take (using this server's own
capabilities):

{example}
"""


def build_execute_script_description(registry: "CapabilityRegistry") -> str:
    """Build execute_script's tool description from `registry`."""
    sections = [_PREAMBLE, "Available capabilities:", "", registry.stub_file()]

    example = render_worked_example(registry)
    if example:
        sections.append(_EXAMPLE.format(example=example))

    return "\n".join(sections).rstrip() + "\n"
