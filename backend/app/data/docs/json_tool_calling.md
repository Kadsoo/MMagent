# JSON Tool Calling Protocol

MMagent uses a structured JSON protocol for tool calling. The model is expected
to return either a tool call or a final answer.

## Tool Call

A tool call asks the runtime to execute a named tool with JSON arguments.

```json
{
  "type": "tool_call",
  "tool_name": "search_docs",
  "arguments": {
    "query": "How does the Agent runtime work?"
  },
  "thought": "Need local project context before answering."
}
```

## Tool Result

The runtime executes the tool and writes the result back into conversation
memory as a tool message.

```json
{
  "type": "tool_result",
  "tool_name": "search_docs",
  "status": "success",
  "result": {
    "summary": "Matched knowledge base snippet..."
  }
}
```

## Final Answer

When the model has enough information, it returns a final answer.

```json
{
  "type": "final_answer",
  "answer": "The Agent runtime uses a multi-step reasoning and execution loop."
}
```

The protocol schemas are defined in backend/app/schemas/protocol.py.
