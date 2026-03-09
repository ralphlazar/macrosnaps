import { useState, useEffect } from "react";

const COUNTRIES = [
  { code: "USA", name: "United States", flag: "🇺🇸" },
  { code: "CAN", name: "Canada", flag: "🇨🇦" },
  { code: "GBR", name: "United Kingdom", flag: "🇬🇧" },
  { code: "JPN", name: "Japan", flag: "🇯🇵" },
  { code: "DEU", name: "Germany", flag: "🇩🇪" },
  { code: "FRA", name: "France", flag: "🇫🇷" },
  { code: "ITA", name: "Italy", flag: "🇮🇹" },
  { code: "CHN", name: "China", flag: "🇨🇳" },
  { code: "IND", name: "India", flag: "🇮🇳" },
  { code: "ZAF", name: "South Africa", flag: "🇿🇦" },
  { code: "BRA", name: "Brazil", flag: "🇧🇷" },
  { code: "RUS", name: "Russia", flag: "🇷🇺" },
];

const SEVERITY_CONFIG = {
  HIGH:   { color: "#ff4444", bg: "rgba(255,68,68,0.10)",   label: "UPDATE NOW",  dot: "#ff4444" },
  MEDIUM: { color: "#f5a623", bg: "rgba(245,166,35,0.10)",  label: "REVIEW",      dot: "#f5a623" },
  LOW:    { color: "#4a9eff", bg: "rgba(74,158,255,0.08)",  label: "MONITOR",     dot: "#4a9eff" },
};

const SYSTEM_PROMPT = `You are a macro intelligence analyst monitoring global events for MacroSnaps, a daily global macro and markets dashboard.

MacroSnaps tracks 12 countries: USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS.

For each country it maintains these updateable fields:
- Country stories (3 bullet narratives at beginner/moderate/expert level)
- Per-metric stories for 14 metrics: GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate, Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, FX pair, FX Vol
- Raw metric values (updated daily/weekly/quarterly depending on tier)
- Global stories (Today's Story, Biggest Movers, The Connection)

Your job: search for notable macro events from the past 48 hours for each of the 12 countries. 

An event is notable if it:
- Changes a metric value (e.g. central bank rate decision, CPI release, jobs data)
- Materially changes the narrative (e.g. political shock, sovereign rating action, geopolitical escalation)
- Creates a global story opportunity (cross-country theme)

For each notable event found, return a JSON array. Each object must have:
- country: the 3-letter code (or "GLOBAL" for cross-country events)
- flag: the country flag emoji
- headline: one sharp sentence describing the event (max 12 words, no em dashes)
- detail: 2-3 sentences of context. What happened, why it matters for MacroSnaps. No em dashes.
- severity: "HIGH" (update today), "MEDIUM" (review this week), or "LOW" (monitor)
- fields_affected: array of strings, each being a field name from the list above (e.g. "Policy Rate", "Country stories", "Global stories", "Inflation (CPI)")
- source: short source attribution (e.g. "Reuters / Bloomberg, March 2026")

If no notable event found for a country, omit it from the array.

Return ONLY valid JSON. No preamble, no markdown fences, no explanation. Just the raw JSON array.`;

