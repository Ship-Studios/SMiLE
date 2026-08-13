"""
Tests for the capability-registration paths in smile/capabilities.py:

  1. @registry.register with docstring inference
  2. registry.register_module (auto-wrap an existing module)
  3. registry.register_class (auto-wrap an existing client instance)
  4. registry.register_spec / load_specs (declarative JSON/YAML)
  5. @capability marker + registry.collect() (registry-free registration)

Plus the SDK ergonomics additions: early picklability checks, async
capability support, and Annotated[...] per-parameter descriptions.

Run with: uv run python3 tests/test_capabilities.py
Not using pytest here to keep the prototype dependency-light -- these are
plain assert-based checks with a runner at the bottom.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).parent))  # for `fixtures.*` imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # for `smile.*` imports

from smile.capabilities import (
    CapabilityDefinitionError,
    CapabilityRegistry,
    CapabilitySpec,
    capability,
)
from smile.sandbox import run_script

_failures: list[str] = []


def check(condition: bool, label: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


# --------------------------------------------------------------------------
# 1. Decorator + docstring inference
#
# Capabilities registered via @registry.register must be module-level
# functions, not closures nested inside a test function -- the sandbox
# pickles every registered callable across a process boundary, and a
# CapabilityRegistry.collect() validate_picklable check now rejects
# closures at registration time (see test_picklability_check below). So
# every capability used in these tests is defined at module scope.
# --------------------------------------------------------------------------


def _get_widget(widget_id: str) -> dict:
    """Fetch a widget by ID.

    >>> _get_widget("w1")
    """
    return {"id": widget_id}


def test_decorator_inference() -> None:
    registry = CapabilityRegistry()
    registry.register(_get_widget, name="get_widget")

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check("get_widget" in caps, "decorator: function registered")
    check(
        caps["get_widget"]["description"] == "Fetch a widget by ID.",
        "decorator: description inferred from docstring summary",
    )
    check(
        caps["get_widget"]["example"] == 'get_widget("w1")',
        "decorator: example inferred from doctest line",
    )
    check(
        caps["get_widget"]["signature"] == "def get_widget(widget_id: str) -> dict: ...",
        "decorator: stub signature renders correctly",
    )


def _no_example(x: int, y: int = 0) -> int:
    """Add two things, no example given."""
    return x + y


def test_decorator_synthesized_example() -> None:
    registry = CapabilityRegistry()
    registry.register(_no_example)

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check(
        caps["_no_example"]["example"] == "_no_example(x=...)",
        "decorator: example synthesized from signature when docstring has none "
        f"(got {caps['_no_example']['example']!r})",
    )


def _explicit_example() -> None:
    """This docstring should be ignored in favor of the explicit args."""
    return None


def test_decorator_explicit_overrides_still_work() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _explicit_example,
        description="Explicit description.",
        example="explicit_example()",
    )

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check(
        caps["_explicit_example"]["description"] == "Explicit description.",
        "decorator: explicit description= overrides docstring inference",
    )
    check(
        caps["_explicit_example"]["example"] == "explicit_example()",
        "decorator: explicit example= overrides docstring inference",
    )


def _missing_param_hint(x) -> int:
    """Missing a param hint."""
    return x


def test_validation_missing_param_hint() -> None:
    registry = CapabilityRegistry()
    try:
        registry.register(_missing_param_hint)
        check(False, "validation: missing param hint should raise")
    except CapabilityDefinitionError as exc:
        check("missing type hints" in str(exc), "validation: missing param hint raises with clear message")


def _missing_return_hint(x: int):
    """Missing a return hint."""
    return x


def test_validation_missing_return_hint() -> None:
    registry = CapabilityRegistry()
    try:
        registry.register(_missing_return_hint)
        check(False, "validation: missing return hint should raise")
    except CapabilityDefinitionError as exc:
        check("return type hint" in str(exc), "validation: missing return hint raises with clear message")


def _missing_description(x: int) -> int:
    return x


def test_validation_no_description() -> None:
    registry = CapabilityRegistry()
    try:
        registry.register(_missing_description)
        check(False, "validation: missing description should raise")
    except CapabilityDefinitionError as exc:
        check(
            "no description" in str(exc),
            "validation: missing description raises with clear message",
        )


def _dup(x: int) -> int:
    return x


def test_validation_duplicate_name() -> None:
    registry = CapabilityRegistry()
    registry.register(_dup, name="dup", description="first")

    try:
        registry.register(_dup, name="dup", description="second")
        check(False, "validation: duplicate name should raise")
    except CapabilityDefinitionError as exc:
        check("already registered" in str(exc), "validation: duplicate name raises with clear message")


# --------------------------------------------------------------------------
# 2. register_module
# --------------------------------------------------------------------------


def test_register_module() -> None:
    import fixtures.sample_module as sample_module  # type: ignore

    registry = CapabilityRegistry()
    report = registry.register_module(sample_module)

    check(
        set(report.registered) == {"add_numbers", "greet", "lookup_product"},
        f"register_module: registers public typed functions only (got {report.registered})",
    )
    check(
        any(name == "untyped_function" for name, _ in report.skipped),
        "register_module: skips untyped function with a reason instead of raising",
    )
    check(
        not any(c["name"] == "_internal_helper" for c in registry.list_capabilities()),
        "register_module: private functions never considered",
    )


def test_register_module_strict_raises() -> None:
    import fixtures.sample_module as sample_module  # type: ignore

    registry = CapabilityRegistry()
    try:
        registry.register_module(sample_module, strict=True)
        check(False, "register_module(strict=True) should raise on first bad function")
    except CapabilityDefinitionError:
        check(True, "register_module(strict=True) raises on first bad function")


def test_register_module_prefix_and_filters() -> None:
    import fixtures.sample_module as sample_module  # type: ignore

    registry = CapabilityRegistry()
    report = registry.register_module(sample_module, prefix="math.", include=["add_numbers"])
    check(
        report.registered == ["math.add_numbers"],
        f"register_module: prefix + include filter work together (got {report.registered})",
    )

    result = run_script("__result__ = math.add_numbers(2, 3)", registry.namespace())
    check(result.return_value == 5, "register_module: prefixed capability callable in sandbox")


# --------------------------------------------------------------------------
# 3. register_class
# --------------------------------------------------------------------------


def test_register_class() -> None:
    from fixtures.sample_client import FakeStripeClient  # type: ignore

    client = FakeStripeClient()
    registry = CapabilityRegistry()
    report = registry.register_class(client, prefix="stripe.")

    check(
        set(report.registered) == {"stripe.charge_card", "stripe.refund"},
        f"register_class: registers public typed methods only (got {report.registered})",
    )
    check(
        not any("account_id" in name for name in report.registered),
        "register_class: properties are not registered as capabilities",
    )

    stub = registry.stub_file()
    check(
        "stripe.charge_card(amount_cents: int" in stub,
        "register_class: namespaced stub uses call-style syntax, not invalid `def a.b(...)`",
    )
    check(
        "Example: stripe.charge_card(1000)" in stub,
        f"register_class: example rewritten to use namespaced name (stub={stub!r})",
    )


def test_register_class_sandbox_roundtrip() -> None:
    from fixtures.sample_client import FakeStripeClient  # type: ignore

    client = FakeStripeClient()
    registry = CapabilityRegistry()
    registry.register_class(client, prefix="stripe.")

    result = run_script(
        '__result__ = {"charge": stripe.charge_card(500, currency="eur"), '
        '"refund": stripe.refund("ch_1")}',
        registry.namespace(),
    )
    check(result.error is None, f"register_class: sandbox call succeeds (error={result.error})")
    check(
        result.return_value == {
            "charge": {"charged": 500, "currency": "eur"},
            "refund": {"refunded": "ch_1"},
        },
        f"register_class: namespaced capability works correctly across sandbox process boundary "
        f"(got {result.return_value})",
    )


# --------------------------------------------------------------------------
# 4. Declarative specs (python + http targets, JSON + YAML loading)
# --------------------------------------------------------------------------


def test_register_spec_python_target() -> None:
    registry = CapabilityRegistry()
    spec = CapabilitySpec.from_dict(
        {
            "name": "get_product",
            "description": "Look up a product by SKU.",
            "target": {"kind": "python", "path": "fixtures.sample_module.lookup_product"},
        }
    )
    registry.register_spec(spec)

    result = run_script('__result__ = get_product("SKU-1")', registry.namespace())
    check(
        result.return_value == {"sku": "SKU-1", "name": "Product SKU-1", "price": 9.99},
        f"register_spec: python-target capability works in sandbox (got {result.return_value})",
    )


def test_register_spec_http_target_picklable() -> None:
    """The critical regression test: HTTP-target capabilities must be
    picklable across the sandbox's spawn boundary. A naive closure-based
    implementation fails here with AttributeError at proc.start()."""
    registry = CapabilityRegistry()
    spec = CapabilitySpec.from_dict(
        {
            "name": "get_todo",
            "description": "Fetch a todo by ID.",
            "target": {
                "kind": "http",
                "method": "GET",
                "url_template": "https://jsonplaceholder.typicode.com/todos/{todo_id}",
            },
            "parameters": {"todo_id": {"type": "int", "required": True}},
            "returns": "dict",
        }
    )
    registry.register_spec(spec)

    result = run_script("__result__ = get_todo(todo_id=1)", registry.namespace())
    check(
        result.error is None,
        f"register_spec: http-target capability survives pickling across sandbox boundary "
        f"(error={result.error})",
    )
    check(
        isinstance(result.return_value, dict) and result.return_value.get("id") == 1,
        f"register_spec: http-target capability returns real data (got {result.return_value})",
    )


def test_load_specs_json() -> None:
    registry = CapabilityRegistry()
    spec_path = Path(__file__).parent / "fixtures" / "specs.json"
    registered = registry.load_specs(spec_path)
    check(
        set(registered) == {"get_todo_json", "get_product_json"},
        f"load_specs: loads multiple capabilities from a JSON file (got {registered})",
    )


def test_load_specs_yaml() -> None:
    registry = CapabilityRegistry()
    spec_path = Path(__file__).parent / "fixtures" / "specs.yaml"
    registered = registry.load_specs(spec_path)
    check(
        registered == ["list_posts_yaml"],
        f"load_specs: loads a capability from a YAML file (got {registered})",
    )


def test_capability_spec_missing_field_raises() -> None:
    try:
        CapabilitySpec.from_dict({"name": "x"})
        check(False, "CapabilitySpec.from_dict should raise on missing required fields")
    except CapabilityDefinitionError as exc:
        check("missing required field" in str(exc), "CapabilitySpec.from_dict raises with clear message")


# --------------------------------------------------------------------------
# 5. Early picklability check
# --------------------------------------------------------------------------


class _LocalScopeOwner:
    """Used inside test_picklability_check_rejects_locally_defined_class_method
    to build a bound method whose *instance* is of a locally-defined class --
    this class itself must stay module-level so it's importable, but the
    test builds a look-alike local class inline to exercise the check."""

    def method(self, x: int) -> int:
        return x


def test_picklability_check_rejects_closure() -> None:
    registry = CapabilityRegistry()

    def make_capability():
        def get_widget(widget_id: str) -> dict:
            """Fetch a widget by ID."""
            return {"id": widget_id}

        return get_widget

    try:
        registry.register(make_capability())
        check(False, "picklability: closure should raise CapabilityDefinitionError")
    except CapabilityDefinitionError as exc:
        check(
            "closure" in str(exc) or "nested function" in str(exc),
            f"picklability: closure raises with a diagnosis naming the shape (got {exc})",
        )


def test_picklability_check_rejects_lambda() -> None:
    registry = CapabilityRegistry()
    bad = lambda x: x  # noqa: E731

    try:
        registry.register(bad, name="bad_lambda", description="A lambda.")
        check(False, "picklability: lambda should raise CapabilityDefinitionError")
    except CapabilityDefinitionError as exc:
        check("lambda" in str(exc), f"picklability: lambda raises with a diagnosis (got {exc})")


def test_picklability_check_rejects_locally_defined_class_method() -> None:
    registry = CapabilityRegistry()

    class LocallyDefinedClient:
        def get_widget(self, widget_id: str) -> dict:
            """Fetch a widget by ID."""
            return {"id": widget_id}

    client = LocallyDefinedClient()
    try:
        registry.register(client.get_widget, name="get_widget")
        check(False, "picklability: locally-defined class method should raise")
    except CapabilityDefinitionError as exc:
        check(
            "locally-defined class" in str(exc),
            f"picklability: locally-defined class method raises with a diagnosis (got {exc})",
        )


def test_picklability_check_accepts_module_level_function() -> None:
    registry = CapabilityRegistry()
    # _get_widget (defined above) is module-level -- should register fine,
    # confirming the check has no false positives on ordinary capabilities.
    registry.register(_get_widget, name="get_widget_ok")
    check(
        "get_widget_ok" in {c["name"] for c in registry.list_capabilities()},
        "picklability: ordinary module-level function registers without error",
    )


# --------------------------------------------------------------------------
# 6. Async capability support
# --------------------------------------------------------------------------


async def _fetch_widget_async(widget_id: str) -> dict:
    """Fetch a widget by ID, asynchronously."""
    return {"id": widget_id, "async": True}


def test_async_capability_registers_and_runs_in_sandbox() -> None:
    registry = CapabilityRegistry()
    registry.register(_fetch_widget_async, name="fetch_widget")

    result = run_script('__result__ = fetch_widget("w1")', registry.namespace())
    check(result.error is None, f"async: sandbox call succeeds (error={result.error})")
    check(
        result.return_value == {"id": "w1", "async": True},
        f"async: capability returns its resolved value, not a coroutine (got {result.return_value})",
    )


def test_async_capability_stub_signature_matches_sync_form() -> None:
    registry = CapabilityRegistry()
    registry.register(_fetch_widget_async, name="fetch_widget")

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check(
        caps["fetch_widget"]["signature"] == "def fetch_widget(widget_id: str) -> dict: ...",
        f"async: stub signature renders identically to a sync capability "
        f"(got {caps['fetch_widget']['signature']!r})",
    )


def test_async_capability_closure_still_rejected() -> None:
    registry = CapabilityRegistry()

    def make_async_capability():
        async def get_widget(widget_id: str) -> dict:
            """Fetch a widget by ID, asynchronously."""
            return {"id": widget_id}

        return get_widget

    try:
        registry.register(make_async_capability())
        check(False, "async: closure-based async capability should still be rejected")
    except CapabilityDefinitionError as exc:
        check(
            "closure" in str(exc) or "nested function" in str(exc),
            f"async: closure-based async capability rejected by picklability check (got {exc})",
        )


# --------------------------------------------------------------------------
# 7. @capability marker + registry.collect()
# --------------------------------------------------------------------------


@capability
def marked_get_order(order_id: str) -> dict:
    """Fetch an order by ID.

    >>> marked_get_order("o1")
    """
    return {"id": order_id}


@capability(description="Marked with explicit metadata.", example="marked_explicit()")
def marked_explicit() -> None:
    """Docstring should be ignored in favor of explicit marker metadata."""
    return None


def unmarked_function(x: int) -> int:
    """Not marked -- collect() should ignore this."""
    return x


def test_capability_marker_does_not_register() -> None:
    registry = CapabilityRegistry()
    check(
        len(registry.list_capabilities()) == 0,
        "marker: @capability alone does not register anything",
    )


def test_registry_collect_gathers_marked_functions_only() -> None:
    import sys as _sys

    registry = CapabilityRegistry()
    this_module = _sys.modules[__name__]
    report = registry.collect(this_module)

    check(
        "marked_get_order" in report.registered,
        f"collect: registers @capability-marked module-level functions (got {report.registered})",
    )
    check(
        "unmarked_function" not in report.registered,
        "collect: ignores unmarked functions even if well-typed and documented",
    )


def test_registry_collect_uses_marker_metadata() -> None:
    import sys as _sys

    registry = CapabilityRegistry()
    this_module = _sys.modules[__name__]
    registry.collect(this_module)

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check(
        caps["marked_explicit"]["description"] == "Marked with explicit metadata.",
        "collect: marker description used over docstring",
    )
    check(
        caps["marked_explicit"]["example"] == "marked_explicit()",
        "collect: marker example used over docstring",
    )


def test_register_uses_marker_as_fallback() -> None:
    registry = CapabilityRegistry()
    registry.register(marked_get_order)

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check(
        caps["marked_get_order"]["description"] == "Fetch an order by ID.",
        "register: docstring inference still applies to a marked function with no explicit marker description",
    )


# --------------------------------------------------------------------------
# 8. Per-parameter Annotated[...] descriptions
# --------------------------------------------------------------------------


def _charge_card(
    amount_cents: Annotated[int, "amount to charge, in the smallest currency unit"],
    currency: Annotated[str, "ISO 4217 currency code, e.g. \"usd\""] = "usd",
) -> dict:
    """Charge a card for the given amount."""
    return {"charged": amount_cents, "currency": currency}


def test_annotated_param_descriptions_render_in_stub() -> None:
    registry = CapabilityRegistry()
    registry.register(_charge_card, name="charge_card")

    caps = {c["name"]: c for c in registry.list_capabilities()}
    sig = caps["charge_card"]["signature"]
    check(
        "def charge_card(amount_cents: int, currency: str = 'usd') -> dict: ..." in sig,
        f"annotated: base signature line unchanged (got {sig!r})",
    )
    check(
        "#   amount_cents: amount to charge, in the smallest currency unit" in sig,
        f"annotated: amount_cents description rendered as trailing comment (got {sig!r})",
    )
    check(
        '#   currency: ISO 4217 currency code, e.g. "usd"' in sig,
        f"annotated: currency description rendered as trailing comment (got {sig!r})",
    )


def test_non_annotated_capability_renders_unchanged() -> None:
    registry = CapabilityRegistry()
    registry.register(_get_widget, name="get_widget")

    caps = {c["name"]: c for c in registry.list_capabilities()}
    check(
        caps["get_widget"]["signature"] == "def get_widget(widget_id: str) -> dict: ...",
        "annotated: a capability with zero Annotated params renders byte-identical to before "
        f"(got {caps['get_widget']['signature']!r})",
    )


# --------------------------------------------------------------------------
# 9. Sandbox process-boundary handling
#
# Regression tests for three bugs in the parent/child handoff, all of
# which silently destroyed a correctly-computed result.
# --------------------------------------------------------------------------


def _echo(n: int) -> int:
    """Return n unchanged."""
    return n


def _unpicklable() -> object:
    """Return something that can't cross a process boundary."""
    import threading

    return threading.Lock()


