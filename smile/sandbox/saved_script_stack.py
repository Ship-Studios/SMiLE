"""Call-depth tracker for saved-script invocation. A ContextVar (no
function) so nested scripts.a -> scripts.b calls in one execute_script
share a stack without pickling anything across the process boundary.
"""

from __future__ import annotations

import contextvars

_call_stack: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar(
    "smile_saved_script_stack", default=()
)
