# Frontend Trace and Conversation Memory

The MMagent frontend is built with React, TypeScript, and Vite. It separates the
main chat page from the trace and tools pages.

## Home Page

The Home page focuses on conversation. Users can enter a User ID, choose an
existing conversation, start a new conversation, and send messages to the Agent.

## Trace Page

The Trace page shows each Agent step:

- model output
- parsed JSON tool call
- tool result
- final answer

This makes the Agent execution loop visible for debugging and interviews.

## Conversation Persistence

The backend supports user-scoped sessions. Conversation runs can be stored in
MySQL when database settings are configured. If MySQL is unavailable, the system
falls back to in-memory conversation state for local demos.

Important files:

- frontend/src/App.tsx
- frontend/src/components/ChatPanel.tsx
- frontend/src/components/TracePanel.tsx
- backend/app/services/conversation_store.py