def _hard_exit() -> None:
    """Kill the child process abruptly, without reporting a result."""
    import os

    os._exit(3)


def test_sandbox_large_output_does_not_deadlock() -> None:
    """A multiprocessing.Queue is backed by a ~64KB pipe buffer. Joining
    the child before draining that queue deadlocks: the child blocks
    writing, the parent blocks waiting for it to exit. That reported a
    spurious timeout and threw away both stdout and a correct result."""
    registry = CapabilityRegistry()
    registry.register(_echo)

    # Budgets disabled: this test is about the process-boundary deadlock,
    # not about output size policy. With truncation active the payload
    # would be capped in the parent *after* crossing the pipe, so a
    # deadlock regression would still be caught -- but the assertion below
    # about capturing the whole stream would no longer mean anything.
    result = run_script(
        "print('x' * 500000)\n__result__ = _echo(42)",
        registry.namespace(),
        result_budget=0,
        stream_budget=0,
    )
    check(
        not result.timed_out,
        f"sandbox: 500KB of stdout does not deadlock into a spurious timeout "
        f"(timed_out={result.timed_out})",
    )
    check(
        result.return_value == 42,
        f"sandbox: result survives output larger than the pipe buffer (got {result.return_value})",
    )
    check(
        len(result.stdout) == 500001,
        f"sandbox: full stdout is captured, not truncated (got {len(result.stdout)} chars)",
    )


