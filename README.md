# MMagent

MMagent is a runnable JSON Tool Calling Agent demo. It is designed as an
interview-ready project that shows how to build an Agent runtime, a tool
registry, a mock/real LLM adapter layer, and a frontend trace visualizer.

## Directory Tree

```text
MMagent/
  backend/
    app/
      agent/        # runtime loop, memory, system prompt
      api/          # FastAPI routes
      core/         # config and logging
      data/         # local knowledge base and todo store
      llm/          # BaseLLMAdapter, MockLLMAdapter, OpenAI-compatible adapter
      schemas/      # Pydantic JSON tool calling protocol
      services/     # todo persistence service
      tools/        # tool registry and built-in tools
      utils/        # safe calculator evaluator
    requirements.txt
  frontend/
    src/
      components/   # chat, trace, tools, JSON viewer
      hooks/
      services/
      types/
    package.json
  .env.example
  README.md
```

## Core Features

- Agent Runtime: multi-step reasoning-execution-observation loop with a max
  step guard.
- JSON Tool Calling Protocol: `tool_call`, `tool_result`, and `final_answer`
  are defined with Pydantic.
- Tool Registry: tools are registered by name, description, input schema, and
  handler function.
- LLM Adapter Layer: local `MockLLMAdapter` works without an API key;
  `OpenAICompatibleAdapter` is ready for real chat-completion models.
- Observability: every model output, parsed JSON call, tool result, and final
  answer is returned as trace data and visualized in React.
- Extensibility: includes a `map_lookup` tool to show how this architecture can
  evolve into a game Agent.

## JSON Tool Calling Protocol

Tool call:

```json
{
  "type": "tool_call",
  "tool_name": "get_weather",
  "arguments": {
    "city": "Nanjing"
  },
  "thought": "Need weather info before answering"
}
```

Tool result:

```json
{
  "type": "tool_result",
  "tool_name": "get_weather",
  "status": "success",
  "result": {
    "city": "Nanjing",
    "temperature": "26C",
    "condition": "Sunny"
  }
}
```

Final answer:

```json
{
  "type": "final_answer",
  "answer": "The weather in Nanjing is Sunny and 26C."
}
```

## Built-in Tools

- `get_weather`: mock weather by city.
- `get_time`: local time by city or IANA timezone.
- `calculator`: safe arithmetic for `+`, `-`, `*`, `/`, and parentheses.
- `search_docs`: keyword search over `backend/app/data/knowledge.md`.
- `todo_add`: add a todo item.
- `todo_list`: list todo items.
- `todo_delete`: delete a todo item by 1-based index.
- `get_system_status`: inspect runtime status.
- `map_lookup`: game-AI style map observation demo.

## Run Locally

Windows one-click startup:

```bat
start-local.bat
```

This script creates/repairs the backend virtual environment, installs backend
and frontend dependencies when needed, and opens two terminal windows for the
FastAPI backend and Vite frontend.

Backend:

```bash
cd MMagent/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd MMagent/frontend
npm install
npm run dev
```

Open the frontend at `http://127.0.0.1:5173`.

## Environment

Copy `.env.example` to `.env` in the project root. The default mode is mock and
does not require any API key.

To use a real model:

```env
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

## API Examples

Health:

```bash
curl http://127.0.0.1:8000/api/health
```

Chat:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"What's the weather and current time in Nanjing?\"}"
```

Response shape:

```json
{
  "session_id": "...",
  "final_answer": "...",
  "trace": [
    {
      "step": 1,
      "model_output": "{\"type\":\"tool_call\",...}",
      "tool_call": {
        "type": "tool_call",
        "tool_name": "get_weather",
        "arguments": {
          "city": "Nanjing"
        }
      },
      "tool_result": {
        "type": "tool_result",
        "tool_name": "get_weather",
        "status": "success"
      }
    }
  ],
  "messages": []
}
```

## Screenshot Placeholder

Add screenshots after running the app:

- `docs/screenshots/chat-trace.png`
- `docs/screenshots/tools-panel.png`

## Resume Bullet Ideas

- Built a JSON Tool Calling Agent runtime with a multi-step
  reasoning-execution-observation loop.
- Designed a Pydantic-based protocol for tool calls, tool results, and final
  answers.
- Implemented a pluggable Tool Registry with schema-driven tool discovery and
  execution.
- Added a mock LLM adapter for local demos and an OpenAI-compatible adapter for
  production model integration.
- Created a React + TypeScript trace dashboard for inspecting model outputs,
  JSON tool calls, tool results, and final answers.

## Extension Roadmap

- Add streaming responses through Server-Sent Events or WebSocket.
- Persist sessions in SQLite or Postgres.
- Add authentication and per-user todo/document stores.
- Add multimodal file upload and image understanding tools.
- Expand game Agent tools: inventory query, enemy position query, move, attack,
  pickup, and planner policies.
- Add test suites for tool validation, runtime loops, and adapter parsing.
