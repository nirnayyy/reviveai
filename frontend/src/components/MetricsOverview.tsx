import React from "react";
import type { MetricsOverview as MetricsType } from "../types";
import { TrendingUp, ShieldAlert } from "lucide-react";

interface Props {
  metrics: MetricsType;
}

export const MetricsOverview: React.FC<Props> = ({ metrics }) => {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Revenue at Risk</div>
        <div className="metric-value">₹{metrics.total_revenue_at_risk_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
        <div className="metric-footer">
          <span className="metric-subtext">{metrics.total_cases} total risk events captured</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Recovered Revenue</div>
        <div className="metric-value" style={{ color: "#059669" }}>
          ₹{metrics.total_recovered_revenue_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </div>
        <div className="metric-footer">
          <TrendingUp size={14} color="#10B981" />
          <span className="metric-lift">
            {metrics.recovery_rate_pct.toFixed(1)}% recovery rate
          </span>
          <span className="metric-subtext">(vs {metrics.baseline_recovery_rate_pct}% baseline)</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Net Revenue Lift</div>
        <div className="metric-value" style={{ color: "#2563EB" }}>
          +₹{metrics.net_revenue_lift_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </div>
        <div className="metric-footer">
          <span className="metric-subtext">After deducting direct action costs</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Active / Escalated</div>
        <div className="metric-value" style={{ color: metrics.escalated_cases > 0 ? "#D97706" : "#0C2340" }}>
          {metrics.active_cases} <span style={{ fontSize: "16px", color: "#64748B", fontWeight: 400 }}>/ {metrics.escalated_cases} escalated</span>
        </div>
        <div className="metric-footer">
          {metrics.escalated_cases > 0 ? (
            <span style={{ color: "#D97706", display: "flex", alignItems: "center", gap: "4px" }}>
              <ShieldAlert size={13} /> High-value/ambiguous human sign-off
            </span>
          ) : (
            <span className="metric-subtext">All bounded by safety policies</span>
          )}
        </div>
      </div>
    </div>
  );
};
