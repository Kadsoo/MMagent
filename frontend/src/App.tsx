import { useEffect, useMemo, useRef, useState } from "react";
import { HashRouter, NavLink, Route, Routes } from "react-router-dom";
import ChatPanel from "./components/ChatPanel";
import ToolsPanel from "./components/ToolsPanel";
import TracePanel from "./components/TracePanel";
import { useTools } from "./hooks/useTools";
import {
  chat,
  getConversationDetail,
  getConversations,
  renameConversation
} from "./services/api";
import type {
  ConversationDetail,
  ConversationSummary
} from "./types/api";

const starterPrompts = [
  "What's the weather and current time in Nanjing?",
  "Calculate (18 + 24) / 3 and explain the result.",
  "Search docs for RAG design in MMagent.",
  "Web search: FastAPI background tasks",
  "Add todo: prepare MMagent demo for interview",
  "List todos"
];

const USER_ID_STORAGE_KEY = "mmagent-user-id";
type ConversationMode = "new" | "existing";

export default function App() {
  const [userId, setUserId] = useState(loadOrCreateUserId);
  const [draftUserId, setDraftUserId] = useState(userId);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationMode, setConversationMode] = useState<ConversationMode>("new");
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [selectedRunIndex, setSelectedRunIndex] = useState<number>(-1);
  const [conversationTitleDraft, setConversationTitleDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { tools, loading: toolsLoading, error: toolsError } = useTools();
  const conversationRequestRef = useRef(0);
  const userIdRef = useRef(userId);
  const displayConversation = conversationMode === "existing" ? activeConversation : null;
  const conversationStatus = useMemo(() => {
    if (historyLoading) {
      return {
        label: "Status",
        value: "Loading conversation history..."
      };
    }
    if (displayConversation) {
      return {
        label: "Active",
        value: displayConversation.title
      };
    }
    return {
      label: "Status",
      value: "Pick a saved conversation or start a fresh one."
    };
  }, [displayConversation, historyLoading]);

  const selectedRun = useMemo(() => {
    if (!displayConversation || displayConversation.runs.length === 0) {
      return null;
    }
    if (selectedRunIndex >= 0 && selectedRunIndex < displayConversation.runs.length) {
      return displayConversation.runs[selectedRunIndex];
    }
    return displayConversation.runs[displayConversation.runs.length - 1];
  }, [displayConversation, selectedRunIndex]);

  useEffect(() => {
    userIdRef.current = userId;
  }, [userId]);

  useEffect(() => {
    window.localStorage.setItem(USER_ID_STORAGE_KEY, userId);
    void refreshConversations(userId, null);
  }, [userId]);

  useEffect(() => {
    if (!displayConversation || displayConversation.runs.length === 0) {
      setSelectedRunIndex(-1);
      return;
    }
    setSelectedRunIndex(displayConversation.runs.length - 1);
  }, [displayConversation?.session_id, displayConversation?.runs.length]);

  useEffect(() => {
    setConversationTitleDraft(displayConversation?.title ?? "");
  }, [displayConversation?.session_id, displayConversation?.title]);

  async function refreshConversations(
    targetUserId: string,
    preferredSessionId: string | null
  ) {
    const requestId = ++conversationRequestRef.current;
    setHistoryLoading(true);
    try {
      const list = await getConversations(targetUserId);
      if (requestId !== conversationRequestRef.current || targetUserId !== userIdRef.current) {
        return;
      }
      setConversations(list);

      if (!preferredSessionId) {
        setConversationMode("new");
        setActiveSessionId(null);
        setActiveConversation(null);
        return;
      }

      const detail = await getConversationDetail(targetUserId, preferredSessionId);
      if (requestId !== conversationRequestRef.current || targetUserId !== userIdRef.current) {
        return;
      }
      setConversationMode("existing");
      setActiveSessionId(detail.session_id);
      setActiveConversation(detail);
    } catch (err) {
      if (requestId !== conversationRequestRef.current) {
        return;
      }
      setConversationMode("new");
      setError(err instanceof Error ? err.message : "Failed to load conversations");
      setActiveSessionId(null);
      setActiveConversation(null);
    } finally {
      if (requestId === conversationRequestRef.current) {
        setHistoryLoading(false);
      }
    }
  }

  async function openConversation(sessionId: string, targetUserId = userId) {
    const requestId = ++conversationRequestRef.current;
    setHistoryLoading(true);
    setError(null);
    try {
      const detail = await getConversationDetail(targetUserId, sessionId);
      if (requestId !== conversationRequestRef.current || targetUserId !== userIdRef.current) {
        return;
      }
      setConversationMode("existing");
      setActiveSessionId(detail.session_id);
      setActiveConversation(detail);
    } catch (err) {
      if (requestId !== conversationRequestRef.current) {
        return;
      }
      setConversationMode("new");
      setActiveSessionId(null);
      setActiveConversation(null);
      setError(err instanceof Error ? err.message : "Failed to load conversation");
    } finally {
      if (requestId === conversationRequestRef.current) {
        setHistoryLoading(false);
      }
    }
  }

  async function handleSend(message: string) {
    setLoading(true);
    setPendingUserMessage(message);
    setError(null);
    try {
      const response = await chat({
        message,
        user_id: userId,
        session_id: conversationMode === "existing" ? activeSessionId : null
      });
      setConversationMode("existing");
      setActiveSessionId(response.session_id);
      await refreshConversations(userId, response.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
      setPendingUserMessage(null);
    }
  }

  async function handleRenameConversation() {
    if (!activeSessionId || conversationMode !== "existing") {
      return;
    }
    const cleanTitle = conversationTitleDraft.trim();
    if (!cleanTitle || cleanTitle === displayConversation?.title) {
      return;
    }
    setError(null);
    try {
      const detail = await renameConversation(activeSessionId, {
        user_id: userId,
        title: cleanTitle
      });
      setActiveConversation(detail);
      await refreshConversations(userId, detail.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rename conversation");
    }
  }

  function handleCreateConversation() {
    conversationRequestRef.current += 1;
    setConversationMode("new");
    setActiveSessionId(null);
    setActiveConversation(null);
    setSelectedRunIndex(-1);
    setHistoryLoading(false);
    setError(null);
    if (window.location.hash !== "#/") {
      window.location.hash = "#/";
    }
  }

  function handleApplyUserId() {
    const clean = draftUserId.trim();
    if (!clean || clean === userId) {
      return;
    }
    conversationRequestRef.current += 1;
    setConversationMode("new");
    setActiveSessionId(null);
    setActiveConversation(null);
    setSelectedRunIndex(-1);
    setConversations([]);
    setHistoryLoading(true);
    setError(null);
    setUserId(clean);
  }

  return (
    <HashRouter>
      <main className="app-shell">
        <aside className="app-sidebar">
          <div className="brand-block">
            <p className="eyebrow">JSON Tool Calling</p>
            <h1>MMagent</h1>
          </div>

          <nav className="nav-strip" aria-label="Primary">
            <NavLink to="/" end className={navClassName}>
              Home
            </NavLink>
            <NavLink to="/trace" className={navClassName}>
              Trace
            </NavLink>
            <NavLink to="/tools" className={navClassName}>
              Tools
            </NavLink>
          </nav>

          <section className="control-stack">
            <div className="control-card">
              <div className="control-header">
                <span>User ID</span>
                <strong>{userId}</strong>
              </div>
              <div className="inline-form">
                <input
                  value={draftUserId}
                  onChange={(event) => setDraftUserId(event.target.value)}
                  placeholder="Enter a user id"
                />
                <button type="button" className="secondary-button" onClick={handleApplyUserId}>
                  确定
                </button>
              </div>
              <p className="helper-note">请注册新id或使用已有id。</p>
            </div>

            <div className="control-card">
              <div className="control-header">
                <span>Conversation</span>
                <strong>{conversations.length}</strong>
              </div>
              <div className="inline-form">
                <select
                  className="conversation-select"
                  value={activeSessionId ?? ""}
                  onChange={(event) => {
                    const nextSessionId = event.target.value;
                    if (!nextSessionId) {
                      handleCreateConversation();
                      return;
                    }
                    void openConversation(nextSessionId);
                  }}
                >
                  <option value="">Start a new conversation</option>
                  {conversations.map((conversation) => (
                    <option key={conversation.session_id} value={conversation.session_id}>
                      {conversation.title}
                    </option>
                  ))}
                </select>
                <button type="button" className="primary-button" onClick={handleCreateConversation}>
                  New
                </button>
              </div>
              {displayConversation ? (
                <div className="rename-form">
                  <input
                    value={conversationTitleDraft}
                    onChange={(event) => setConversationTitleDraft(event.target.value)}
                    placeholder="Conversation name"
                    maxLength={80}
                  />
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={handleRenameConversation}
                  >
                    Rename
                  </button>
                </div>
              ) : null}
              <p className="control-note" aria-live="polite">
                <span className="control-note-label">{conversationStatus.label}</span>
                <span className="control-note-value">{conversationStatus.value}</span>
              </p>
            </div>
          </section>
        </aside>

        <section className="app-content">
          <Routes>
            <Route
              path="/"
              element={
                <section className="page-container">
                  <ChatPanel
                    key={conversationMode === "new" ? "new-conversation" : activeSessionId ?? "active"}
                    runs={displayConversation?.runs ?? []}
                    loading={loading}
                    historyLoading={historyLoading}
                    pendingUserMessage={pendingUserMessage}
                    error={error}
                    starterPrompts={starterPrompts}
                    onSend={handleSend}
                    sessionTitle={displayConversation?.title ?? "New Conversation"}
                    userId={userId}
                  />
                </section>
              }
            />
            <Route
              path="/trace"
              element={
                <section className="page-container trace-layout">
                  <section className="panel run-list-panel">
                    <div className="panel-heading">
                      <h2>Stored Runs</h2>
                      <span>{displayConversation?.runs.length ?? 0} runs</span>
                    </div>
                    {!displayConversation || displayConversation.runs.length === 0 ? (
                      <p className="muted">
                        Select a conversation with at least one completed request to inspect its trace.
                      </p>
                    ) : (
                      <div className="run-list">
                        {displayConversation.runs.map((run, index) => (
                          <button
                            key={`${run.id ?? index}-${run.created_at}`}
                            type="button"
                            className={
                              index === selectedRunIndex
                                ? "run-list-item run-list-item-active"
                                : "run-list-item"
                            }
                            onClick={() => setSelectedRunIndex(index)}
                          >
                            <strong>{run.user_input}</strong>
                            <span>{formatDate(run.created_at)}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </section>
                  <TracePanel
                    trace={selectedRun?.trace ?? []}
                    title={selectedRun ? selectedRun.user_input : "Execution Trace"}
                  />
                </section>
              }
            />
            <Route
              path="/tools"
              element={
                <section className="page-container">
                  <ToolsPanel tools={tools} loading={toolsLoading} error={toolsError} />
                </section>
              }
            />
          </Routes>
        </section>
      </main>
    </HashRouter>
  );
}

function navClassName({ isActive }: { isActive: boolean }) {
  return isActive ? "nav-link nav-link-active" : "nav-link";
}

function loadOrCreateUserId() {
  const stored = window.localStorage.getItem(USER_ID_STORAGE_KEY);
  if (stored) {
    return stored;
  }
  const generated = `user-${Math.random().toString(36).slice(2, 8)}`;
  window.localStorage.setItem(USER_ID_STORAGE_KEY, generated);
  return generated;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}
