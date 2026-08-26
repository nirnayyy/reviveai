import React, { useState } from "react";
import type { RecoveryCaseDetail } from "../types";
import {
  X,
  CheckCircle,
  ShieldCheck,
  ShieldAlert,
  Info,
  Sparkles
} from "lucide-react";

interface Props {
  caseDetail: RecoveryCaseDetail;
  onClose: () => void;
  onOverrideAction: (action: string, timing: number, notes?: string) => Promise<void>;
}

export const CaseDetailModal: React.FC<Props> = ({
  caseDetail,
  onClose,
  onOverrideAction,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<"ai_policy" | "counterfactuals" | "timeline">("ai_policy");
  const [overrideAction, setOverrideAction] = useState<string>("smart_timing_retry");
  const [overrideNotes, setOverrideNotes] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const latestAI = caseDetail.ai_decisions[caseDetail.ai_decisions.length - 1];
  const latestPolicy = caseDetail.policy_decisions[caseDetail.policy_decisions.length - 1];

  const handleApplyOverride = async () => {
    setIsSubmitting(true);
    try {
      await onOverrideAction(overrideAction, 0, overrideNotes);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#0C2340" }}>
                {caseDetail.case_number}
              </h2>
              <span className="badge badge-info">{caseDetail.status}</span>
              <span className="badge badge-neutral">{caseDetail.recovery_mode}</span>
            </div>
            <p style={{ fontSize: "12px", color: "#64748B", marginTop: "2px" }}>
              Customer: {caseDetail.customer_name} ({caseDetail.customer_email || caseDetail.customer_id}) • LTV: ₹{caseDetail.customer_ltv_inr.toLocaleString("en-IN")}
            </p>
          </div>

          <button
            onClick={onClose}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#64748B" }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Sub-Tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid #E2E8F0", padding: "0 24px", background: "#F8FAFC" }}>
          <button
            style={{
              padding: "10px 16px",
              border: "none",
              background: "none",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              borderBottom: activeSubTab === "ai_policy" ? "2px solid #3395FF" : "none",
              color: activeSubTab === "ai_policy" ? "#0C2340" : "#64748B"
            }}
            onClick={() => setActiveSubTab("ai_policy")}
          >
            Diagnosis & Policy Authorization
          </button>

          <button
            style={{
              padding: "10px 16px",
              border: "none",
              background: "none",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              borderBottom: activeSubTab === "counterfactuals" ? "2px solid #3395FF" : "none",
              color: activeSubTab === "counterfactuals" ? "#0C2340" : "#64748B"
            }}
            onClick={() => setActiveSubTab("counterfactuals")}
          >
            Counterfactual Value Matrix
          </button>

          <button
            style={{
              padding: "10px 16px",
              border: "none",
              background: "none",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              borderBottom: activeSubTab === "timeline" ? "2px solid #3395FF" : "none",
              color: activeSubTab === "timeline" ? "#0C2340" : "#64748B"
            }}
            onClick={() => setActiveSubTab("timeline")}
          >
            Action Timeline & Outcomes
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Top Quick Bar */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", background: "#F1F5F9", padding: "12px 16px", borderRadius: "8px" }}>
            <div>
              <div style={{ fontSize: "11px", color: "#64748B", textTransform: "uppercase" }}>Amount at Risk</div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "#0C2340" }}>
                ₹{caseDetail.amount_at_risk_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <div style={{ fontSize: "11px", color: "#64748B", textTransform: "uppercase" }}>Payment Method</div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "#0C2340" }}>
                {caseDetail.payment_method.toUpperCase()}
              </div>
            </div>

            <div>
              <div style={{ fontSize: "11px", color: "#64748B", textTransform: "uppercase" }}>Expected Recovery</div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "#059669" }}>
                ₹{caseDetail.expected_recovery_value_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <div style={{ fontSize: "11px", color: "#64748B", textTransform: "uppercase" }}>Consecutive Retries</div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: caseDetail.retry_count >= 3 ? "#DC2626" : "#0C2340" }}>
                {caseDetail.retry_count} / 3 Max
              </div>
            </div>
          </div>

          {activeSubTab === "ai_policy" && (
            <>
              {/* 1. Fact / Inference / Unknown Breakdown */}
              {latestAI && (
                <div>
                  <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#0C2340", marginBottom: "8px" }}>
                    EPISTEMIC DIAGNOSIS: KNOWN FACTS VS. INFERENCES VS. UNKNOWNS
                  </h3>
                  <div className="reasoning-breakdown-grid">
                    <div className="reasoning-col facts">
                      <div className="reasoning-col-title">
                        <CheckCircle size={12} /> Known Data Facts
                      </div>
                      <ul className="reasoning-list">
                        {latestAI.known_facts.map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="reasoning-col inferences">
                      <div className="reasoning-col-title">
                        <Sparkles size={12} /> Contextual Inferences
                      </div>
                      <ul className="reasoning-list">
                        {latestAI.inferred_factors.map((inf, i) => (
                          <li key={i}>{inf}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="reasoning-col unknowns">
                      <div className="reasoning-col-title">
                        <Info size={12} /> Unobservable Unknowns
                      </div>
                      <ul className="reasoning-list">
                        {latestAI.unknown_factors.map((u, i) => (
                          <li key={i}>{u}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* 2. AI Recommendation */}
              {latestAI && (
                <div style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "8px", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#1E40AF", fontWeight: 700, fontSize: "13px" }}>
                      <Sparkles size={14} />
                      AI RECOVERY AGENT PROPOSAL ({latestAI.model_name})
                    </div>
                    <span style={{ fontSize: "12px", color: "#1E40AF", fontWeight: 600 }}>
                      Estimated P(Recovery): {(latestAI.expected_recovery_probability * 100).toFixed(0)}% • Confidence: {(latestAI.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div style={{ fontSize: "14px", fontWeight: 700, color: "#0C2340", marginBottom: "4px" }}>
                    Recommended Action: <span style={{ color: "#2563EB" }}>{latestAI.recommended_action}</span> (Delay: {latestAI.timing_schedule_minutes} mins)
                  </div>
                  <p style={{ fontSize: "13px", color: "#334155", lineHeight: 1.4 }}>
                    {latestAI.reasoning_summary}
                  </p>
                </div>
              )}

              {/* 3. Policy & Safety Engine */}
              {latestPolicy && (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#0C2340" }}>
                      DETERMINISTIC SAFETY & POLICY AUTHORIZATION
                    </h3>
                    <span className={`badge ${latestPolicy.is_authorized ? "badge-success" : "badge-warning"}`}>
                      {latestPolicy.is_authorized ? "POLICY AUTHORIZED" : (latestPolicy.requires_human_review ? "HELD FOR HUMAN REVIEW" : "STOPPED BY POLICY")}
                    </span>
                  </div>

                  <div className="policy-checklist">
                    {latestPolicy.rule_evaluations.map((r, idx) => (
                      <div key={idx} className={`policy-item ${r.passed ? "passed" : "failed"}`}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          {r.passed ? <ShieldCheck size={16} color="#10B981" /> : <ShieldAlert size={16} color="#EF4444" />}
                          <div>
                            <span style={{ fontWeight: 600, color: "#0C2340" }}>{r.rule_name}</span>
                            <div style={{ fontSize: "11px", color: "#64748B" }}>{r.reason}</div>
                          </div>
                        </div>
                        <span style={{ fontSize: "11px", fontWeight: 600, color: r.passed ? "#059669" : "#DC2626" }}>
                          {r.passed ? "PASS" : "FAIL / HOLD"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {activeSubTab === "counterfactuals" && latestAI && (
            <div>
              <div style={{ marginBottom: "12px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#0C2340" }}>
                  Candidate Action Counterfactual Matrix
                </h3>
                <p style={{ fontSize: "12px", color: "#64748B" }}>
                  Expected Value = P(Recovery) × ₹{caseDetail.amount_at_risk_inr.toLocaleString("en-IN")} − Action Cost − Friction Penalty
                </p>
              </div>

              <div className="table-container">
                <table className="counterfactual-table">
                  <thead>
                    <tr>
                      <th>Candidate Intervention</th>
                      <th>Recovery Prob</th>
                      <th>Gross Value</th>
                      <th>Direct Cost</th>
                      <th>Friction Penalty</th>
                      <th>Net Expected Value</th>
                      <th>Trade-off Assessment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestAI.counterfactuals.map((cf, idx) => {
                      const isSelected = cf.action_name === latestAI.recommended_action;
                      return (
                        <tr key={idx} className={isSelected ? "selected" : ""}>
                          <td>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              {isSelected && <span className="badge badge-success" style={{ fontSize: "10px", padding: "1px 4px" }}>OPTIMAL</span>}
                              <span>{cf.action_name}</span>
                            </div>
                          </td>
                          <td>{(cf.recovery_probability * 100).toFixed(1)}%</td>
                          <td>₹{cf.expected_recovered_inr.toFixed(2)}</td>
                          <td style={{ color: "#DC2626" }}>-₹{cf.intervention_cost_inr.toFixed(2)}</td>
                          <td style={{ color: "#D97706" }}>-₹{cf.friction_penalty_inr.toFixed(2)}</td>
                          <td style={{ fontWeight: 700, color: cf.expected_net_value_inr > 0 ? "#059669" : "#DC2626" }}>
                            ₹{cf.expected_net_value_inr.toFixed(2)}
                          </td>
                          <td style={{ fontSize: "11px", color: "#475569", maxWidth: "250px" }}>
                            {cf.tradeoff_summary}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeSubTab === "timeline" && (
            <div>
              <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#0C2340", marginBottom: "12px" }}>
                Interventions & Recovery Outcomes
              </h3>

              {caseDetail.actions.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#64748B" }}>
                  No actions executed yet for this case.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {caseDetail.actions.map((act, i) => (
                    <div key={i} style={{ border: "1px solid #E2E8F0", borderRadius: "6px", padding: "12px", background: "#F8FAFC" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: 600, color: "#0C2340" }}>{act.action_type}</span>
                        <span className={`badge ${act.status === "SUCCEEDED" ? "badge-success" : "badge-warning"}`}>
                          {act.status}
                        </span>
                      </div>
                      <div style={{ fontSize: "12px", color: "#64748B", marginTop: "4px" }}>
                        Scheduled: {new Date(act.scheduled_for).toLocaleTimeString()} • Cost: ₹{act.cost_inr.toFixed(2)} • Mode: {act.execution_mode}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Manual Operator Actions */}
          <div style={{ borderTop: "1px solid #E2E8F0", paddingTop: "16px" }}>
            <h4 style={{ fontSize: "13px", fontWeight: 700, color: "#0C2340", marginBottom: "8px" }}>
              Merchant Operator Actions
            </h4>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <select
                value={overrideAction}
                onChange={(e) => setOverrideAction(e.target.value)}
                style={{ padding: "6px 10px", borderRadius: "6px", border: "1px solid #CBD5E1", fontSize: "13px" }}
              >
                <option value="smart_timing_retry">Smart Timing Retry (Next Morning)</option>
                <option value="delayed_retry">Delayed Gateway Retry (Immediate/3h)</option>
                <option value="payment_method_update_request">Request Payment Method Update (Link)</option>
                <option value="customer_reminder_email">Send Email Recovery Link</option>
                <option value="customer_reminder_whatsapp">Send WhatsApp 1-Tap UPI Link</option>
                <option value="stop_recovery">Stop Recovery (Cancel)</option>
              </select>

              <input
                type="text"
                placeholder="Optional operator override notes..."
                value={overrideNotes}
                onChange={(e) => setOverrideNotes(e.target.value)}
                style={{ flex: 1, padding: "6px 10px", borderRadius: "6px", border: "1px solid #CBD5E1", fontSize: "13px" }}
              />

              <button
                className="btn btn-primary"
                onClick={handleApplyOverride}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Executing..." : "Apply Operator Action"}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
