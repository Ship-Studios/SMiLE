"""dotted_call_name: resolves an ast.Call's func expression to the dotted
name it would be exposed as in the sandbox namespace, e.g. Name("foo") ->
"foo", Attribute(Name("crm"), "get_customer") -> "crm.get_customer".

Only these two shapes are ever produced by registry_namespace() (flat
names or one level of namespace.attr), so anything else -- a call
through a subscript, a chained attribute, a call result -- can't be a
capability call and returns None.
"""

from __future__ import annotations

import ast


def dotted_call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return None