function AlertCard({ alert, index }) {
  const [expanded, setExpanded] = useState(false);
  const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.LOW;
  const country = COUNTRIES.find(c => c.code === alert.country);
  const flag = country?.flag || alert.flag || "🌐";

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      style={{
        background: sev.bg,
        border: `1px solid ${sev.color}33`,
        borderLeft: `3px solid ${sev.color}`,
        borderRadius: "6px",
        padding: "14px 18px",
        cursor: "pointer",
        transition: "all 0.15s ease",
        animation: `fadeSlideIn 0.3s ease both`,
        animationDelay: `${index * 0.06}s`,
        opacity: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span style={{ fontSize: "20px", lineHeight: 1 }}>{flag}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
            <span style={{
              fontSize: "9px",
              fontFamily: "'Courier New', monospace",
              fontWeight: 700,
              letterSpacing: "0.12em",
              color: sev.color,
              background: `${sev.color}18`,
              padding: "2px 7px",
              borderRadius: "3px",
            }}>
              {sev.label}
            </span>
            <span style={{
              fontSize: "9px",
              fontFamily: "'Courier New', monospace",
              color: "#666",
              letterSpacing: "0.08em",
            }}>
              {alert.country}
            </span>
          </div>
          <div style={{
            fontSize: "13.5px",
            fontFamily: "'Georgia', serif",
            fontWeight: 600,
            color: "#e8e8e8",
            lineHeight: 1.35,
          }}>
            {alert.headline}
          </div>
        </div>
        <div style={{
          fontSize: "11px",
          color: "#555",
          transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
          transition: "transform 0.2s ease",
          flexShrink: 0,
        }}>▾</div>
      </div>

      {expanded && (
        <div style={{
          marginTop: "12px",
          paddingTop: "12px",
          borderTop: `1px solid ${sev.color}22`,
          animation: "expandIn 0.2s ease",
        }}>
          <p style={{
            fontSize: "12.5px",
            color: "#aaa",
            lineHeight: 1.6,
            margin: "0 0 12px 0",
            fontFamily: "'Georgia', serif",
          }}>
            {alert.detail}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "8px" }}>
            {(alert.fields_affected || []).map(field => (
              <span key={field} style={{
                fontSize: "10px",
                fontFamily: "'Courier New', monospace",
                color: "#888",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid #333",
                padding: "2px 8px",
                borderRadius: "3px",
              }}>
                {field}
              </span>
            ))}
          </div>
          <div style={{ fontSize: "10px", color: "#555", fontFamily: "'Courier New', monospace" }}>
            {alert.source}
          </div>
        </div>
      )}
    </div>
  );
}

function PulsingDot({ color }) {
  return (
    <span style={{ position: "relative", display: "inline-block", width: 8, height: 8 }}>
      <span style={{
        position: "absolute", inset: 0, borderRadius: "50%",
        background: color, animation: "ping 1.4s ease infinite",
      }} />
      <span style={{
        position: "absolute", inset: 0, borderRadius: "50%", background: color,
      }} />
    </span>
  );
}

