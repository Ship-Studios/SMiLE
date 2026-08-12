"""A fake "existing module" -- not written with SMiLE in mind, used to
test register_module and the CapabilitySpec python-target path."""

from __future__ import annotations


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def greet(name: str, formal: bool = False) -> str:
    """Greet someone by name.

    >>> greet("Ada")
    """
    return f"Good day, {name}" if formal else f"Hi {name}"


def _internal_helper(x: int) -> int:
    """Should be skipped -- starts with underscore."""
    return x * 2


def untyped_function(x):
    """Missing a type hint -- should be skipped by register_module's
    default non-strict mode, and raise in strict mode."""
    return x


def lookup_product(sku: str) -> dict:
    """Look up a product by SKU."""
    return {"sku": sku, "name": f"Product {sku}", "price": 9.99}
