"""perform_execute_script: the execute_script tool body, extracted so
tests can pass a local registry/store/settings without going through
MCP or the process-global instances.
"""

from __future__ import annotations

import typing
from typing import Any

from smile.sandbox import ScriptResult, run_script
from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.build_tool_response import build_tool_response
from smile.server.extract_called_capabilities import extract_called_capabilities
from smile.server.log_intent import log_intent
from smile.server.parse_save_request import parse_save_request
from smile.server.parse_unpublish_request import parse_unpublish_request
from smile.server.saved_script_error import SavedScriptError
from smile.server.scripts_namespace_taken import scripts_namespace_taken
from smile.server.validate_saved_script import validate_saved_script

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry
    from smile.server.script_store import ScriptStore
    from smile.server.server_settings import ServerSettings


def perform_execute_script(
    code: str,
    intent: str,
    *,
    registry: "CapabilityRegistry | None" = None,
    script_store: "ScriptStore | None" = None,
    settings: "ServerSettings | None" = None,
) -> dict[str, Any]:
    """Run `code` against `registry`, honoring `__save__` and injecting
    any already-saved functions as `scripts.*`.

    Defaults to the process-global registry/store/settings used by the
    MCP tool; tests pass locals so they do not publish into the live
    session store or append to the live intent log.
    """
    if not intent.strip():
        raise ValueError(
            "intent must be a non-empty, plain-English description of what "
            "the script is trying to do."
        )
    if registry is None:
        from smile.server.registry_instance import registry as registry
    if script_store is None:
        from smile.server.script_store_instance import script_store as script_store
    if settings is None:
        from smile.server.settings_instance import settings as settings

    saved_script_info: dict[str, str] | None = None
    unpublished_info: dict[str, str] | None = None
    try:
        save_request = parse_save_request(code)
        unpublish_name = parse_unpublish_request(code)
        if save_request is not None and unpublish_name is not None:
            raise SavedScriptError(
                "Cannot set both __save__ and __unpublish__ in the same "
                "script. Publish and remove in separate execute_script calls."
            )
        if unpublish_name is not None:
            script_store.delete(unpublish_name)
            unpublished_info = {"name": f"scripts.{unpublish_name}"}
        if save_request is not None:
            validate_saved_script(save_request, registry, script_store)
            script_store.put(
                SavedScriptRecord(
                    name=save_request.name,
                    func_name=save_request.func_name,
                    source=save_request.source,
                    description=save_request.description,
                    signature=save_request.signature,
                    example=save_request.example,
                )
            )
            saved_script_info = {
                "name": f"scripts.{save_request.name}",
                "signature": save_request.signature,
                "description": save_request.description,
            }
    except SavedScriptError as exc:
        result = ScriptResult(
            stdout="",
            stderr="",
            return_value=None,
            error=str(exc),
            timed_out=False,
        )
        log_intent(
            settings.intent_log_path,
            intent,
            code,
            extract_called_capabilities(code, registry, script_store.sources()),
            result,
        )
        return build_tool_response(result)

    saved_scripts = None
    if not scripts_namespace_taken(registry):
        saved_scripts = tuple(script_store.list())

    result = run_script(
        code,
        registry.namespace(),
        saved_scripts=saved_scripts,
        timeout_s=settings.timeout_s,
        result_budget=settings.result_budget,
        stream_budget=settings.stream_budget,
    )
    log_intent(
        settings.intent_log_path,
        intent,
        code,
        extract_called_capabilities(code, registry, script_store.sources()),
        result,
    )
    response = build_tool_response(result)
    if saved_script_info is not None:
        response["saved_script"] = saved_script_info
    if unpublished_info is not None:
        response["unpublished_script"] = unpublished_info
    return response
