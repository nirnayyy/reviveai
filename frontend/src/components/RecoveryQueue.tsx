import React from "react";
import type { RecoveryCaseItem } from "../types";
import { Search, ArrowUpRight, AlertCircle, CheckCircle, Clock, ShieldX } from "lucide-react";

interface Props {
  cases: RecoveryCaseItem[];
  onSelectCase: (caseItem: RecoveryCaseItem) => void;
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

export const RecoveryQueue: React.FC<Props> = ({
  cases,
  onSelectCase,
  statusFilter,
  setStatusFilter,
  searchQuery,
  setSearchQuery,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RECOVERED":
        return <span className="badge badge-success"><CheckCircle size={11} /> Recovered</span>;
      case "ESCALATED":
        return <span className="badge badge-warning"><AlertCircle size={11} /> Escalated (Review)</span>;
      case "STOPPED":
        return <span className="badge badge-danger"><ShieldX size={11} /> Stopped (Safety)</span>;
      case "FAILED":
      case "POLICY_REJECTED":
        return <span className="badge badge-danger">Failed</span>;
      case "EXECUTING":
        return <span className="badge badge-info"><Clock size={11} /> Executing</span>;
      case "POLICY_APPROVED":
        return <span className="badge badge-info">Approved</span>;
      default:
        return <span className="badge badge-neutral">{status}</span>;
    }
  };

  const getFailureLabel = (cat: string) => {
    const map: Record<string, string> = {
      insufficient_funds: "Insufficient Funds",
      upi_mandate_failed: "UPI Mandate Failed",
      expired_payment_method: "Expired Card / Mandate",
      bank_decline_temporary: "Temporary Bank Downtime",
      bank_decline_hard: "Hard Bank Decline (Stolen)",
      auth_abandonment: "3DS Drop-off",
      subscription_halted: "Subscription Halted",
      unknown_ambiguous: "Unclassified Decline",
    };
    return map[cat] || cat;
  };

  const getActionLabel = (action: string | null) => {
    if (!action) return "Pending Evaluation";
    const map: Record<string, string> = {
      smart_timing_retry: "Smart Timing Retry",
      delayed_retry: "Delayed Retry",
      payment_method_update_request: "Request Card Update",
      customer_reminder_email: "Email Recovery Link",
      customer_reminder_whatsapp: "WhatsApp UPI Link",
      incentive_grace_period: "Grace Period Offer",
      escalate_to_human_review: "Escalate to Human",
      stop_recovery: "Stop Recovery",
    };
    return map[action] || action;
  };

  return (
    <div className="card">
      <div className="card-header">
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h2 className="card-title">Active Revenue Recovery Queue</h2>
          <span style={{ fontSize: "12px", color: "#64748B" }}>
            Sorted by Urgency & Expected Value
          </span>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <div style={{ position: "relative" }}>
            <Search size={14} style={{ position: "absolute", left: "10px", top: "10px", color: "#94A3B8" }} />
            <input
              type="text"
              placeholder="Search case or customer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: "6px 10px 6px 30px",
                borderRadius: "6px",
                border: "1px solid #CBD5E1",
                fontSize: "13px",
                width: "220px",
              }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: "6px 10px",
              borderRadius: "6px",
              border: "1px solid #CBD5E1",
              fontSize: "13px",
              background: "#FFFFFF",
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="DETECTED">Detected</option>
            <option value="POLICY_APPROVED">Policy Approved</option>
            <option value="EXECUTING">Executing</option>
            <option value="RECOVERED">Recovered</option>
            <option value="ESCALATED">Escalated</option>
            <option value="STOPPED">Stopped</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {cases.length === 0 ? (
        <div style={{ padding: "48px 20px", textAlign: "center", color: "#64748B" }}>
          <AlertCircle size={32} style={{ margin: "0 auto 12px", color: "#94A3B8" }} />
          <p style={{ fontWeight: 600, fontSize: "15px", color: "#0C2340" }}>No revenue recovery cases in this view</p>
          <p style={{ fontSize: "13px", marginTop: "4px" }}>
            Trigger a batch simulation from the top menu to populate realistic payment failure events.
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Case Number</th>
                <th>Customer</th>
                <th>Amount at Risk</th>
                <th>Diagnosis / Problem</th>
                <th>Recommended Action</th>
                <th>Expected Net EV</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} onClick={() => onSelectCase(c)}>
                  <td style={{ fontWeight: 600, color: "#0C2340" }}>{c.case_number}</td>
                  <td>
                    <div>{c.customer_name}</div>
                    <div style={{ fontSize: "11px", color: "#64748B" }}>{c.customer_email || c.customer_id}</div>
                  </td>
                  <td style={{ fontWeight: 700, color: "#0C2340" }}>
                    ₹{c.amount_at_risk_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td>
                    <span style={{ fontWeight: 500 }}>{getFailureLabel(c.failure_reason)}</span>
                    <div style={{ fontSize: "11px", color: "#64748B" }}>via {c.payment_method.toUpperCase()}</div>
                  </td>
                  <td style={{ color: "#0369A1", fontWeight: 600 }}>
                    {getActionLabel(c.recommended_action)}
                  </td>
                  <td style={{ fontWeight: 600, color: c.expected_recovery_value_inr > 0 ? "#059669" : "#64748B" }}>
                    {c.expected_recovery_value_inr > 0 ? `₹${c.expected_recovery_value_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "₹0.00"}
                  </td>
                  <td>
                    <span style={{ fontSize: "12px", fontWeight: 600 }}>
                      {Math.round(c.confidence_score * 100)}%
                    </span>
                  </td>
                  <td>{getStatusBadge(c.status)}</td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={(e) => { e.stopPropagation(); onSelectCase(c); }}>
                      Inspect <ArrowUpRight size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
