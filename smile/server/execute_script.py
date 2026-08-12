"""execute_script MCP tool."""

from __future__ import annotations

from smile.sandbox import run_script
from smile.server.mcp_instance import mcp
from smile.server.registry_instance import registry


@mcp.tool()
def execute_script(code: str) -> dict:
    """Execute a Python script in a sandboxed environment.

    The functions listed by list_capabilities() are available directly
    in the global namespace -- call them like local functions, no
    imports or client setup needed. Standard control flow (loops,
    conditionals, comprehensions, exception handling) all work normally.

    To return a value from the script, assign it to a variable named
    __result__ at any point in your script. Whatever __result__ holds at
    the end of execution is returned as `return_value`. If you never set
    it, `return_value` is null and only stdout/stderr are returned.

    The sandbox has no filesystem or network access beyond the injected
    functions, and no import statement is available -- only the
    capabilities listed by list_capabilities() and a restricted set of
    Python builtins.

    Example:
        enterprise = list_customers(tier="enterprise")
        results = []
        for c in enterprise:
            orders = list_orders(c["id"], status="paid")
            total = sum(o["amount"] for o in orders)
            results.append({"customer": c["name"], "total_paid": total})
        __result__ = results
    """
    result = run_script(code, registry.namespace())
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_value": result.return_value,
        "error": result.error,
        "timed_out": result.timed_out,
    }
