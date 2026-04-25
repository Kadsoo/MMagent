import type {
  ChatRequest,
  ChatResponse,
  ConversationDetail,
  ConversationSummary,
  ToolSpec
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function chat(payload: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getTools(): Promise<ToolSpec[]> {
  return request<ToolSpec[]>("/api/tools");
}

export function getConversations(userId: string): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>(
    `/api/conversations?user_id=${encodeURIComponent(userId)}`
  );
}

export function getConversationDetail(
  userId: string,
  sessionId: string
): Promise<ConversationDetail> {
  return request<ConversationDetail>(
    `/api/conversations/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(userId)}`
  );
}