export default function MacroSnapsAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState("idle"); // idle | scanning | done | error
  const [lastScanned, setLastScanned] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [scanLog, setScanLog] = useState([]);

  const highCount   = alerts.filter(a => a.severity === "HIGH").length;
  const mediumCount = alerts.filter(a => a.severity === "MEDIUM").length;
  const lowCount    = alerts.filter(a => a.severity === "LOW").length;

  const addLog = (msg) => setScanLog(prev => [...prev.slice(-4), msg]);

  const scan = async () => {
    setStatus("scanning");
    setAlerts([]);
    setErrorMsg("");
    setScanLog([]);

    const logs = [
      "Connecting to news feeds...",
      "Scanning macro event horizon...",
      "Checking central bank calendars...",
      "Filtering for material signals...",
      "Assembling alert report...",
    ];
    let logIdx = 0;
    const logInterval = setInterval(() => {
      if (logIdx < logs.length) {
        addLog(logs[logIdx++]);
      }
    }, 900);

    try {
      const today = new Date().toLocaleDateString("en-GB", {
        day: "numeric", month: "long", year: "numeric"
      });

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 4000,
          tools: [{ type: "web_search_20250305", name: "web_search" }],
          system: SYSTEM_PROMPT,
          messages: [{
            role: "user",
            content: `Today is ${today}. Search for notable macro events from the past 48 hours for the 12 MacroSnaps countries. Use web search to find real current news. Return the JSON alert array as instructed.`
          }]
        })
      });

      clearInterval(logInterval);

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`API error ${response.status}: ${err}`);
      }

      const data = await response.json();

      const textBlock = data.content.find(b => b.type === "text");
      if (!textBlock) throw new Error("No text response from API");

      let raw = textBlock.text.trim();
      raw = raw.replace(/^```json\s*/i, "").replace(/```\s*$/, "").trim();

      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) throw new Error("Response was not a JSON array");

      setAlerts(parsed.sort((a, b) => {
        const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
        return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
      }));
      setLastScanned(new Date());
      setStatus("done");
    } catch (err) {
      clearInterval(logInterval);
      setErrorMsg(err.message);
      setStatus("error");
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0a",
      fontFamily: "'Courier New', monospace",
      padding: "0",
    }}>
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes expandIn {
          from { opacity: 0; transform: translateY(-4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes ping {
          0%   { transform: scale(1); opacity: 0.8; }
          75%  { transform: scale(2.2); opacity: 0; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        @keyframes scanPulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.3; }
        }
        @keyframes scrollLog {
          from { opacity: 0; transform: translateX(-6px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        .scan-btn {
          background: #e8e8e8;
          color: #0a0a0a;
          border: none;
          padding: 11px 28px;
          font-family: 'Courier New', monospace;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.14em;
          cursor: pointer;
          border-radius: 4px;
          transition: all 0.15s ease;
        }
        .scan-btn:hover { background: #fff; transform: translateY(-1px); }
        .scan-btn:disabled { background: #333; color: #666; cursor: not-allowed; transform: none; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 2px; }
      `}</style>

      {/* Header */}
      <div style={{
        borderBottom: "1px solid #1a1a1a",
        padding: "20px 28px 18px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        background: "#0a0a0a",
        zIndex: 10,
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "3px" }}>
            <span style={{ fontSize: "10px", color: "#444", letterSpacing: "0.16em" }}>
              MACROSNAPS
            </span>
            <span style={{ color: "#222", fontSize: "10px" }}>/</span>
            <span style={{ fontSize: "10px", color: "#666", letterSpacing: "0.16em" }}>
              COUNTRY ALERT SCANNER
            </span>
          </div>
          <div style={{ fontSize: "18px", fontFamily: "'Georgia', serif", color: "#e8e8e8", fontWeight: 600 }}>
            Macro Event Monitor
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          {status === "done" && alerts.length > 0 && (
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              {highCount > 0 && (
                <span style={{ fontSize: "11px", color: "#ff4444", display: "flex", alignItems: "center", gap: "5px" }}>
                  <PulsingDot color="#ff4444" /> {highCount} urgent
                </span>
              )}
              {mediumCount > 0 && (
                <span style={{ fontSize: "11px", color: "#f5a623" }}>{mediumCount} review</span>
              )}
              {lowCount > 0 && (
                <span style={{ fontSize: "11px", color: "#4a9eff" }}>{lowCount} monitor</span>
              )}
            </div>
          )}
          <button
            className="scan-btn"
            onClick={scan}
            disabled={status === "scanning"}
          >
            {status === "scanning" ? "SCANNING..." : status === "done" ? "RESCAN" : "SCAN NOW"}
          </button>
        </div>
      </div>

      <div style={{ padding: "20px 28px", maxWidth: "860px", margin: "0 auto" }}>

        {/* Idle state */}
        {status === "idle" && (
          <div style={{
            textAlign: "center",
            padding: "60px 20px",
            color: "#333",
          }}>
            <div style={{ fontSize: "36px", marginBottom: "16px", opacity: 0.4 }}>⚡</div>
            <div style={{ fontSize: "13px", letterSpacing: "0.1em", marginBottom: "8px" }}>
              MACRO EVENT SCANNER
            </div>
            <div style={{ fontSize: "11px", color: "#2a2a2a", maxWidth: "340px", margin: "0 auto", lineHeight: 1.7 }}>
              Scans 12 countries for notable events in the past 48 hours. Flags which MacroSnaps fields need updating.
            </div>
            <div style={{ marginTop: "32px", display: "flex", gap: "24px", justifyContent: "center" }}>
              {[
                { label: "Central bank decisions", icon: "🏦" },
                { label: "Data releases", icon: "📊" },
                { label: "Political shocks", icon: "⚠️" },
                { label: "Market events", icon: "📉" },
              ].map(item => (
                <div key={item.label} style={{ fontSize: "10px", color: "#2a2a2a", textAlign: "center" }}>
                  <div style={{ fontSize: "18px", marginBottom: "4px" }}>{item.icon}</div>
                  {item.label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Scanning state */}
        {status === "scanning" && (
          <div style={{ padding: "48px 20px" }}>
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "28px",
            }}>
              <div style={{
                width: "8px", height: "8px", borderRadius: "50%",
                background: "#4a9eff",
                animation: "scanPulse 1s ease infinite",
              }} />
              <span style={{ fontSize: "11px", color: "#4a9eff", letterSpacing: "0.1em" }}>
                LIVE SCAN IN PROGRESS
              </span>
            </div>

            {/* Country progress dots */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "32px" }}>
              {COUNTRIES.map((c, i) => (
                <div key={c.code} style={{
                  display: "flex", alignItems: "center", gap: "5px",
                  background: "#111", border: "1px solid #1e1e1e",
                  borderRadius: "4px", padding: "5px 10px",
                  animation: `fadeSlideIn 0.3s ease both`,
                  animationDelay: `${i * 0.07}s`,
                  opacity: 0,
                }}>
                  <span style={{ fontSize: "12px" }}>{c.flag}</span>
                  <span style={{ fontSize: "9px", color: "#444", letterSpacing: "0.1em" }}>{c.code}</span>
                </div>
              ))}
            </div>

            {/* Log */}
            <div style={{
              background: "#0f0f0f", border: "1px solid #1a1a1a",
              borderRadius: "4px", padding: "14px 16px",
              minHeight: "80px",
            }}>
              {scanLog.map((log, i) => (
                <div key={i} style={{
                  fontSize: "10px", color: i === scanLog.length - 1 ? "#666" : "#2a2a2a",
                  lineHeight: "1.8",
                  animation: "scrollLog 0.3s ease",
                }}>
                  <span style={{ color: "#333", marginRight: "8px" }}>$</span>{log}
                  {i === scanLog.length - 1 && (
                    <span style={{ animation: "scanPulse 0.8s ease infinite", marginLeft: "4px", color: "#4a9eff" }}>▌</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error state */}
        {status === "error" && (
          <div style={{
            background: "rgba(255,68,68,0.06)", border: "1px solid rgba(255,68,68,0.2)",
            borderRadius: "6px", padding: "20px 24px", marginBottom: "20px",
          }}>
            <div style={{ fontSize: "11px", color: "#ff4444", marginBottom: "6px", letterSpacing: "0.1em" }}>
              SCAN ERROR
            </div>
            <div style={{ fontSize: "12px", color: "#888", lineHeight: 1.6 }}>{errorMsg}</div>
          </div>
        )}

        {/* Results */}
        {status === "done" && (
          <div>
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              marginBottom: "16px",
            }}>
              <div style={{ fontSize: "10px", color: "#333", letterSpacing: "0.1em" }}>
                {alerts.length} ALERTS FOUND
              </div>
              {lastScanned && (
                <div style={{ fontSize: "10px", color: "#2a2a2a" }}>
                  Scanned {lastScanned.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
                </div>
              )}
            </div>

            {alerts.length === 0 ? (
              <div style={{
                textAlign: "center", padding: "40px 20px",
                color: "#2a2a2a", fontSize: "12px",
              }}>
                No notable events detected in the past 48 hours. No MacroSnaps updates required.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {alerts.map((alert, i) => (
                  <AlertCard key={i} alert={alert} index={i} />
                ))}
              </div>
            )}

            {/* Footer */}
            <div style={{
              marginTop: "28px", paddingTop: "16px",
              borderTop: "1px solid #141414",
              fontSize: "10px", color: "#252525",
              lineHeight: 1.7,
            }}>
              Click any alert to expand. HIGH = update data.json today. MEDIUM = review this week. LOW = monitor.
              <br />
              Powered by Claude with live web search. Results reflect past 48 hours of global macro news.
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