def test_sandbox_unpicklable_result_falls_back_to_repr() -> None:
    """Queue.put() serializes on a background feeder thread, so a
    try/except around it never sees the PicklingError -- the payload was
    dropped and stdout/stderr lost with it. The value is pickled up front
    now, so the repr fallback is actually reachable."""
    registry = CapabilityRegistry()
    registry.register(_unpicklable)

    result = run_script("print('kept')\n__result__ = _unpicklable()", registry.namespace())
    check(
        isinstance(result.return_value, str) and "lock" in result.return_value,
        f"sandbox: unpicklable result degrades to its repr (got {result.return_value!r})",
    )
    check(
        result.stdout == "kept\n",
        f"sandbox: stdout survives an unpicklable result (got {result.stdout!r})",
    )


def test_sandbox_crashed_child_is_not_reported_as_timeout() -> None:
    """A child that dies without reporting leaves the queue empty rather
    than raising, so a single blocking get() would burn the whole timeout
    and mislabel the crash as one."""
    registry = CapabilityRegistry()
    registry.register(_hard_exit)

    result = run_script("__result__ = _hard_exit()", registry.namespace(), timeout_s=15.0)
    check(
        not result.timed_out,
        "sandbox: a crashed child is reported as an unexpected exit, not a timeout",
    )
    check(
        result.error is not None and "exited unexpectedly" in result.error,
        f"sandbox: crash error names the real cause (got {result.error!r})",
    )


