import { FormEvent, useState } from "react";
import type { ConversationRun } from "../types/api";

type ChatPanelProps = {
  runs: ConversationRun[];
  loading: boolean;
  historyLoading: boolean;
  error: string | null;
  starterPrompts: string[];
  sessionTitle: string;
  userId: string;
  onSend: (message: string) => Promise<void>;
};

export default function ChatPanel({
  runs,
  loading,
  historyLoading,
  error,
  starterPrompts,
  sessionTitle,
  userId,
  onSend
}: ChatPanelProps) {
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const clean = message.trim();
    if (!clean || loading) {
      return;
    }
    setMessage("");
    await onSend(clean);
  }

  return (
    <section className="chat-panel">
      <div className="chat-panel-header">
        <div>
          <span className="section-label">Conversation</span>
          <h2>{sessionTitle}</h2>
        </div>
        <div className="user-pill">{userId}</div>
      </div>

      <div className="conversation">
        {historyLoading ? (
          <div className="loading-state">
            <h2>Loading conversation</h2>
            <p>Fetching this user&apos;s saved history and active session...</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="empty-state">
            <h2>Run an agent task</h2>
            <p>
              Ask for weather, time, calculations, local docs, web search, or
              todos. This home page stays focused on conversation only.
            </p>
            <div className="prompt-grid">
              {starterPrompts.map((prompt) => (
                <button
                  className="prompt-chip"
                  type="button"
                  key={prompt}
                  onClick={() => setMessage(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          runs.map((run, index) => (
            <article
              className="turn"
              key={`${run.id ?? index}-${run.created_at}`}
            >
              <div className="bubble user-bubble">
                <span>User</span>
                <p>{run.user_input}</p>
              </div>
              <div className="bubble agent-bubble">
                <span>Agent final answer</span>
                <p>{run.final_answer}</p>
              </div>
              <div className="turn-meta">
                Round {index + 1} · {new Date(run.created_at).toLocaleString()}
              </div>
            </article>
          ))
        )}
      </div>

      {error ? <div className="error-line">{error}</div> : null}

      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask MMagent to solve a task..."
          rows={3}
        />
        <button className="send-button" type="submit" disabled={loading}>
          {loading ? "Running" : "Send"}
        </button>
      </form>
    </section>
  );
}
