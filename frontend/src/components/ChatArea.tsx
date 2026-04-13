"use client";

import { useState, useRef, useEffect } from "react";
import { Session, Message, DebateEvent, ROLE_COLORS, ROLE_BG_COLORS, ROLE_ICONS } from "@/lib/types";
import { getWebSocketURL, fetchMessages, updateSessionModel } from "@/lib/api";

interface ChatAreaProps {
  session: Session | null;
  models: string[];
  onDebateComplete: () => void;
}

interface DisplayMessage {
  role: string;
  content: string;
  isStreaming?: boolean;
}

export default function ChatArea({ session, models, onDebateComplete }: ChatAreaProps) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [topic, setTopic] = useState("");
  const [rounds, setRounds] = useState(2);
  const [selectedModel, setSelectedModel] = useState(session?.model || "gpt-4o");
  const [isDebating, setIsDebating] = useState(false);
  const [currentRole, setCurrentRole] = useState<string | null>(null);
  const [currentRound, setCurrentRound] = useState(0);
  const [totalRounds, setTotalRounds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Load existing messages when session changes
  useEffect(() => {
    if (!session) {
      setMessages([]);
      return;
    }
    setSelectedModel(session.model);
    setIsDebating(session.status === "debating");

    fetchMessages(session.id).then((msgs: Message[]) => {
      setMessages(msgs.map((m) => ({ role: m.role, content: m.content })));
    }).catch(() => {});

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [session?.id]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentRole]);

  const startDebate = () => {
    if (!session || !topic.trim()) return;
    setError(null);
    setIsDebating(true);
    setMessages((prev) => [...prev, { role: "user", content: topic }]);

    const ws = new WebSocket(getWebSocketURL(session.id));
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ topic: topic.trim(), model: selectedModel, rounds }));
      setTopic("");
    };

    ws.onmessage = (event) => {
      const data: DebateEvent = JSON.parse(event.data);

      switch (data.type) {
        case "round":
          setCurrentRound(data.round || 0);
          setTotalRounds(data.total_rounds || 0);
          break;

        case "debater_start":
          setCurrentRole(data.role || null);
          setMessages((prev) => [...prev, { role: data.role!, content: "", isStreaming: true }]);
          break;

        case "token":
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === data.role) {
              updated[updated.length - 1] = { ...last, content: last.content + data.content };
            }
            return updated;
          });
          break;

        case "debater_end":
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === data.role) {
              updated[updated.length - 1] = { ...last, isStreaming: false };
            }
            return updated;
          });
          setCurrentRole(null);
          break;

        case "complete":
          setIsDebating(false);
          setCurrentRole(null);
          setCurrentRound(0);
          onDebateComplete();
          break;

        case "error":
          setError(data.message || "Unknown error");
          if (!messages.some((m) => m.role !== "user")) {
            setIsDebating(false);
          }
          break;
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed. Is the backend running?");
      setIsDebating(false);
    };

    ws.onclose = () => {
      setIsDebating(false);
      setCurrentRole(null);
    };
  };

  const handleModelChange = async (model: string) => {
    setSelectedModel(model);
    if (session) {
      await updateSessionModel(session.id, model).catch(() => {});
    }
  };

  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ background: "var(--main-bg)" }}>
        <div className="text-center">
          <div className="text-6xl mb-4">{"\u2696\uFE0F"}</div>
          <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
            AI Debate Council
          </h2>
          <p style={{ color: "var(--text-secondary)" }}>
            Select or create a debate session to begin
          </p>
          <div className="flex justify-center gap-6 mt-6 text-sm" style={{ color: "var(--text-secondary)" }}>
            <div className="text-center">
              <div className="text-2xl mb-1">{"\uD83E\uDD1C"}</div>
              <div>4 Debaters</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">{"\u2696\uFE0F"}</div>
              <div>1 Judge</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">{"\uD83E\uDD16"}</div>
              <div>16 Models</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col" style={{ background: "var(--main-bg)" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--card-bg)" }}>
        <div>
          <h2 className="font-semibold" style={{ color: "var(--text-primary)" }}>{session.name}</h2>
          {session.topic && (
            <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
              Topic: {session.topic}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isDebating && currentRound > 0 && (
            <span className="text-xs px-2 py-1 rounded-full" style={{ background: "var(--accent)", color: "white" }}>
              Round {currentRound}/{totalRounds}
            </span>
          )}
          <select
            value={selectedModel}
            onChange={(e) => handleModelChange(e.target.value)}
            disabled={isDebating}
            className="text-xs px-2 py-1.5 rounded border outline-none"
            style={{
              background: "var(--main-bg)",
              borderColor: "var(--border)",
              color: "var(--text-primary)",
            }}
          >
            {models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {error && (
          <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 text-sm animate-fade-in">
            {error}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`animate-fade-in border rounded-lg p-4 ${ROLE_BG_COLORS[msg.role] || "bg-gray-500/10 border-gray-500/30"}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{ROLE_ICONS[msg.role] || "\uD83D\uDCAC"}</span>
              <span className={`font-semibold text-sm ${ROLE_COLORS[msg.role] || "text-gray-400"}`}>
                {msg.role}
              </span>
              {msg.isStreaming && (
                <span className="typing-indicator text-xs" style={{ color: "var(--text-secondary)" }}>
                  <span>.</span><span>.</span><span>.</span>
                </span>
              )}
            </div>
            <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-primary)" }}>
              {msg.content || (msg.isStreaming ? "" : "(empty)")}
            </div>
          </div>
        ))}

        {isDebating && currentRole && !messages.some((m) => m.role === currentRole && m.isStreaming) && (
          <div className="flex items-center gap-2 text-sm animate-fade-in" style={{ color: "var(--text-secondary)" }}>
            <span className="typing-indicator">
              <span>.</span><span>.</span><span>.</span>
            </span>
            <span>{currentRole} is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t" style={{ borderColor: "var(--border)" }}>
        <div className="flex gap-3">
          <div className="flex-1 flex gap-2">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); startDebate(); } }}
              placeholder={isDebating ? "Debate in progress..." : "Enter a debate topic..."}
              disabled={isDebating}
              className="flex-1 px-4 py-2.5 rounded-lg border text-sm outline-none transition-colors"
              style={{
                background: "var(--card-bg)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border)"; }}
            />
            <select
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              disabled={isDebating}
              className="px-2 py-2.5 rounded-lg border text-sm outline-none"
              style={{
                background: "var(--card-bg)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
            >
              {[1, 2, 3, 4, 5].map((r) => (
                <option key={r} value={r}>{r} round{r > 1 ? "s" : ""}</option>
              ))}
            </select>
          </div>
          <button
            onClick={startDebate}
            disabled={isDebating || !topic.trim()}
            className="px-6 py-2.5 rounded-lg text-sm font-medium text-white transition-all"
            style={{
              background: isDebating || !topic.trim() ? "var(--border)" : "var(--accent)",
              cursor: isDebating || !topic.trim() ? "not-allowed" : "pointer",
            }}
            onMouseEnter={(e) => {
              if (!isDebating && topic.trim()) e.currentTarget.style.background = "var(--accent-hover)";
            }}
            onMouseLeave={(e) => {
              if (!isDebating && topic.trim()) e.currentTarget.style.background = "var(--accent)";
            }}
          >
            {isDebating ? "Debating..." : "Start Debate"}
          </button>
        </div>
      </div>
    </div>
  );
}
