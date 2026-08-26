import React, { useState } from "react";
import { triggerBatchSimulation } from "../services/api";
import { Play, RefreshCw } from "lucide-react";

interface Props {
  onSimulationComplete: () => void;
}

export const SimulationRunner: React.FC<Props> = ({ onSimulationComplete }) => {
  const [selectedScenario, setSelectedScenario] = useState<string>("mixed_distribution");
  const [batchCount, setBatchCount] = useState<number>(25);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<any | null>(null);

  const handleRun = async () => {
    setIsRunning(true);
    try {
      const res = await triggerBatchSimulation(selectedScenario, batchCount);
      setLastResult(res);
      onSimulationComplete();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  const scenarios = [
    {
      id: "mixed_distribution",
      name: "Realistic Market Distribution",
      desc: "Representative Indian fintech mix: 40% insufficient balance, 20% UPI Autopay churn, 15% expired cards, 12% gateway downtime, 8% hard declines, 5% high-value enterprise.",
    },
    {
      id: "insufficient_funds_spike",
      name: "Salary-Cycle Liquidity Shortfall",
      desc: "End-of-month card balance declines. Tests ReviveAI's smart timing delayed retry against naive immediate retry.",
    },
    {
      id: "subscription_mandate_churn",
      name: "UPI AutoPay Mandate Failures",
      desc: "Recurring subscription debits paused or revoked. Tests automated 1-click WhatsApp interactive re-auth links.",
    },
    {
      id: "expired_cards_wave",
      name: "Batch Card Token Expirations",
      desc: "Cards expired at month boundary. Demonstrates policy rejection of futile retries and instant token update links.",
    },
    {
      id: "temporary_gateway_outage",
      name: "Transient Bank Gateway Downtime",
      desc: "1-3 hour bank switch timeout. Tests zero-friction short-delay retry without bothering cardholders.",
    },
    {
      id: "hard_declines_stolen",
      name: "Stolen & Closed Account Hard Declines",
      desc: "Critical safety test: verifies policy engine 100% blocks retries on stolen cards to prevent merchant penalties.",
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Live Revenue Risk Batch Simulator</h2>
          <p style={{ fontSize: "13px", color: "#64748B", marginTop: "2px" }}>
            Generate realistic payment failure events to evaluate ReviveAI's end-to-end diagnosis and recovery workflow.
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Scenario Selection */}
        <div>
          <label style={{ fontSize: "12px", fontWeight: 700, color: "#0C2340", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
            Select Simulation Scenario
          </label>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {scenarios.map((sc) => (
              <div
                key={sc.id}
                onClick={() => setSelectedScenario(sc.id)}
                style={{
                  border: selectedScenario === sc.id ? "2px solid #3395FF" : "1px solid #E2E8F0",
                  borderRadius: "8px",
                  padding: "12px 14px",
                  background: selectedScenario === sc.id ? "#F0F7FF" : "#FFFFFF",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ fontWeight: 600, color: "#0C2340", fontSize: "13px" }}>{sc.name}</div>
                <div style={{ fontSize: "12px", color: "#64748B", marginTop: "2px" }}>{sc.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Controls & Execution */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ fontSize: "12px", fontWeight: 700, color: "#0C2340", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
              Batch Sample Size
            </label>
            <div style={{ display: "flex", gap: "10px" }}>
              {[10, 25, 50, 100].map((count) => (
                <button
                  key={count}
                  className={`btn ${batchCount === count ? "btn-primary" : "btn-secondary"}`}
                  onClick={() => setBatchCount(count)}
                >
                  {count} Events
                </button>
              ))}
            </div>
          </div>

          <div style={{ background: "#F8FAFC", border: "1px solid #E2E8F0", borderRadius: "8px", padding: "16px" }}>
            <h4 style={{ fontSize: "13px", fontWeight: 700, color: "#0C2340", marginBottom: "6px" }}>
              Execution Safeguards Active
            </h4>
            <ul style={{ fontSize: "12px", color: "#475569", listStyle: "disc", paddingLeft: "18px", lineHeight: "1.6" }}>
              <li>Deterministic Safety Policy validates every AI decision prior to execution.</li>
              <li>Maximum 3 retries enforced; hard declines automatically blocked.</li>
              <li>Expected Recovery Value model optimizes for net recovered revenue.</li>
              <li>Full immutable audit trail recorded in database.</li>
            </ul>
          </div>

          <button
            className="btn btn-primary"
            style={{ padding: "12px 20px", fontSize: "14px" }}
            onClick={handleRun}
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <RefreshCw size={16} className="spin" /> Generating & Processing {batchCount} Events...
              </>
            ) : (
              <>
                <Play size={16} /> Run {batchCount}-Event Simulation
              </>
            )}
          </button>

          {lastResult && (
            <div style={{ background: "#ECFDF5", border: "1px solid #A7F3D0", borderRadius: "8px", padding: "12px 14px", color: "#065F46", fontSize: "13px" }}>
              <strong>Successfully simulated {lastResult.simulated_count} events!</strong>
              <div style={{ marginTop: "4px", fontSize: "12px" }}>
                Events have been ingested, diagnosed, authorized by safety guardrails, and executed in the Recovery Queue.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
