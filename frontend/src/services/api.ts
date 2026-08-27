import type {
  RecoveryCaseItem,
  RecoveryCaseDetail,
  MetricsOverview,
  AuditLogItem,
  EvaluationReport
} from "../types";
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");

export async function fetchMetrics(): Promise<MetricsOverview> {
  const res = await fetch(`${API_BASE}/cases/metrics`);
  if (!res.ok) throw new Error("Failed to fetch recovery metrics");
  return res.json();
}

export async function fetchCases(status?: string, search?: string): Promise<RecoveryCaseItem[]> {
  const params = new URLSearchParams();
  if (status && status !== "ALL") params.append("status", status);
  if (search) params.append("search", search);
  params.append("limit", "100");

  const res = await fetch(`${API_BASE}/cases?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch cases");
  return res.json();
}

export async function fetchCaseDetail(idOrNumber: string): Promise<RecoveryCaseDetail> {
  const res = await fetch(`${API_BASE}/cases/${idOrNumber}`);
  if (!res.ok) throw new Error(`Failed to fetch case ${idOrNumber}`);
  return res.json();
}

export async function overrideCaseAction(
  caseId: string,
  action: string,
  timingMinutes: number = 0,
  notes?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, timing_schedule_minutes: timingMinutes, notes }),
  });
  if (!res.ok) throw new Error("Failed to apply manual override");
  return res.json();
}

export async function triggerBatchSimulation(scenario: string, count: number = 20): Promise<any> {
  const res = await fetch(`${API_BASE}/simulation/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario, count, auto_process: true }),
  });
  if (!res.ok) throw new Error("Failed to trigger batch simulation");
  return res.json();
}

export async function resetSimulationData(): Promise<any> {
  const res = await fetch(`${API_BASE}/simulation/reset`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reset simulation database");
  return res.json();
}

export async function fetchAuditLogs(actor?: string, limit: number = 100): Promise<AuditLogItem[]> {
  const params = new URLSearchParams();
  if (actor && actor !== "ALL") params.append("actor", actor);
  params.append("limit", String(limit));

  const res = await fetch(`${API_BASE}/audit?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

export async function fetchEvaluationReport(): Promise<EvaluationReport> {
  const res = await fetch(`${API_BASE}/evaluation/latest`);
  if (!res.ok) throw new Error("Failed to fetch evaluation report");
  return res.json();
}

export async function runLiveEvaluation(samples: number = 5000): Promise<any> {
  const res = await fetch(`${API_BASE}/evaluation/run?samples=${samples}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to execute benchmark run");
  return res.json();
}
