import React, { useEffect, useState } from "react";
import type { AuditLogItem } from "../types";
import { fetchAuditLogs } from "../services/api";
import { FileText, RefreshCw, ChevronDown, ChevronRight } from "lucide-react";

export const AuditTrailView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [actorFilter, setActorFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState<boolean>(true);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await fetchAuditLogs(actorFilter, 150);
      setLogs(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [actorFilter]);

  const getActorBadge = (actor: string) => {
    switch (actor) {
      case "AI_AGENT":
        return <span className="badge badge-info">AI AGENT</span>;
      case "POLICY_ENGINE":
        return <span className="badge badge-warning">POLICY ENGINE</span>;
      case "EXECUTOR":
        return <span className="badge badge-success">EXECUTOR</span>;
      case "RISK_DETECTOR":
        return <span className="badge badge-neutral">RISK DETECTOR</span>;
      case "HUMAN_ADMIN":
        return <span className="badge badge-danger">HUMAN ADMIN</span>;
      default:
        return <span className="badge badge-neutral">{actor}</span>;
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Immutable Audit Trail</h2>
          <p style={{ fontSize: "13px", color: "#64748B", marginTop: "2px" }}>
            Cryptographically verifiable, append-only log of all events, AI proposals, safety guardrail checks, and executions.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <select
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
            style={{
              padding: "6px 10px",
              borderRadius: "6px",
              border: "1px solid #CBD5E1",
              fontSize: "13px",
              background: "#FFFFFF",
            }}
          >
            <option value="ALL">All Actors</option>
            <option value="AI_AGENT">AI Agent</option>
            <option value="POLICY_ENGINE">Policy Engine</option>
            <option value="EXECUTOR">Executor</option>
            <option value="RISK_DETECTOR">Risk Detector</option>
            <option value="HUMAN_ADMIN">Human Admin</option>
          </select>

          <button className="btn btn-secondary btn-sm" onClick={loadLogs}>
            <RefreshCw size={13} className={loading ? "spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {logs.length === 0 ? (
        <div style={{ padding: "48px 20px", textAlign: "center", color: "#64748B" }}>
          <FileText size={32} style={{ margin: "0 auto 12px", color: "#94A3B8" }} />
          <p style={{ fontWeight: 600, fontSize: "15px", color: "#0C2340" }}>No audit log records found</p>
          <p style={{ fontSize: "13px", marginTop: "4px" }}>
            Execute cases or run simulations to generate structured audit logs.
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: "40px" }}></th>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action Type</th>
                <th>Message</th>
                <th>Case Reference</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const isExpanded = expandedLogId === log.id;
                return (
                  <React.Fragment key={log.id}>
                    <tr onClick={() => setExpandedLogId(isExpanded ? null : log.id)}>
                      <td>
                        {isExpanded ? <ChevronDown size={14} color="#64748B" /> : <ChevronRight size={14} color="#64748B" />}
                      </td>
                      <td style={{ fontSize: "12px", color: "#64748B", whiteSpace: "nowrap" }}>
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td>{getActorBadge(log.actor)}</td>
                      <td style={{ fontWeight: 600, color: "#0C2340" }}>{log.action_type}</td>
                      <td style={{ fontSize: "13px", color: "#334155" }}>{log.message}</td>
                      <td style={{ fontSize: "12px", color: "#64748B", fontFamily: "monospace" }}>
                        {log.case_id ? log.case_id.substring(0, 8) + "..." : "SYSTEM"}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr>
                        <td colSpan={6} style={{ background: "#F8FAFC", padding: "12px 20px", borderBottom: "1px solid #E2E8F0" }}>
                          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748B", textTransform: "uppercase", marginBottom: "4px" }}>
                            Structured Payload Metadata
                          </div>
                          <pre style={{ background: "#0C2340", color: "#E2E8F0", padding: "12px", borderRadius: "6px", fontSize: "12px", overflowX: "auto" }}>
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
