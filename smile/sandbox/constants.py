"""Shared constants for the sandbox package. No functions/methods here --
this file exists so the constants aren't declared inside a function/method
file (which would violate one-def-per-file for that file's own function)."""

# Sized to fit the default-served run_tests() capability with slack.
DEFAULT_TIMEOUT_S = 30.0

# Grace period for reaping a child process that has already delivered its
# result (or is being terminated). Not a script budget -- purely the time
# allowed for process teardown between the final queue put() and exit.
REAP_TIMEOUT_S = 1.0

# How long the parent blocks on any single queue read while waiting for a
# result (see await_payload.py). Bounds how long a child that died without
# reporting goes unnoticed; short enough to stay responsive, long enough
# not to spin.
POLL_INTERVAL_S = 0.05

# Sentinels distinguishing "no payload" causes in await_payload(). Plain
# module-level objects so they're identity-comparable and can never collide
# with a value a script legitimately returned.
TIMED_OUT = object()
DIED_SILENTLY = object()

# --------------------------------------------------------------------------
# Output budgets
#
# A script result goes straight into the agent's context window, so an
# unbounded result is a context-exhaustion bug: 10,000 CRM-ish rows measure
# ~1.3M characters (~334k tokens), enough to overflow even a large window
# outright and destroy the session. These caps bound that blast radius.
#
# Budgets are in CHARACTERS, not tokens. Tokens are what actually matter,
# but counting them requires a tokenizer specific to the client's model,
# which the server doesn't know. Characters are a stable, dependency-free
# proxy at roughly 4 chars/token for JSON-ish text.
#
# Sized conservatively against a 100k-token context window -- the planning
# assumption, not the largest window available, since a budget tuned to a
# 200k window silently misbehaves on anything smaller. execute_script is
# called repeatedly in a loop, so what matters is not "does one call fit"
# but "how many calls fit before the agent is squeezed":
#
#   worst case per call = result + both streams = 20,000 chars = ~5,000
#   tokens = ~5% of a 100k window, so ~20 calls before real pressure.
#
# The result budget is still generous in absolute terms: ~12,000 characters
# passes a 100-row shortlist through untouched, so it caps accidental data
# dumps without clipping legitimate answers. Callers with a bigger window
# (or none at all) can raise or disable these per call.
# --------------------------------------------------------------------------

DEFAULT_RESULT_BUDGET = 12_000
DEFAULT_STREAM_BUDGET = 4_000

# How many leading list elements a truncation note keeps as a sample.
# Enough to show the agent the row shape; far too few to mistake for the
# whole result. Kept small relative to DEFAULT_RESULT_BUDGET -- the sample
# exists to convey structure, not content, and every row it spends is
# budget not available to the note explaining what was dropped.
TRUNCATION_SAMPLE_ROWS = 10

# How many dict keys describe_shape() names before eliding.
SHAPE_KEY_SAMPLE = 8

# Share of a truncated stream's budget reserved for its tail. The end of a
# log usually carries the failure or the summary, so keep a slice of it.
STREAM_TAIL_FRACTION = 0.3

# How deep one execute_script call may nest saved-script invocations
# (scripts.a calling scripts.b calling ...). Bounds runaway recursion /
# mutual cycles with a clearer error than a raw RecursionError. Ordinary
# composition is one or two deep; 32 is generous for that and still
# fails fast on an unbounded loop.
MAX_SAVED_SCRIPT_DEPTH = 32

# Reserved sandbox global under which saved scripts are exposed, e.g.
# scripts.paid_total(...). Must stay a single identifier --
# registry_namespace only supports one dot of attribute access.
SAVED_SCRIPTS_NAMESPACE = "scripts"

# Builtins considered safe enough for a trusted-ish scripting sandbox.
# Deliberately excludes: __import__, open, exec, eval, compile, input,
# breakpoint, exit, quit, and anything that touches the filesystem or
# process.
SAFE_BUILTIN_NAMES = frozenset(
    {
        "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
        "callable", "chr", "complex", "dict", "divmod", "enumerate",
        "filter", "float", "format", "frozenset", "getattr", "hasattr",
        "hash", "hex", "id", "int", "isinstance", "issubclass", "iter",
        "len", "list", "map", "max", "min", "next", "oct", "ord", "pow",
        "print", "property", "range", "repr", "reversed", "round", "set",
        "setattr", "slice", "sorted", "str", "sum", "tuple", "type", "zip",
        "None", "True", "False", "NotImplemented",
        "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
        "NameError",
        "StopIteration", "RuntimeError", "AttributeError", "ArithmeticError",
        "ZeroDivisionError", "OverflowError", "AssertionError",
    }
)
