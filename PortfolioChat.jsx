"use client";
// PortfolioChat — a self-contained floating chat widget for your portfolio site.
// Works in Next.js (app router: keep the "use client" line above) and any React app.
//
// SECURITY NOTE: this calls a same-origin route (/api/ask) on YOUR OWN site,
// never the Railway backend directly. That route (app/api/ask/route.js) runs
// server-side and attaches the real API secret — which means the secret
// never appears in this file, in the browser bundle, or in the Network tab.
// Do not change apiPath to point at the Railway URL directly; that would
// require shipping the secret to the browser, defeating the whole point.
//
// Usage:
//   import PortfolioChat from "./PortfolioChat";
//   <PortfolioChat />

import { useState, useRef, useEffect } from "react";

const SUGGESTIONS = [
  "What's Vikram's experience?",
  "What technologies does he know?",
  "What projects has he built?",
];

export default function PortfolioChat({ apiPath = "/api/ask" }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! Ask me anything about Vikram's background, skills, or projects.", sources: [] },
  ]);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading, open]);

  async function send(question) {
    const q = (question ?? input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q, sources: [] }]);
    setLoading(true);
    try {
      const res = await fetch(apiPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.answer, sources: data.sources || [] }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, I couldn't reach the assistant right now.", sources: [] }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={S.root}>
      {open && (
        <div style={S.panel}>
          <div style={S.header}>
            <span style={S.headerTitle}>Ask about Vikram</span>
            <button style={S.close} onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </div>

          <div ref={scrollRef} style={S.messages}>
            {messages.map((m, i) => (
              <div key={i} style={{ ...S.row, justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                <div style={{ ...S.bubble, ...(m.role === "user" ? S.userBubble : S.botBubble) }}>
                  <div>{m.content}</div>
                  {m.sources && m.sources.length > 0 && (
                    <div style={S.sources}>Sources: {m.sources.join(", ")}</div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ ...S.row, justifyContent: "flex-start" }}>
                <div style={{ ...S.bubble, ...S.botBubble, ...S.typing }}>…thinking</div>
              </div>
            )}

            {messages.length === 1 && !loading && (
              <div style={S.suggestions}>
                {SUGGESTIONS.map((s) => (
                  <button key={s} style={S.chip} onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            )}
          </div>

          <form
            style={S.inputRow}
            onSubmit={(e) => { e.preventDefault(); send(); }}
          >
            <input
              style={S.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question…"
              aria-label="Your question"
            />
            <button type="submit" style={S.send} disabled={loading}>Send</button>
          </form>
        </div>
      )}

      <button style={S.fab} onClick={() => setOpen((o) => !o)} aria-label="Open chat">
        {open ? "×" : "💬"}
      </button>
    </div>
  );
}

const BRAND = "#4f46e5";
const S = {
  root: { position: "fixed", bottom: 24, right: 24, zIndex: 9999, fontFamily: "system-ui, -apple-system, sans-serif" },
  fab: { width: 56, height: 56, borderRadius: "50%", border: "none", background: BRAND, color: "#fff", fontSize: 24, cursor: "pointer", boxShadow: "0 6px 20px rgba(0,0,0,0.25)" },
  panel: { position: "absolute", bottom: 72, right: 0, width: 360, maxWidth: "90vw", height: 480, maxHeight: "70vh", background: "#fff", borderRadius: 16, boxShadow: "0 12px 40px rgba(0,0,0,0.28)", display: "flex", flexDirection: "column", overflow: "hidden" },
  header: { background: BRAND, color: "#fff", padding: "14px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" },
  headerTitle: { fontWeight: 600, fontSize: 15 },
  close: { background: "transparent", border: "none", color: "#fff", fontSize: 22, cursor: "pointer", lineHeight: 1 },
  messages: { flex: 1, overflowY: "auto", padding: 14, background: "#f7f7f9", display: "flex", flexDirection: "column", gap: 10 },
  row: { display: "flex" },
  bubble: { maxWidth: "80%", padding: "9px 12px", borderRadius: 14, fontSize: 14, lineHeight: 1.45, whiteSpace: "pre-wrap" },
  userBubble: { background: BRAND, color: "#fff", borderBottomRightRadius: 4 },
  botBubble: { background: "#fff", color: "#1a1a1a", border: "1px solid #e5e5ea", borderBottomLeftRadius: 4 },
  sources: { marginTop: 6, fontSize: 11, opacity: 0.6 },
  typing: { fontStyle: "italic", opacity: 0.7 },
  suggestions: { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 4 },
  chip: { border: `1px solid ${BRAND}`, color: BRAND, background: "#fff", borderRadius: 16, padding: "6px 10px", fontSize: 12, cursor: "pointer" },
  inputRow: { display: "flex", gap: 8, padding: 10, borderTop: "1px solid #eee", background: "#fff" },
  input: { flex: 1, border: "1px solid #ddd", borderRadius: 10, padding: "10px 12px", fontSize: 14, outline: "none" },
  send: { border: "none", background: BRAND, color: "#fff", borderRadius: 10, padding: "0 16px", fontSize: 14, cursor: "pointer" },
};
