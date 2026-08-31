export type TaskType = 
  | 'GENERAL_QA'
  | 'CODING'
  | 'DEBUGGING'
  | 'REASONING'
  | 'SUMMARIZATION'
  | 'EXTRACTION'
  | 'WRITING'
  | 'TRANSLATION'
  | 'ANALYSIS'
  | 'MATH'
  | 'LONG_CONTEXT'
  | 'CREATIVE';

export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type ModelTier = 'FAST' | 'BALANCED' | 'POWER';

export interface RequestAnalysis {
  task_type: TaskType;
  complexity: number;
  complexity_label: PriorityLevel;
  reasoning_required: boolean;
  coding_required: boolean;
  vision_required: boolean;
  tools_required: boolean;
  context_size: number;
  latency_priority: PriorityLevel;
  cost_sensitivity: PriorityLevel;
  quality_requirement: PriorityLevel;
  keywords_detected: string[];
  analyzer_used: string;
}

export interface CandidateScore {
  model_id: string;
  model_name: string;
  provider: string;
  tier: string;
  overall_score: number;
  quality_component: number;
  cost_component: number;
  speed_component: number;
  capability_component: number;
  reliability_component: number;
  estimated_latency_ms: number;
  estimated_cost_usd: number;
  eligible: boolean;
  rejection_reason?: string;
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
  candidate_scores: CandidateScore[];
  rejected_candidates: Record<string, string>;
  estimated_cost_usd: number;
  estimated_latency_ms: number;
  rule_applied?: string;
  timestamp: string;
}

export interface ProviderResponse {
  content: string;
  finish_reason: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  provider_latency_ms: number;
  time_to_first_token_ms?: number;
  is_mock: boolean;
  model: string;
  provider: string;
  error?: string;
}

export interface ModelRecord {
  id: string;
  name: string;
  provider: string;
  type: string;
  tier: ModelTier;
  context_window: number;
  supports_coding: boolean;
  supports_reasoning: boolean;
  supports_vision: boolean;
  supports_tools: boolean;
  quality_score: number;
  speed_score: number;
  reliability_score: number;
  cost_per_input_token: number;
  cost_per_output_token: number;
  availability: string;
  is_active: boolean;
}

export interface ProviderInfo {
  id: string;
  name: string;
  status: string;
  base_url?: string;
  message?: string;
  models_available: string[];
  credentials_status: string;
}

export interface TrafficItem {
  request_id: string;
  timestamp: string;
  prompt: string;
  task_type: TaskType;
  complexity: number;
  selected_model: string;
  provider: string;
  status: string;
  total_latency_ms: number;
  estimated_cost: number;
}

export interface SystemAnalytics {
  total_requests: number;
  avg_latency_ms: number;
  avg_routing_latency_ms: number;
  avg_cost_usd: number;
  total_cost_usd: number;
  quality_score_percent?: number;
  fallback_rate_percent: number;
  fallback_count: number;
  model_distribution: Record<string, number>;
  task_distribution: Record<string, number>;
  savings: {
    baseline_model: string;
    total_requests: number;
    baseline_total_cost: number;
    routed_total_cost: number;
    cost_saved_usd: number;
    savings_percentage: number;
  };
}

export interface RoutingRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  is_enabled: boolean;
  condition_field: string;
  condition_operator: string;
  condition_value: string;
  action_type: string;
  action_target: string;
}
