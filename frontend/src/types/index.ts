export interface CounterfactualEvaluation {
  action_name: string;
  recovery_probability: number;
  expected_recovered_inr: number;
  intervention_cost_inr: number;
  friction_penalty_inr: number;
  expected_net_value_inr: number;
  tradeoff_summary: string;
}

export interface AIDecisionSummary {
  id: string;
  model_name: string;
  diagnosis_category: string;
  diagnosis_reasoning: string;
  recommended_action: string;
  timing_schedule_minutes: number;
  expected_recovery_probability: number;
  confidence_score: number;
  reasoning_summary: string;
  known_facts: string[];
  inferred_factors: string[];
  unknown_factors: string[];
  counterfactuals: CounterfactualEvaluation[];
  requires_human_review: boolean;
  is_fallback: boolean;
  created_at: string;
}

export interface RuleEvaluation {
  rule_name: string;
  passed: boolean;
  reason: string;
  details?: Record<string, any>;
}

export interface PolicyDecisionSummary {
  id: string;
  is_authorized: boolean;
  action_approved: string | null;
  stopping_rule_triggered: string | null;
  rejection_reasons: string[];
  rule_evaluations: RuleEvaluation[];
  requires_human_review: boolean;
  created_at: string;
}

export interface ActionSummary {
  id: string;
  action_type: string;
  status: string;
  scheduled_for: string;
  executed_at: string | null;
  cost_inr: number;
  friction_penalty: number;
  execution_mode: string;
}

export interface RecoveryCaseItem {
  id: string;
  case_number: string;
  customer_id: string;
  customer_name: string;
  customer_email: string | null;
  payment_id: string | null;
  subscription_id: string | null;
  amount_at_risk_inr: number;
  customer_ltv_inr: number;
  urgency_score: number;
  risk_age_hours: number;
  failure_reason: string;
  error_code: string | null;
  payment_method: string;
  status: string;
  retry_count: number;
  expected_recovery_probability: number;
  expected_recovery_value_inr: number;
  confidence_score: number;
  recommended_action: string | null;
  recovery_mode: string;
  created_at: string;
}

export interface RecoveryCaseDetail extends RecoveryCaseItem {
  error_description: string | null;
  contact_count: number;
  last_action_timestamp: string | null;
  resolved_at: string | null;
  ai_decisions: AIDecisionSummary[];
  policy_decisions: PolicyDecisionSummary[];
  actions: ActionSummary[];
}

export interface MetricsOverview {
  total_cases: number;
  active_cases: number;
  recovered_cases: number;
  failed_cases: number;
  escalated_cases: number;
  stopped_cases: number;
  total_revenue_at_risk_inr: number;
  total_recovered_revenue_inr: number;
  recovery_rate_pct: number;
  baseline_recovery_rate_pct: number;
  net_revenue_lift_inr: number;
  avg_confidence_score: number;
  prevented_friction_events_count: number;
  total_intervention_cost_inr: number;
}

export interface AuditLogItem {
  id: string;
  case_id: string | null;
  actor: string;
  action_type: string;
  message: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface EvaluationScenarioData {
  total_events: number;
  risk_amount_inr: number;
  baseline_recovered_count: number;
  baseline_recovery_rate_pct: number;
  reviveai_recovered_count: number;
  reviveai_recovery_rate_pct: number;
  reviveai_recovered_inr: number;
  recovery_lift_pct: number;
}

export interface EvaluationReport {
  metadata: {
    evaluation_timestamp: string;
    dataset_size: number;
    execution_time_seconds: number;
  };
  summary: {
    total_revenue_at_risk_inr: number;
    baseline: {
      recovered_count: number;
      recovery_rate_pct: number;
      recovered_amount_inr: number;
      total_cost_inr: number;
      total_friction_inr: number;
      avg_attempts: number;
    };
    reviveai: {
      recovered_count: number;
      recovery_rate_pct: number;
      recovered_amount_inr: number;
      total_cost_inr: number;
      total_friction_inr: number;
      avg_attempts: number;
      policy_rejections_count: number;
      hard_declines_stopped_count: number;
      human_escalations_count: number;
    };
    uplift: {
      recovery_rate_lift_pct: number;
      recovered_revenue_lift_inr: number;
      net_economic_lift_inr: number;
    };
  };
  scenario_breakdown: Record<string, EvaluationScenarioData>;
  failure_analysis: {
    unrecoverable_cases: number;
    policy_rejected_actions: number;
    human_escalated_cases: number;
    hard_declines_intercepted: number;
    explanation: string;
  };
}