def test_sandbox_timeout_still_reported() -> None:
    registry = CapabilityRegistry()
    registry.register(_echo)

    result = run_script("while True: pass", registry.namespace(), timeout_s=2.0)
    check(result.timed_out, "sandbox: a genuinely hung script still times out")
    check(
        result.error is not None and "timeout" in result.error,
        f"sandbox: timeout error message preserved (got {result.error!r})",
    )


# --------------------------------------------------------------------------
# 10. Namespace shadowing
# --------------------------------------------------------------------------


def _crm_flat(x: int) -> int:
    """A plain capability that happens to be named crm."""
    return x * 10


def _crm_method(x: int) -> int:
    """A capability registered under the crm namespace."""
    return x + 1


def test_flat_capability_colliding_with_namespace_raises() -> None:
    """`crm` and `crm.get_customer` are different registry keys, so the
    duplicate-name check misses them -- but namespace() must expose `crm`
    as a _Namespace object, silently shadowing the flat callable. Both
    then appear in the catalog while one is uncallable."""
    registry = CapabilityRegistry()
    registry.register(_crm_flat, name="crm")
    try:
        registry.register(_crm_method, name="crm.get_customer")
        check(False, "shadowing: flat-then-namespace collision should raise")
    except CapabilityDefinitionError as exc:
        check(
            "collides" in str(exc),
            f"shadowing: flat-then-namespace collision raises with a clear message (got {exc})",
        )


