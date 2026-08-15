"""Live Popen objects spawned by run_subprocess in this process.

Held as a module-level list so the worker SIGTERM handler can kill
them when the sandbox parent tears the worker down. No functions here
-- exempt from the one-def-per-file rule.
"""

from __future__ import annotations

import subprocess

live: list[subprocess.Popen] = []
