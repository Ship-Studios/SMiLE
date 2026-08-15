"""build_execute_script_description: renders the tool description an agent
reads before writing a script, against the registry actually being served.

The description is generated rather than hardcoded because the served
capability set is configurable (see load_registry.py: SMILE_CAPABILITIES /
SMILE_CAPABILITY_SPEC). A static docstring can only name one capability
set, so any consumer supplying their own would ship an agent-facing
example calling functions that don't exist for them.
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

Every call also requires `intent`: one plain-English sentence stating
what the script is meant to accomplish, written before you write the
code -- e.g. "Find the most recent change that mentions the sandbox
timeout." State the goal, not a restatement of the code ("call X then
Y" isn't an intent). This is logged alongside which capabilities the
script actually calls, so keep it accurate -- it's the record of what
you meant to do, checked against what the code did.

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
    __result__ = rows

    # Right -- ships one number:
    __result__ = len(rows)

The same applies to print(): stdout is capped too, so avoid printing
inside loops. Use it for a few lines of diagnostics, not as the result
channel.

Reusable scripts. A script that defines exactly one top-level function
and assigns `__save__ = True` (or `__save__ = "name"`) publishes that
function as `scripts.<name>` for later execute_script calls in this
session (and across restarts if SMILE_SCRIPTS_DIR is set). The function
needs type hints on every parameter and the return value, and a
docstring (the first paragraph becomes its description). Overwriting a
name replaces the previous function. `__unpublish__ = "name"` removes
one. Call list_capabilities() to see saved scripts -- they are not
listed in this description, because it is generated once at startup.

    def doubled(n: int) -> int:
        \"\"\"Double a number.\"\"\"
        return n * 2

    __save__ = True
    __result__ = doubled(3)

Later scripts call it as scripts.doubled(3). Saved functions may call
other saved functions the same way (and may call capabilities).
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
