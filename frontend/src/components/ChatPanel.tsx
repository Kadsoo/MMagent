import { FormEvent, useState } from "react";
import type { ChatTurn } from "../types/api";

type ChatPanelProps = {
  turns: ChatTurn[];
  loading: boolean;
  error: string | null;
  starterPrompts: string[];
  lastAnswer: string;
  onSend: (message: string) => Promise<void>;
};

export default function ChatPanel({
  turns,
  loading,
  error,
  starterPrompts,
  lastAnswer,
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
      <div className="conversation">
        {turns.length === 0 ? (
          <div className="empty-state">
            <h2>Run an agent task</h2>
            <p>
              Ask for weather, time, calculations, local docs, todos, or map
              observations. The right panel will show the JSON tool loop.
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
          turns.map((turn) => (
            <article className="turn" key={turn.id}>
              <div className="bubble user-bubble">
                <span>User</span>
                <p>{turn.user}</p>
              </div>
              <div className="bubble agent-bubble">
                <span>Agent final answer</span>
                <p>{turn.answer}</p>
              </div>
            </article>
          ))
        )}
      </div>

      {error ? <div className="error-line">{error}</div> : null}
      {lastAnswer ? <div className="last-answer">Latest: {lastAnswer}</div> : null}

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

