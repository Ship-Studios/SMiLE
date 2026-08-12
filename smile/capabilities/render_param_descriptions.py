"""render_param_descriptions: formats a {param_name: description} dict as
trailing comment lines appended after a capability's stub signature."""

from __future__ import annotations


def render_param_descriptions(descriptions: dict[str, str]) -> str:
    if not descriptions:
        return ""
    return "\n".join(f"#   {name}: {desc}" for name, desc in descriptions.items())
