"""SavedScript.__call__ implementation. Attached to the SavedScript
class in saved_script.py."""

from __future__ import annotations

import typing
from typing import Any

from smile.sandbox.constants import MAX_SAVED_SCRIPT_DEPTH
from smile.sandbox.saved_script_stack import _call_stack

if typing.TYPE_CHECKING:
    from smile.sandbox.saved_script import SavedScript


def saved_script_call(self: "SavedScript", *args: Any, **kwargs: Any) -> Any:
    """Exec the saved function source in an isolated globals dict that
    still sees the same capabilities and `scripts` namespace, then call
    it. Isolation is what keeps one invocation's locals from leaking
    into the next; sharing `scripts` is what lets saved scripts compose.
    """
    stack = _call_stack.get()
    if len(stack) >= MAX_SAVED_SCRIPT_DEPTH:
        chain = " -> ".join((*stack, self.record.name))
        raise RuntimeError(
            f"Saved script call depth exceeded ({MAX_SAVED_SCRIPT_DEPTH}): "
            f"{chain}. A cycle or unbounded recursion is likely."
        )
    token = _call_stack.set((*stack, self.record.name))
    try:
        g: dict[str, Any] = {"__builtins__": self.builtins}
        g.update(self.inject)
        exec(
            compile(self.record.source, f"<saved:{self.record.name}>", "exec"),
            g,
        )
        fn = g.get(self.record.func_name)
        if not callable(fn):
            raise RuntimeError(
                f"Saved script '{self.record.name}' did not define "
                f"callable {self.record.func_name!r}."
            )
        return fn(*args, **kwargs)
    finally:
        _call_stack.reset(token)
