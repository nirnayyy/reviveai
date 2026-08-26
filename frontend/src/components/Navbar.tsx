import React from "react";
import { ShieldCheck, Play, RotateCcw, Activity, FileText, BarChart2 } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onReset: () => void;
  onRunBatch: () => void;
  recoveryMode: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onReset,
  onRunBatch,
  recoveryMode
}) => {
  return (
    <header className="navbar">
      <div className="nav-brand">
        <span className="nav-logo-badge">ReviveAI</span>
        <span className="nav-title">Revenue Recovery Agent</span>
        <span className="nav-subtitle">Razorpay Track 3</span>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === "queue" ? "active" : ""}`}
          onClick={() => setActiveTab("queue")}
        >
          <Activity size={15} />
          Recovery Queue
        </button>
        <button
          className={`nav-tab ${activeTab === "simulator" ? "active" : ""}`}
          onClick={() => setActiveTab("simulator")}
        >
          <Play size={15} />
          Batch Simulator
        </button>
        <button
          className={`nav-tab ${activeTab === "evaluation" ? "active" : ""}`}
          onClick={() => setActiveTab("evaluation")}
        >
          <BarChart2 size={15} />
          Evaluation (10k Benchmark)
        </button>
        <button
          className={`nav-tab ${activeTab === "audit" ? "active" : ""}`}
          onClick={() => setActiveTab("audit")}
        >
          <FileText size={15} />
          Audit Trail
        </button>
      </nav>

      <div className="nav-actions">
        <span className={`mode-badge ${recoveryMode === "RAZORPAY_TEST_MODE" ? "test-mode" : "simulation"}`}>
          <ShieldCheck size={13} />
          {recoveryMode === "RAZORPAY_TEST_MODE" ? "Razorpay Test Mode" : "Sandbox Simulation"}
        </span>

        <button className="btn btn-secondary btn-sm" onClick={onRunBatch} title="Simulate 20 payment failures">
          <Play size={13} />
          Quick Batch (20)
        </button>

        <button className="btn btn-secondary btn-sm" onClick={onReset} title="Reset demo environment">
          <RotateCcw size={13} />
          Reset
        </button>
      </div>
    </header>
  );
};
