"""
Real end-to-end test: Gemini (gemini-2.5-flash-lite) driving the SMiLE MCP
server as an actual tool-calling agent.

This is not a scripted stand-in -- it:
  1. Launches smile/server.py as a real MCP subprocess over stdio
  2. Converts the server's MCP tool schemas into Gemini FunctionDeclarations
  3. Sends Gemini a task in plain English
  4. Lets Gemini decide, on its own, to call list_capabilities and then
     execute_script with a script it writes itself
  5. Executes those calls against the live MCP session and feeds results
     back to Gemini until it produces a final answer

Run with:  GEMINI_API_KEY=... uv run python3 tests/e2e_gemini.py
"""

from __future__ import annotations

import asyncio
import json
import os

from google import genai
from google.genai import types as gtypes
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "gemini-2.5-flash-lite"

TASK = (
    "Using the available tools, find all 'enterprise' tier customers, "
    "and for each one, compute the total amount they've paid (status='paid' orders only). "
    "Then send each of them an email with the subject 'Your account summary' "
    "and a body mentioning their total. "
    "Do this with a single script rather than many small tool calls. "
    "Finally, tell me in plain English how many customers you emailed and their totals."
)


def mcp_tool_to_gemini_declaration(tool) -> gtypes.FunctionDeclaration:
    """Convert an MCP Tool (name, description, inputSchema) into the shape
    Gemini's function-calling API expects."""
    schema = dict(tool.input_schema)
    # Gemini's schema validator rejects JSON Schema keys it doesn't know
    # about (e.g. "title", "$schema") on some SDK versions -- strip to the
    # minimal subset MCP tool schemas actually use.
    #
    # IMPORTANT: the allowlist only applies to *schema keywords*
    # ("type", "properties", "required", ...) -- it must never be applied
    # to the keys *inside* a "properties" object, since those are
    # arbitrary parameter names (e.g. "code"), not schema keywords. A
    # naive recursive filter strips them by accident.
    _SCHEMA_KEYWORDS = {"type", "properties", "required", "items", "description", "enum"}

    def _clean_schema(node):
        """Clean a JSON-Schema node: filter its own keys against the
        keyword allowlist, but recurse into `properties` values (which are
        keyed by arbitrary parameter names) via _clean_properties."""
        if not isinstance(node, dict):
            return node
        cleaned = {}
        for k, v in node.items():
            if k not in _SCHEMA_KEYWORDS:
                continue
            if k == "properties":
                cleaned[k] = _clean_properties(v)
            elif k == "items":
                cleaned[k] = _clean_schema(v)
            else:
                cleaned[k] = v
        return cleaned

    def _clean_properties(properties: dict) -> dict:
        """Clean the value of a "properties" key: keys here are parameter
        names and must be preserved as-is; only their sub-schemas are
        cleaned."""
        return {name: _clean_schema(sub_schema) for name, sub_schema in properties.items()}

    return gtypes.FunctionDeclaration(
        name=tool.name,
        description=tool.description or "",
        parameters=_clean_schema(schema),
    )


async def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)

    params = StdioServerParameters(command="uv", args=["run", "python3", "-m", "smile.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            print(f"[setup] MCP server exposes: {[t.name for t in mcp_tools]}\n")

            gemini_tool = gtypes.Tool(
                function_declarations=[mcp_tool_to_gemini_declaration(t) for t in mcp_tools]
            )

            contents: list[gtypes.Content] = [
                gtypes.Content(role="user", parts=[gtypes.Part(text=TASK)])
            ]

            max_turns = 6
            for turn in range(1, max_turns + 1):
                print(f"--- turn {turn}: sending to {MODEL} ---")
                response = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=gtypes.GenerateContentConfig(
                        tools=[gemini_tool],
                        # Force the model to actually use tools rather than
                        # answering from nothing, until it's done.
                        automatic_function_calling=gtypes.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )

                candidate = response.candidates[0]
                contents.append(candidate.content)

                function_calls = [
                    part.function_call
                    for part in candidate.content.parts
                    if part.function_call is not None
                ]

                if not function_calls:
                    text = "".join(
                        part.text for part in candidate.content.parts if part.text
                    )
                    print(f"\n[final answer, turn {turn}]\n{text}\n")
                    return

                # Execute every requested tool call against the *real* MCP
                # server, then feed all results back in one turn.
                response_parts = []
                for fc in function_calls:
                    print(f"  [gemini requested] {fc.name}({json.dumps(dict(fc.args))[:200]})")
                    result = await session.call_tool(fc.name, dict(fc.args))
                    result_text = "\n".join(
                        block.text for block in result.content if hasattr(block, "text")
                    )
                    print(f"  [mcp server returned] {result_text[:300]}")
                    response_parts.append(
                        gtypes.Part(
                            function_response=gtypes.FunctionResponse(
                                name=fc.name,
                                response={"result": result_text},
                            )
                        )
                    )
                contents.append(gtypes.Content(role="tool", parts=response_parts))
                print()

            print("[stopped] hit max_turns without a final answer")


if __name__ == "__main__":
    asyncio.run(main())