def test_namespace_colliding_with_flat_capability_raises() -> None:
    registry = CapabilityRegistry()
    registry.register(_crm_method, name="crm.get_customer")
    try:
        registry.register(_crm_flat, name="crm")
        check(False, "shadowing: namespace-then-flat collision should raise")
    except CapabilityDefinitionError as exc:
        check(
            "collides" in str(exc),
            f"shadowing: namespace-then-flat collision raises with a clear message (got {exc})",
        )


def test_sibling_capabilities_under_one_namespace_still_work() -> None:
    """The guard must not reject the ordinary case it sits next to."""
    registry = CapabilityRegistry()
    registry.register(_crm_method, name="crm.get_customer")
    registry.register(_echo, name="crm.echo")

    result = run_script("__result__ = crm.echo(7) + crm.get_customer(1)", registry.namespace())
    check(
        result.return_value == 9,
        f"shadowing: two capabilities sharing a prefix coexist as attributes (got {result.return_value})",
    )


# --------------------------------------------------------------------------
# 11. Declarative spec validation
# --------------------------------------------------------------------------


def test_http_spec_missing_url_template_raises_definition_error() -> None:
    try:
        CapabilityRegistry().register_spec(
            CapabilitySpec.from_dict(
                {"name": "x", "description": "d", "target": {"kind": "http"}}
            )
        )
        check(False, "spec: http target with no url_template should raise")
    except CapabilityDefinitionError as exc:
        check(
            "url_template" in str(exc),
            f"spec: missing url_template raises CapabilityDefinitionError, not KeyError (got {exc})",
        )


