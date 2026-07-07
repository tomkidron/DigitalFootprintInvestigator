"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [activeTab, setActiveTab] = useState("investigate");
  const [target, setTarget] = useState("");
  const [consent, setConsent] = useState(false);
  const [scanMode, setScanMode] = useState("advanced");
  const [timeline, setTimeline] = useState(false);
  const [network, setNetwork] = useState(false);
  const [deepContent, setDeepContent] = useState(false);

  const [isInvestigating, setIsInvestigating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [currentReport, setCurrentReport] = useState<string | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string | null>(null);

  const [reports, setReports] = useState<
    {
      name: string;
      size: number;
      created_at: number;
    }[]
  >([]);

  const [viewingReport, setViewingReport] = useState<string | null>(null);
  const [viewingReportContent, setViewingReportContent] = useState<string>("");

  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  async function fetchReports() {
    try {
      const res = await fetch("/api/reports");
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (e) {
      console.error("Failed to fetch reports", e);
    }
  }

  useEffect(() => {
    if (activeTab === "reports") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchReports();
    }
  }, [activeTab]);

  const deleteReport = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
    try {
      await fetch(`/api/reports/${filename}`, {
        method: "DELETE",
      });
      fetchReports();
    } catch (e) {
      console.error("Failed to delete report", e);
    }
  };

  const viewReport = async (filename: string) => {
    try {
      const res = await fetch(`/api/reports/${filename}`);
      if (res.ok) {
        const text = await res.text();
        setViewingReportContent(text);
        setViewingReport(filename);
      }
    } catch (e) {
      console.error("Failed to view report", e);
    }
  };

  const startInvestigation = async () => {
    if (!target || !consent) return;
    setIsInvestigating(true);
    setLogs([]);
    setCurrentReport(null);
    setCurrentFilename(null);

    const config = {
      search: { mode: scanMode },
      advanced_analysis: {
        timeline_correlation: timeline,
        network_analysis: network,
        deep_content_analysis: deepContent,
      },
    };

    try {
      const res = await fetch("/api/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, config }),
      });

      if (!res.ok) {
        setLogs((prev) => [...prev, "Error: Failed to start investigation"]);
        setIsInvestigating(false);
        return;
      }

      // Stream SSE
      // Note: In browser, fetch doesn't easily process SSE. We should use EventSource or readable stream.
      // Next.js static export means we can just use native EventSource but EventSource only supports GET.
      // So we have to parse the chunked response manually or use fetch with ReadableStream.
      if (!res.body) return;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (value) {
          buffer += decoder.decode(value, { stream: !done });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.replace("data: ", "").trim();
              if (dataStr) {
                try {
                  console.log("Parsing data:", dataStr);
                  const data = JSON.parse(dataStr);
                  setLogs((prev) => [
                    ...prev,
                    `[${new Date().toLocaleTimeString()}] ${
                      data.content || "done"
                    }`,
                  ]);
                  console.log("Parsed data:", data);
                  if (data.type === "done" || data.type === "error") {
                    console.log(
                      "Setting isInvestigating to false, filename:",
                      data.filename,
                    );
                    setIsInvestigating(false);
                    if (data.report) {
                      setCurrentReport(data.report);
                    }
                    if (data.filename) {
                      setCurrentFilename(data.filename);
                    }
                  }
                } catch {
                  setLogs((prev) => [...prev, dataStr]);
                }
              }
            }
          }
        }
        if (done) {
          if (buffer.trim().startsWith("data: ")) {
            const dataStr = buffer.replace("data: ", "").trim();
            try {
              const data = JSON.parse(dataStr);
              if (data.type === "done" || data.type === "error") {
                setIsInvestigating(false);
                if (data.filename) setCurrentFilename(data.filename);
              }
            } catch (e) {}
          }
          break;
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setLogs((prev) => [...prev, `Error: ${msg}`]);
      setIsInvestigating(false);
    }
  };

  return (
    <main className="container">
      <div className="header">
        <h1>Digital Footprint Investigator</h1>
        <p>OSINT tool for digital footprint analysis and reporting.</p>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === "investigate" ? "active" : ""}`}
          onClick={() => setActiveTab("investigate")}
        >
          🔍 Investigate
        </button>
        <button
          className={`tab ${activeTab === "reports" ? "active" : ""}`}
          onClick={() => setActiveTab("reports")}
        >
          📂 Reports
        </button>
      </div>

      {activeTab === "investigate" && (
        <div className="grid-cols-2">
          <div>
            <div className="card">
              <div style={{ marginBottom: "1.5rem" }}>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "var(--danger-color)",
                    fontWeight: 500,
                    marginBottom: "1rem",
                  }}
                >
                  EDUCATIONAL USE ONLY: This tool is designed for educational
                  purposes, security research, and legitimate OSINT
                  investigations.
                </p>
                <div className="checkbox-group">
                  <input
                    type="checkbox"
                    id="consent"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                  <label htmlFor="consent" style={{ fontSize: "0.875rem" }}>
                    I confirm I have a legitimate purpose and will comply with
                    all applicable laws and Terms of Service.
                  </label>
                </div>
              </div>

              <div className="flex-row">
                <div className="input-group flex-1" style={{ marginBottom: 0 }}>
                  <label htmlFor="target">Target Identifier</label>
                  <input
                    type="text"
                    id="target"
                    placeholder="Enter Name, Email, Username, Domain, or Phone Number..."
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    disabled={isInvestigating}
                    aria-label="Target Identifier"
                  />
                </div>
                <button
                  className="btn btn-primary"
                  disabled={!target.trim() || !consent || isInvestigating}
                  onClick={startInvestigation}
                >
                  {isInvestigating ? "Investigating..." : "Start Investigation"}
                </button>
              </div>
            </div>

            <div className="card">
              <h3 style={{ marginBottom: "1rem", fontSize: "1.125rem" }}>
                Investigation Logs
              </h3>
              <div className="log-console" data-testid="stExpander">
                {logs.length === 0 ? (
                  <span style={{ color: "var(--text-secondary)" }}>
                    Waiting to start...
                  </span>
                ) : (
                  logs.map((log, i) => <div key={i}>{log}</div>)
                )}
                <div ref={logEndRef} />
              </div>
            </div>

            {currentReport && (
              <div className="card" style={{ marginTop: "1.5rem" }}>
                <h3
                  style={{
                    marginBottom: "1rem",
                    fontSize: "1.125rem",
                    borderBottom: "1px solid var(--border-color)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Investigation Report
                </h3>
                <div
                  data-testid="stMain"
                  style={{
                    backgroundColor: "var(--bg-primary)",
                    padding: "1.5rem",
                    borderRadius: "6px",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <ReactMarkdown>{currentReport}</ReactMarkdown>
                </div>
                {currentFilename && (
                  <div
                    style={{
                      marginTop: "1.5rem",
                      display: "flex",
                      gap: "0.5rem",
                    }}
                  >
                    <a
                      href={`/api/reports/${currentFilename}.pdf`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                    >
                      Download PDF
                    </a>
                    <a
                      href={`/api/reports/${currentFilename}.html`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                    >
                      Download HTML
                    </a>
                    <a
                      href={`/api/reports/${currentFilename}.json`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                    >
                      Download JSON
                    </a>
                    <a
                      href={`/api/reports/${currentFilename}.md`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                    >
                      Download MD
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="sidebar" data-testid="stSidebar">
            <h2 style={{ fontSize: "1.25rem", marginBottom: "1.5rem" }}>
              Configuration
            </h2>

            <div className="input-group">
              <label>Scan Mode</label>
              <div className="radio-group" style={{ marginTop: "0.5rem" }}>
                <label className="radio-option">
                  <input
                    type="radio"
                    name="scanMode"
                    value="quick"
                    checked={scanMode === "quick"}
                    onChange={() => setScanMode("quick")}
                  />
                  Quick
                </label>
                <label className="radio-option">
                  <input
                    type="radio"
                    name="scanMode"
                    value="advanced"
                    checked={scanMode === "advanced"}
                    onChange={() => setScanMode("advanced")}
                  />
                  Advanced
                </label>
              </div>
            </div>

            {scanMode === "advanced" && (
              <>
                <div className="divider"></div>
                <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>
                  Advanced Analysis
                </h3>

                <div
                  className="checkbox-group"
                  style={{ marginBottom: "1rem" }}
                >
                  <input
                    type="checkbox"
                    id="timeline"
                    checked={timeline}
                    onChange={(e) => setTimeline(e.target.checked)}
                  />
                  <label htmlFor="timeline">Timeline Correlation</label>
                </div>

                <div
                  className="checkbox-group"
                  style={{ marginBottom: "1rem" }}
                >
                  <input
                    type="checkbox"
                    id="network"
                    checked={network}
                    onChange={(e) => setNetwork(e.target.checked)}
                  />
                  <label htmlFor="network">Social Connection Analysis</label>
                </div>

                <div className="checkbox-group">
                  <input
                    type="checkbox"
                    id="deepContent"
                    checked={deepContent}
                    onChange={(e) => setDeepContent(e.target.checked)}
                  />
                  <label htmlFor="deepContent">Deep Content Analysis</label>
                </div>
              </>
            )}

            <div className="divider"></div>
            <div
              style={{
                padding: "1rem",
                backgroundColor: "rgba(63, 125, 232, 0.1)",
                borderRadius: "6px",
                border: "1px solid rgba(63, 125, 232, 0.2)",
              }}
            >
              <p style={{ fontSize: "0.875rem", color: "var(--accent-hover)" }}>
                Ensure you have set up your API keys in .env for full
                functionality.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === "reports" && (
        <div className="card">
          <h2 style={{ fontSize: "1.25rem", marginBottom: "1.5rem" }}>
            Saved Reports
          </h2>
          {reports.length === 0 ? (
            <p style={{ color: "var(--text-secondary)" }}>No reports found.</p>
          ) : (
            <div className="report-list">
              {reports.map((report) => (
                <div key={report.name} className="report-item">
                  <div>
                    <strong>{report.name}</strong>
                    <div
                      style={{
                        fontSize: "0.875rem",
                        color: "var(--text-secondary)",
                        marginTop: "0.25rem",
                      }}
                    >
                      {(report.size / 1024).toFixed(2)} KB •{" "}
                      {new Date(report.created_at * 1000).toLocaleString()}
                    </div>
                  </div>
                  <div className="report-actions">
                    <button
                      className="btn btn-primary"
                      style={{
                        padding: "0.25rem 0.5rem",
                        fontSize: "0.875rem",
                        backgroundColor: "var(--accent-hover)",
                      }}
                      onClick={() => viewReport(report.name)}
                    >
                      View
                    </button>
                    <a
                      href={`/api/reports/${report.name.replace(
                        ".md",
                        ".pdf",
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                      style={{
                        padding: "0.25rem 0.5rem",
                        fontSize: "0.875rem",
                      }}
                    >
                      PDF
                    </a>
                    <a
                      href={`/api/reports/${report.name.replace(
                        ".md",
                        ".html",
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                      style={{
                        padding: "0.25rem 0.5rem",
                        fontSize: "0.875rem",
                      }}
                    >
                      HTML
                    </a>
                    <a
                      href={`/api/reports/${report.name.replace(
                        ".md",
                        ".json",
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                      style={{
                        padding: "0.25rem 0.5rem",
                        fontSize: "0.875rem",
                      }}
                    >
                      JSON
                    </a>
                    <a
                      href={`/api/reports/${report.name}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary"
                      style={{
                        padding: "0.25rem 0.5rem",
                        fontSize: "0.875rem",
                      }}
                    >
                      MD
                    </a>
                    <button
                      className="btn btn-danger"
                      style={{
                        padding: "0.25rem 0.5rem",
                        fontSize: "0.875rem",
                      }}
                      onClick={() => deleteReport(report.name)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {viewingReport && (
            <div
              style={{
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: "rgba(0,0,0,0.5)",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                zIndex: 1000,
                padding: "2rem",
              }}
              onClick={() => setViewingReport(null)}
            >
              <div
                style={{
                  backgroundColor: "var(--bg-primary)",
                  padding: "2rem",
                  borderRadius: "8px",
                  width: "100%",
                  maxWidth: "800px",
                  maxHeight: "90vh",
                  overflowY: "auto",
                  position: "relative",
                  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={() => setViewingReport(null)}
                  style={{
                    position: "absolute",
                    top: "1rem",
                    right: "1rem",
                    background: "none",
                    border: "none",
                    fontSize: "1.5rem",
                    cursor: "pointer",
                    color: "var(--text-primary)",
                  }}
                >
                  &times;
                </button>
                <h3 style={{ marginBottom: "1.5rem", paddingRight: "2rem" }}>
                  {viewingReport}
                </h3>
                <div
                  style={{
                    padding: "1.5rem",
                    backgroundColor: "var(--bg-secondary)",
                    borderRadius: "6px",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <ReactMarkdown>{viewingReportContent}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
