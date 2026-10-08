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
  semantic_similarity?: number;
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
  trace_id?: string;
  exploration_active?: boolean;
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
  input_tokens?: number;
  output_tokens?: number;
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

export interface Workspace {
  id: string;
  name: string;
  default_policy: string;
  rate_limit_rpm: number;
  created_at: string;
  is_active: boolean;
}

export interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  workspace_id: string;
  rate_limit_rpm: number;
  created_at: string;
  is_active: boolean;
  key?: string; // Only returned on creation
}

export interface BenchmarkCandidate {
  name: string;
  target_type: string;
  total_samples: number;
  correct_samples: number;
  accuracy_percent: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  avg_cost_per_1k_usd: number;
  total_cost_usd: number;
  accuracy_retention_percent: number;
  cost_savings_percent: number;
  latency_reduction_percent: number;
  is_pareto_optimal: boolean;
  model_breakdown?: Record<string, number>;
}

export interface BenchmarkReport {
  dataset_name: string;
  sample_count: number;
  baseline_model: string;
  candidates: BenchmarkCandidate[];
  pareto_frontier: string[];
  generated_at: string;
  ascii_graph: string;
}
