export type Role = 'system' | 'user' | 'assistant';

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd?: number;
}

export interface ChatCompletionChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string;
}

export interface ChatCompletion {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: ChatCompletionChoice[];
  usage: Usage;
  routing_metadata?: Record<string, any>;
}

export interface ChatCompletionChunkDelta {
  role?: Role;
  content?: string;
}

export interface ChatCompletionChunkChoice {
  index: number;
  delta: ChatCompletionChunkDelta;
  finish_reason?: string | null;
}

export interface ChatCompletionChunk {
  id: string;
  object: 'chat.completion.chunk';
  created: number;
  model: string;
  choices: ChatCompletionChunkChoice[];
  routing_metadata?: Record<string, any>;
}

export interface RoutingDecision {
  decision_id: string;
  request_id: string;
  selected_model: string;
  selected_model_name: string;
  provider: string;
  tier: string;
  confidence: number;
  policy_used: string;
  reasons: string[];
  estimated_cost_usd: number;
  estimated_latency_ms: number;
  rejected_candidates?: Record<string, string>;
  rule_applied?: string | null;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  tier: string;
  context_window: number;
  quality_score: number;
  speed_score: number;
  cost_per_input_token: number;
  cost_per_output_token: number;
  is_active: boolean;
}

export interface ModelRouterOptions {
  apiKey?: string;
  baseUrl?: string;
  policy?: 'balanced' | 'cost_optimized' | 'speed_optimized' | 'quality_first' | string;
  workspaceId?: string;
  timeoutMs?: number;
  fetch?: typeof fetch;
}

export interface ChatCompletionCreateParams {
  messages?: ChatMessage[];
  prompt?: string;
  policy?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  headers?: Record<string, string>;
}
