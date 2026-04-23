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

export type ChatRequest = {
  message: string;
  session_id?: string | null;
};

export type ChatResponse = {
  session_id: string;
  final_answer: string;
  trace: TraceStep[];
  messages: AgentMessage[];
};

export type ChatTurn = {
  id: string;
  user: string;
  answer: string;
};

