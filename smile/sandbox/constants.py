"""Shared constants for the sandbox package. No functions/methods here --
this file exists so the constants aren't declared inside a function/method
file (which would violate one-def-per-file for that file's own function)."""

DEFAULT_TIMEOUT_S = 10.0

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
        "StopIteration", "RuntimeError", "AttributeError", "ArithmeticError",
        "ZeroDivisionError", "OverflowError", "AssertionError",
    }
)