def test_python_spec_missing_path_raises_definition_error() -> None:
    try:
        CapabilityRegistry().register_spec(
            CapabilitySpec.from_dict(
                {"name": "x", "description": "d", "target": {"kind": "python"}}
            )
        )
        check(False, "spec: python target with no path should raise")
    except CapabilityDefinitionError as exc:
        check(
            "path" in str(exc),
            f"spec: missing path raises CapabilityDefinitionError, not KeyError (got {exc})",
        )


def test_http_spec_undeclared_template_param_raises() -> None:
    """A placeholder with no matching parameter would KeyError at call
    time, inside the sandbox, where the agent can't act on it."""
    try:
        CapabilityRegistry().register_spec(
            CapabilitySpec.from_dict(
                {
                    "name": "get_order",
                    "description": "d",
                    "target": {
                        "kind": "http",
                        "url_template": "https://x.test/orders/{order_id}",
                    },
                    "parameters": {"oid": {"type": "str"}},
                }
            )
        )
        check(False, "spec: undeclared url_template placeholder should raise")
    except CapabilityDefinitionError as exc:
        check(
            "order_id" in str(exc),
            f"spec: undeclared placeholder named in the error (got {exc})",
        )


# --------------------------------------------------------------------------
# 12. Generated execute_script tool description
# --------------------------------------------------------------------------


def test_execute_script_description_reflects_served_registry() -> None:
    """The description an agent reads before writing a script has to
    describe the registry actually being served -- it used to be a
    hardcoded docstring naming the bundled demo app's capabilities, which
    are wrong for any consumer supplying their own capability set via
    SMILE_CAPABILITIES / SMILE_CAPABILITY_SPEC."""
    from smile.server.build_execute_script_description import (
        build_execute_script_description,
    )

    registry = CapabilityRegistry()
    registry.register(_get_widget, name="get_widget")
    description = build_execute_script_description(registry)

    check(
        "def get_widget(widget_id: str) -> dict: ..." in description,
        "description: the served registry's stub signatures are embedded",
    )
    check(
        "list_customers" not in description,
        "description: no leftover hardcoded example_app capability names",
    )
    check(
        "__result__" in description,
        "description: the __result__ return convention is still explained",
    )


def test_execute_script_description_handles_empty_registry() -> None:
    """An empty registry must not produce a fabricated example naming a
    capability that doesn't exist -- the agent may copy it verbatim."""
    from smile.server.build_execute_script_description import (
        build_execute_script_description,
    )

    description = build_execute_script_description(CapabilityRegistry())
    check(
        "Example of the shape" not in description,
        "description: no worked example is invented for an empty registry",
    )


# --------------------------------------------------------------------------
# 13. Output budgets (context-window protection)
# --------------------------------------------------------------------------


def _rows(n: int) -> list:
    """Return n CRM-ish rows."""
    return [
        {"id": f"cust_{i}", "name": f"Customer {i}", "email": f"c{i}@example.com"}
        for i in range(n)
    ]


def test_small_result_passes_through_untouched() -> None:
    """The budget must be invisible for ordinary results -- if it isn't,
    it's changing answers rather than protecting context."""
    registry = CapabilityRegistry()
    registry.register(_rows)

    result = run_script("__result__ = _rows(3)", registry.namespace())
    check(
        result.truncation is None,
        "budget: a small result is not truncated",
    )
    check(
        isinstance(result.return_value, list) and len(result.return_value) == 3,
        f"budget: a small result is returned verbatim (got {result.return_value!r})",
    )


def test_oversized_result_is_truncated_with_a_note() -> None:
    registry = CapabilityRegistry()
    registry.register(_rows)

    result = run_script("__result__ = _rows(10000)", registry.namespace(), timeout_s=30.0)
    check(result.truncation is not None, "budget: an oversized result is truncated")
    check(
        result.return_value["omitted_items"] == 10000 - result.return_value["returned_items"],
        f"budget: the note accounts for every omitted item (got {result.return_value.get('omitted_items')})",
    )
    check(
        "10,000" in result.return_value["original_shape"],
        f"budget: the note reports the true original size "
        f"(got {result.return_value.get('original_shape')!r})",
    )
    check(
        result.return_value["truncated"] is True,
        "budget: the note is explicitly flagged as truncated, not silently partial",
    )


