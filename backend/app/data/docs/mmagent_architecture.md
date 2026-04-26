# MMagent Architecture

MMagent is a JSON Tool Calling Agent system. Its main goal is to demonstrate an
engineering-style Agent runtime rather than a plain chatbot.

## Runtime Loop

The runtime receives user input, keeps conversation memory, builds a system
prompt with the registered tool list, calls the LLM adapter, parses the JSON
output, executes a tool when needed, stores the tool result, and repeats until
the model returns a final answer.

Important files:

- backend/app/agent/runtime.py
- backend/app/agent/memory.py
- backend/app/agent/prompts.py

## Tool Registry

The Tool Registry stores tool name, description, Pydantic input schema, and the
handler function. Runtime code does not hard-code weather, todos, web search, or
document search. It only calls the registry by tool name.

Important files:

- backend/app/tools/registry.py
- backend/app/tools/builtin.py
- backend/app/tools/context.py

## LLM Adapter

The LLM adapter layer lets the project switch between a local MockLLMAdapter and
an OpenAI-compatible chat completion model. This keeps provider-specific API
details away from the Agent runtime.

Important files:

- backend/app/llm/base.py
- backend/app/llm/mock.py
- backend/app/llm/openai_compatible.py
