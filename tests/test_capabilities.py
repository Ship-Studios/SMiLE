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