def test_truncated_result_preserves_the_full_value() -> None:
    """Truncation must not destroy data -- the full value is what makes
    the resource link possible."""
    registry = CapabilityRegistry()
    registry.register(_rows)

    result = run_script("__result__ = _rows(10000)", registry.namespace(), timeout_s=30.0)
    check(
        isinstance(result.full_return_value, list) and len(result.full_return_value) == 10000,
        f"budget: the complete result is retained for resource fetch "
        f"(got {type(result.full_return_value).__name__})",
    )


def test_oversized_stdout_is_excerpted_head_and_tail() -> None:
    registry = CapabilityRegistry()
    registry.register(_echo)

    result = run_script(
        "for i in range(20000): print('row', i)\n__result__ = _echo(1)",
        registry.namespace(),
        timeout_s=30.0,
    )
    check(result.stdout_truncated, "budget: oversized stdout is marked truncated")
    check(
        "SMiLE truncated" in result.stdout,
        "budget: truncated stdout carries an inline marker naming what was dropped",
    )
    check(
        result.stdout.rstrip().endswith("row 19999"),
        "budget: the tail of stdout is preserved, not just the head",
    )
    check(
        result.return_value == 1,
        f"budget: a capped stream doesn't disturb the return value (got {result.return_value})",
    )


def test_budgets_can_be_disabled() -> None:
    registry = CapabilityRegistry()
    registry.register(_rows)

    result = run_script(
        "__result__ = _rows(5000)", registry.namespace(), result_budget=0, timeout_s=30.0
    )
    check(
        result.truncation is None and len(result.return_value) == 5000,
        "budget: result_budget=0 disables truncation for non-agent callers",
    )


# --------------------------------------------------------------------------
# 14. Result store + resource link
# --------------------------------------------------------------------------


def test_result_store_round_trip() -> None:
    from smile.server.constants import RESULT_MISSING
    from smile.server.result_store import ResultStore

    store = ResultStore()
    result_id = store.put([1, 2, 3])
    check(store.get(result_id) == [1, 2, 3], "store: a stored result round-trips by id")
    check(
        store.get("nonexistent") is RESULT_MISSING,
        "store: an unknown id returns the RESULT_MISSING sentinel",
    )


def test_result_store_distinguishes_missing_from_stored_none() -> None:
    """None is a legitimate script result, so it must not be confused with
    an evicted or unknown entry."""
    from smile.server.constants import RESULT_MISSING
    from smile.server.result_store import ResultStore

    store = ResultStore()
    result_id = store.put(None)
    check(store.get(result_id) is None, "store: a stored None comes back as None")
    check(
        store.get(result_id) is not RESULT_MISSING,
        "store: a stored None is not reported as missing",
    )


def test_result_store_evicts_oldest_past_capacity() -> None:
    from smile.server.constants import MAX_STORED_RESULTS, RESULT_MISSING
    from smile.server.result_store import ResultStore

    store = ResultStore()
    first = store.put("oldest")
    for i in range(MAX_STORED_RESULTS):
        store.put(i)

    check(
        store.get(first) is RESULT_MISSING,
        "store: the oldest entry is evicted once capacity is exceeded",
    )
    check(
        len(store._results) == MAX_STORED_RESULTS,
        f"store: the store stays bounded (got {len(store._results)} entries)",
    )


def test_tool_response_links_truncated_result() -> None:
    from smile.server.build_tool_response import build_tool_response
    from smile.server.result_store_instance import result_store

    registry = CapabilityRegistry()
    registry.register(_rows)
    result = run_script("__result__ = _rows(10000)", registry.namespace(), timeout_s=30.0)
    response = build_tool_response(result)

    check(
        "full_result_uri" in response,
        "link: a truncated response carries a resource URI",
    )
    check(
        "full_result_uri" in response["return_value"],
        "link: the URI is repeated inside the truncation note the agent reads",
    )

    result_id = response["full_result_uri"].rsplit("/", 1)[-1]
    check(
        len(result_store.get(result_id)) == 10000,
        "link: the URI resolves to the complete result in the store",
    )


def test_tool_response_omits_link_for_normal_results() -> None:
    from smile.server.build_tool_response import build_tool_response

    registry = CapabilityRegistry()
    registry.register(_rows)
    response = build_tool_response(run_script("__result__ = _rows(2)", registry.namespace()))

    check(
        "full_result_uri" not in response,
        "link: an untruncated response carries no resource link",
    )
    check(
        response["return_value"] == _rows(2),
        "link: an untruncated response returns the value verbatim",
    )


