import { useState, useEffect } from "react";
import {
  fetchCases,
  fetchMetrics,
  fetchCaseDetail,
  overrideCaseAction,
  triggerBatchSimulation,
  resetSimulationData
} from "./services/api";
import type { RecoveryCaseItem, RecoveryCaseDetail, MetricsOverview as MetricsType } from "./types";
import { Navbar } from "./components/Navbar";
import { MetricsOverview } from "./components/MetricsOverview";
import { RecoveryQueue } from "./components/RecoveryQueue";
import { CaseDetailModal } from "./components/CaseDetailModal";
import { SimulationRunner } from "./components/SimulationRunner";
import { EvaluationView } from "./components/EvaluationView";
import { AuditTrailView } from "./components/AuditTrailView";

export function App() {
  const [activeTab, setActiveTab] = useState<string>("queue");
  const [cases, setCases] = useState<RecoveryCaseItem[]>([]);
  const [metrics, setMetrics] = useState<MetricsType>({
    total_cases: 0,
    active_cases: 0,
    recovered_cases: 0,
    failed_cases: 0,
    escalated_cases: 0,
    stopped_cases: 0,
    total_revenue_at_risk_inr: 0.0,
    total_recovered_revenue_inr: 0.0,
    recovery_rate_pct: 0.0,
    baseline_recovery_rate_pct: 38.5,
    net_revenue_lift_inr: 0.0,
    avg_confidence_score: 0.85,
    prevented_friction_events_count: 0,
    total_intervention_cost_inr: 0.0,
  });

  const [selectedCaseDetail, setSelectedCaseDetail] = useState<RecoveryCaseDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [recoveryMode, setRecoveryMode] = useState<string>("SANDBOX_SIMULATION");

  const loadData = async () => {
    try {
      const [casesData, metricsData] = await Promise.all([
        fetchCases(statusFilter, searchQuery),
        fetchMetrics(),
      ]);
      setCases(casesData);
      setMetrics(metricsData);
      if (casesData.length > 0) {
        setRecoveryMode(casesData[0].recovery_mode);
      }
    } catch (e) {
      console.error("Error loading ReviveAI data:", e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [statusFilter, searchQuery]);

  const handleSelectCase = async (item: RecoveryCaseItem) => {
    try {
      const detail = await fetchCaseDetail(item.id);
      setSelectedCaseDetail(detail);
    } catch (e) {
      console.error(e);
    }
  };

  const handleOverrideAction = async (action: string, timing: number, notes?: string) => {
    if (!selectedCaseDetail) return;
    await overrideCaseAction(selectedCaseDetail.id, action, timing, notes);
    const updated = await fetchCaseDetail(selectedCaseDetail.id);
    setSelectedCaseDetail(updated);
    loadData();
  };

  const handleQuickBatch = async () => {
    await triggerBatchSimulation("mixed_distribution", 20);
    await loadData();
    setActiveTab("queue");
  };

  const handleReset = async () => {
    await resetSimulationData();
    await loadData();
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onReset={handleReset}
        onRunBatch={handleQuickBatch}
        recoveryMode={recoveryMode}
      />

      <main className="main-content">
        {/* Top KPI Metrics Banner */}
        <MetricsOverview metrics={metrics} />

        {/* Tab Views */}
        {activeTab === "queue" && (
          <RecoveryQueue
            cases={cases}
            onSelectCase={handleSelectCase}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
        )}

        {activeTab === "simulator" && (
          <SimulationRunner onSimulationComplete={loadData} />
        )}

        {activeTab === "evaluation" && (
          <EvaluationView />
        )}

        {activeTab === "audit" && (
          <AuditTrailView />
        )}
      </main>

      {/* Case Detail & Decision Inspector Modal */}
      {selectedCaseDetail && (
        <CaseDetailModal
          caseDetail={selectedCaseDetail}
          onClose={() => setSelectedCaseDetail(null)}
          onOverrideAction={handleOverrideAction}
        />
      )}
    </div>
  );
}

export default App;
