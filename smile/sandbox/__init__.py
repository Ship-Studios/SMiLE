"""
Sandboxed executor: runs agent-submitted Python against a capability
namespace, in a separate subprocess.

PROTOTYPE-GRADE ISOLATION ONLY. This uses a subprocess boundary, a
restricted __builtins__ set, and no import machinery beyond what's
injected. That stops accidental misuse and casual escapes -- it is NOT
adversarially secure. It does not stop a determined attacker with code
execution (e.g. via ctypes-style introspection tricks, or resource
exhaustion beyond the coarse limits set here).

A production version of SMiLE should replace this module's isolation
mechanism with one of:
  - Pyodide/WASM (wasmtime or similar) -- memory-safe by construction
  - gVisor or Firecracker microVMs -- OS-level isolation
  - A managed code-execution service

The public interface (`run_script`) is written so that swap is
contained to this package -- callers just get a ScriptResult back.

This package follows the project's one-function/method-per-file rule
(see CLAUDE.md): each piece lives in its own module, reassembled here
for a stable public import surface (`from smile.sandbox import
run_script, ScriptResult` keeps working exactly as when this was a
single sandbox.py file).
"""

from __future__ import annotations

from smile.sandbox.run_script import run_script
from smile.sandbox.script_result import ScriptResult

__all__ = ["run_script", "ScriptResult"]