# --------------------------------------------------------------------------
# 15. Environment configuration (.mcp.json env vars)
# --------------------------------------------------------------------------


def _with_env(**overrides: str):
    """Run load_settings() with the given env vars set, restoring after."""
    import os

    from smile.server.load_settings import load_settings

    saved = {k: os.environ.get(k) for k in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        return load_settings()
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_settings_default_when_unset() -> None:
    from smile.sandbox.constants import DEFAULT_RESULT_BUDGET

    settings = _with_env()
    check(
        settings.result_budget == DEFAULT_RESULT_BUDGET,
        f"settings: unset env falls back to the built-in default "
        f"(got {settings.result_budget})",
    )


def test_settings_read_from_environment() -> None:
    settings = _with_env(
        SMILE_RESULT_BUDGET="50000",
        SMILE_STREAM_BUDGET="1000",
        SMILE_TIMEOUT_S="2.5",
        SMILE_MAX_STORED_RESULTS="4",
    )
    check(settings.result_budget == 50000, "settings: SMILE_RESULT_BUDGET is applied")
    check(settings.stream_budget == 1000, "settings: SMILE_STREAM_BUDGET is applied")
    check(settings.timeout_s == 2.5, "settings: SMILE_TIMEOUT_S accepts a float")
    check(
        settings.max_stored_results == 4,
        "settings: SMILE_MAX_STORED_RESULTS is applied",
    )


def test_settings_accept_underscore_separators() -> None:
    """These are read and edited by humans in a JSON config."""
    settings = _with_env(SMILE_RESULT_BUDGET="24_000")
    check(settings.result_budget == 24000, "settings: underscore digit separators are accepted")


def test_settings_zero_disables_a_budget() -> None:
    settings = _with_env(SMILE_RESULT_BUDGET="0")
    check(settings.result_budget == 0, "settings: 0 is accepted as 'no limit'")


def test_settings_reject_malformed_values() -> None:
    """A typo in .mcp.json must stop the server, not silently revert to a
    default the consumer never chose."""
    for value in ("lots", "12.5", "-5"):
        try:
            _with_env(SMILE_RESULT_BUDGET=value)
            check(False, f"settings: SMILE_RESULT_BUDGET={value!r} should raise")
        except CapabilityDefinitionError as exc:
            check(
                "SMILE_RESULT_BUDGET" in str(exc),
                f"settings: malformed budget {value!r} raises naming the variable (got {exc})",
            )


def test_settings_reject_nonpositive_timeout() -> None:
    for value in ("0", "-1"):
        try:
            _with_env(SMILE_TIMEOUT_S=value)
            check(False, f"settings: SMILE_TIMEOUT_S={value!r} should raise")
        except CapabilityDefinitionError as exc:
            check(
                "greater than zero" in str(exc),
                f"settings: non-positive timeout rejected (got {exc})",
            )


def test_settings_reject_empty_result_store() -> None:
    """A zero-capacity store would hand out links that never resolve."""
    try:
        _with_env(SMILE_MAX_STORED_RESULTS="0")
        check(False, "settings: SMILE_MAX_STORED_RESULTS=0 should raise")
    except CapabilityDefinitionError as exc:
        check(
            "at least 1" in str(exc),
            f"settings: empty result store rejected (got {exc})",
        )


def test_result_store_honors_configured_capacity() -> None:
    from smile.server.constants import RESULT_MISSING
    from smile.server.result_store import ResultStore

    store = ResultStore(max_results=2)
    first = store.put("a")
    store.put("b")
    store.put("c")

    check(
        store.get(first) is RESULT_MISSING and len(store._results) == 2,
        f"settings: a store sized from config evicts at that size "
        f"(got {len(store._results)} entries)",
    )


def test_example_mcp_json_is_valid_and_bootable() -> None:
    """The shipped example is copy-paste config -- it must parse, and it
    must not reference a capability module that doesn't exist."""
    import json
    from pathlib import Path

    path = Path(__file__).parent.parent / ".mcp.json.example"
    config = json.loads(path.read_text())
    env = config["mcpServers"]["smile"]["env"]
    active = {k: v for k, v in env.items() if not k.startswith("$")}

    check(
        all(isinstance(v, str) for v in active.values()),
        "example: every active env value is a string, as MCP clients require",
    )
    check(
        "SMILE_CAPABILITIES" not in active and "SMILE_CAPABILITY_SPEC" not in active,
        "example: ships with no capability source set, so it boots against the demo app",
    )

    settings = _with_env(**active)
    check(
        settings.result_budget > 0 and settings.timeout_s > 0,
        "example: the shipped values load as valid settings",
    )


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    for test_fn in tests:
        print(f"\n--- {test_fn.__name__} ---")
        test_fn()

    print("\n" + "=" * 60)
    if _failures:
        print(f"{len(_failures)} FAILURE(S):")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")
