# MMagent Knowledge Base

MMagent is a demo project for a JSON Tool Calling Agent runtime. It separates
the Agent loop, LLM adapter, tool registry, schemas, services, and API layer.

## Agent Runtime

The runtime receives user input, builds a system prompt with available tools,
calls an LLM adapter, parses structured JSON, executes tools, records
observations, and repeats the reasoning-execution-observation loop until a
final answer is produced.

## JSON Tool Calling Protocol

The protocol uses explicit JSON objects:

- `tool_call` asks the runtime to execute a named tool with JSON arguments.
- `tool_result` records the execution status and returned payload.
- `final_answer` ends the loop with a user-facing answer.

## Tool Registry

Tools are registered with a name, description, Pydantic input schema, and
handler function. This makes capabilities discoverable from `/api/tools` and
keeps runtime code independent from specific tools.

## LLM Adapter

The default adapter is `MockLLMAdapter`, which runs locally without an API key.
`OpenAICompatibleAdapter` is included for real model calls through
OpenAI-compatible chat completions.

## Game Agent Extension

The `map_lookup` tool is a small game-AI extension point. Future tools can add
inventory queries, enemy position queries, move actions, attack actions, and
pickup actions without changing the runtime loop.

