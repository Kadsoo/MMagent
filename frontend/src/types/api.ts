export type AgentMessage = {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string | null;
};

export type ToolCall = {
  type: "tool_call";
  tool_name: string;
  arguments: Record<string, unknown>;
  thought?: string | null;
};

export type ToolResult = {
  type: "tool_result";
  tool_name: string;
  status: "success" | "error";
  result?: unknown;
  error?: string | null;
};

export type FinalAnswer = {
  type: "final_answer";
  answer: string;
};

export type TraceStep = {
  step: number;
  model_output?: string | null;
  parsed_output?: Record<string, unknown> | null;
  tool_call?: ToolCall | null;
  tool_result?: ToolResult | null;
  final_answer?: FinalAnswer | null;
  error?: string | null;
};

export type ToolSpec = {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
};

export type ConversationRun = {
  id?: number | null;
  user_input: string;
  final_answer: string;
  trace: TraceStep[];
  created_at: string;
};

export type ConversationSummary = {
  session_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_message_preview?: string | null;
};

export type ConversationDetail = ConversationSummary & {
  messages: AgentMessage[];
  runs: ConversationRun[];
};

export type ChatRequest = {
  message: string;
  user_id: string;
  session_id?: string | null;
};

export type ChatResponse = {
  session_id: string;
  user_id: string;
  final_answer: string;
  trace: TraceStep[];
  messages: AgentMessage[];
  runs: ConversationRun[];
};

export type ConversationRenameRequest = {
  user_id: string;
  title: string;
};
