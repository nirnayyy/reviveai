import React, { useEffect, useState } from "react";
import type { EvaluationReport } from "../types";
import { fetchEvaluationReport, runLiveEvaluation } from "../services/api";
import { RefreshCw } from "lucide-react";

export const EvaluationView: React.FC = () => {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRunningEval, setIsRunningEval] = useState<boolean>(false);

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await fetchEvaluationReport();
      setReport(data);
    } catch (e) {
      console.error("Failed to load evaluation report:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  const handleReRun = async () => {
    setIsRunningEval(true);
    try {
      const data = await runLiveEvaluation(10000);
      setReport(data.results);
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningEval(false);
    }
  };

  if (loading || !report) {
    return (
      <div className="card" style={{ padding: "48px", textAlign: "center" }}>
        <RefreshCw size={24} className="spin" style={{ margin: "0 auto 12px", color: "#3395FF" }} />
        <p>Loading 10,000-event benchmark evaluation data...</p>
      </div>
    );
  }

  const { summary, scenario_breakdown, failure_analysis } = report;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Benchmark Header */}
      <div className="card">
        <div className="card-header" style={{ marginBottom: 0, paddingBottom: 0, border: "none" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h2 className="card-title" style={{ fontSize: "18px" }}>
                ReviveAI Empirical Benchmark (10,000 Payment Events)
              </h2>
              <span className="badge badge-success">Reproducible Evaluation</span>
            </div>
            <p style={{ fontSize: "13px", color: "#64748B", marginTop: "4px" }}>
              Comparing Baseline (Fixed 24h Naive Retry) against ReviveAI Adaptive Decision Agent across realistic failure scenarios.
            </p>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={handleReRun}
            disabled={isRunningEval}
          >
            <RefreshCw size={13} className={isRunningEval ? "spin" : ""} />
            {isRunningEval ? "Evaluating 10k Events..." : "Re-run 10k Benchmark"}
          </button>
        </div>
      </div>

      {/* Summary KPI Lift Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Recovery Rate Lift</div>
          <div className="metric-value" style={{ color: "#059669" }}>
            +{summary.uplift.recovery_rate_lift_pct.toFixed(1)}%
          </div>
          <div className="metric-footer">
            <span className="metric-subtext">
              {summary.reviveai.recovery_rate_pct.toFixed(1)}% (ReviveAI) vs {summary.baseline.recovery_rate_pct.toFixed(1)}% (Baseline)
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Recovered Revenue Lift</div>
          <div className="metric-value" style={{ color: "#2563EB" }}>
            +₹{summary.uplift.recovered_revenue_lift_inr.toLocaleString("en-IN", { minimumFractionDigits: 0 })}
          </div>
          <div className="metric-footer">
            <span className="metric-subtext">
              ₹{summary.reviveai.recovered_amount_inr.toLocaleString("en-IN")} total recovered
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Intervention Cost Saved</div>
          <div className="metric-value" style={{ color: "#059669" }}>
            ₹{(summary.baseline.total_cost_inr - summary.reviveai.total_cost_inr).toLocaleString("en-IN")}
          </div>
          <div className="metric-footer">
            <span className="metric-subtext">
              Saved by preventing blind futile retries
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Net Economic Benefit</div>
          <div className="metric-value" style={{ color: "#0C2340" }}>
            +₹{summary.uplift.net_economic_lift_inr.toLocaleString("en-IN", { minimumFractionDigits: 0 })}
          </div>
          <div className="metric-footer">
            <span className="metric-subtext">
              Revenue lift minus costs and friction
            </span>
          </div>
        </div>
      </div>

      {/* Side by Side Comparison Table */}
      <div className="card">
        <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#0C2340", marginBottom: "12px" }}>
          Head-to-Head Comparative Summary
        </h3>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Benchmark Metric</th>
                <th>Baseline (Fixed Naive Retry)</th>
                <th>ReviveAI (Adaptive Agent)</th>
                <th>Engineering Difference / Lift</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Total Revenue at Risk</strong></td>
                <td>₹{summary.total_revenue_at_risk_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                <td>₹{summary.total_revenue_at_risk_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                <td>Identical 10k Test Split</td>
              </tr>
              <tr>
                <td><strong>Recovered Payment Events</strong></td>
                <td>{summary.baseline.recovered_count.toLocaleString()} cases</td>
                <td style={{ fontWeight: 700, color: "#059669" }}>{summary.reviveai.recovered_count.toLocaleString()} cases</td>
                <td style={{ color: "#059669", fontWeight: 600 }}>+{(summary.reviveai.recovered_count - summary.baseline.recovered_count).toLocaleString()} (+{summary.uplift.recovery_rate_lift_pct}%)</td>
              </tr>
              <tr>
                <td><strong>Total Recovered Revenue</strong></td>
                <td>₹{summary.baseline.recovered_amount_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                <td style={{ fontWeight: 700, color: "#059669" }}>₹{summary.reviveai.recovered_amount_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                <td style={{ color: "#059669", fontWeight: 600 }}>+₹{summary.uplift.recovered_revenue_lift_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
              </tr>
              <tr>
                <td><strong>Average Attempts per Case</strong></td>
                <td>{summary.baseline.avg_attempts.toFixed(2)} blind attempts</td>
                <td style={{ fontWeight: 600 }}>{summary.reviveai.avg_attempts.toFixed(2)} targeted action</td>
                <td style={{ color: "#059669" }}>-{(summary.baseline.avg_attempts - summary.reviveai.avg_attempts).toFixed(2)} (Friction reduced)</td>
              </tr>
              <tr>
                <td><strong>Hard Declines Safely Intercepted</strong></td>
                <td style={{ color: "#DC2626" }}>0 (Wasted bank retries & penalties)</td>
                <td style={{ color: "#059669", fontWeight: 600 }}>{summary.reviveai.hard_declines_stopped_count} (100% blocked)</td>
                <td style={{ color: "#059669", fontWeight: 600 }}>Zero merchant score penalty</td>
              </tr>
              <tr>
                <td><strong>Human Review Escalations</strong></td>
                <td>0 (Unchecked autonomous errors)</td>
                <td>{summary.reviveai.human_escalations_count} high-value cases</td>
                <td>Safety & Governance bounded</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Scenario Breakdown */}
      <div className="card">
        <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#0C2340", marginBottom: "12px" }}>
          Breakdown by Payment Failure Scenario
        </h3>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Failure Scenario</th>
                <th>Total Events</th>
                <th>Risk Amount</th>
                <th>Baseline Recovery %</th>
                <th>ReviveAI Recovery %</th>
                <th>ReviveAI Recovered (₹)</th>
                <th>Lift</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(scenario_breakdown).map(([scenarioKey, sc]) => (
                <tr key={scenarioKey}>
                  <td style={{ fontWeight: 600 }}>{scenarioKey.replace(/_/g, " ").toUpperCase()}</td>
                  <td>{sc.total_events.toLocaleString()}</td>
                  <td>₹{sc.risk_amount_inr.toLocaleString("en-IN")}</td>
                  <td>{sc.baseline_recovery_rate_pct.toFixed(1)}%</td>
                  <td style={{ fontWeight: 700, color: "#059669" }}>{sc.reviveai_recovery_rate_pct.toFixed(1)}%</td>
                  <td style={{ fontWeight: 600 }}>₹{sc.reviveai_recovered_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                  <td style={{ color: "#059669", fontWeight: 700 }}>+{sc.recovery_lift_pct.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Honest Failure Analysis */}
      <div className="card" style={{ borderLeft: "4px solid #F59E0B" }}>
        <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#0C2340", marginBottom: "6px" }}>
          Honest Failure Analysis & System Boundaries
        </h3>
        <p style={{ fontSize: "13px", color: "#475569", lineHeight: "1.5" }}>
          {failure_analysis.explanation}
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginTop: "16px" }}>
          <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "6px", padding: "12px" }}>
            <div style={{ fontSize: "11px", color: "#991B1B", fontWeight: 700, textTransform: "uppercase" }}>
              Unrecoverable Cases
            </div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: "#991B1B", marginTop: "2px" }}>
              {failure_analysis.unrecoverable_cases.toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#7F1D1D", marginTop: "2px" }}>
              Permanently closed accounts / revoked mandate
            </div>
          </div>

          <div style={{ background: "#FFFBEB", border: "1px solid #FDE68A", borderRadius: "6px", padding: "12px" }}>
            <div style={{ fontSize: "11px", color: "#92400E", fontWeight: 700, textTransform: "uppercase" }}>
              Policy Interceptions
            </div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: "#92400E", marginTop: "2px" }}>
              {failure_analysis.policy_rejected_actions.toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#78350F", marginTop: "2px" }}>
              Violations of retry limits or cooldowns prevented
            </div>
          </div>

          <div style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "6px", padding: "12px" }}>
            <div style={{ fontSize: "11px", color: "#1E40AF", fontWeight: 700, textTransform: "uppercase" }}>
              Human Escalations
            </div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: "#1E40AF", marginTop: "2px" }}>
              {failure_analysis.human_escalated_cases.toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#1E3A8A", marginTop: "2px" }}>
              Amounts &gt; ₹50,000 routed to human review
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
