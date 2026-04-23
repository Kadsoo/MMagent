import { useMemo, useState } from "react";
import ChatPanel from "./components/ChatPanel";
import ToolsPanel from "./components/ToolsPanel";
import TracePanel from "./components/TracePanel";
import { chat } from "./services/api";
import type { ChatTurn, TraceStep } from "./types/api";
import { useTools } from "./hooks/useTools";

const starterPrompts = [
  "What's the weather and current time in Nanjing?",
  "Calculate (18 + 24) / 3 and explain the result.",
  "Search docs for JSON tool calling runtime.",
  "Add todo: prepare MMagent demo for interview",
  "List todos",
  "Look up the forest map."
];

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { tools, loading: toolsLoading, error: toolsError } = useTools();

  const lastAnswer = useMemo(
    () => turns.length > 0 ? turns[turns.length - 1].answer : "",
    [turns]
  );

  async function handleSend(message: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await chat({ message, session_id: sessionId });
      setSessionId(response.session_id);
      setTurns((current) => [
        ...current,
        {
          id: `${Date.now()}`,
          user: message,
          answer: response.final_answer
        }
      ]);
      setTrace(response.trace);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">JSON Tool Calling Agent Runtime</p>
          <h1>MMagent</h1>
        </div>
        <div className="status-strip">
          <span>{tools.length} tools</span>
          <span>{trace.length} trace steps</span>
          <span>{sessionId ? "session active" : "new session"}</span>
        </div>
      </header>

      <section className="workspace">
        <ChatPanel
          turns={turns}
          loading={loading}
          error={error}
          starterPrompts={starterPrompts}
          onSend={handleSend}
          lastAnswer={lastAnswer}
        />

        <aside className="inspector">
          <TracePanel trace={trace} />
          <ToolsPanel tools={tools} loading={toolsLoading} error={toolsError} />
        </aside>
      </section>
    </main>
  );
}

