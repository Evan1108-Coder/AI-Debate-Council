"use client";

import { useState } from "react";
import { Session } from "@/lib/types";

interface SidebarProps {
  sessions: Session[];
  activeSessionId: number | null;
  onSelectSession: (id: number) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: number) => void;
  onRenameSession: (id: number, name: string) => void;
  activeDebates: number;
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onRenameSession,
  activeDebates,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");

  const startRename = (session: Session) => {
    setEditingId(session.id);
    setEditName(session.name);
  };

  const submitRename = (id: number) => {
    if (editName.trim()) {
      onRenameSession(id, editName.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="w-72 h-screen flex flex-col border-r"
      style={{ background: "var(--sidebar-bg)", borderColor: "var(--border)" }}>
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: "var(--border)" }}>
        <h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
          AI Debate Council
        </h1>
        <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
          {activeDebates}/3 active debates
        </p>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onCreateSession}
          disabled={sessions.length >= 10}
          className="w-full py-2.5 px-4 rounded-lg text-sm font-medium transition-all border"
          style={{
            borderColor: "var(--accent)",
            color: sessions.length >= 10 ? "var(--text-secondary)" : "var(--accent)",
            opacity: sessions.length >= 10 ? 0.5 : 1,
          }}
          onMouseEnter={(e) => {
            if (sessions.length < 10) {
              e.currentTarget.style.background = "var(--accent)";
              e.currentTarget.style.color = "white";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = sessions.length >= 10 ? "var(--text-secondary)" : "var(--accent)";
          }}
        >
          + New Debate {sessions.length >= 10 ? "(Max 10)" : `(${sessions.length}/10)`}
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto px-2">
        {sessions.map((session) => (
          <div
            key={session.id}
            className="group flex items-center gap-2 px-3 py-2.5 rounded-lg mb-1 cursor-pointer transition-all"
            style={{
              background: activeSessionId === session.id ? "var(--sidebar-active)" : "transparent",
            }}
            onMouseEnter={(e) => {
              if (activeSessionId !== session.id) {
                e.currentTarget.style.background = "var(--sidebar-hover)";
              }
            }}
            onMouseLeave={(e) => {
              if (activeSessionId !== session.id) {
                e.currentTarget.style.background = "transparent";
              }
            }}
            onClick={() => onSelectSession(session.id)}
          >
            {/* Status indicator */}
            <span className="text-xs">
              {session.status === "debating" ? "\uD83D\uDD34" : session.status === "completed" ? "\u2705" : "\u26AA"}
            </span>

            {/* Name */}
            <div className="flex-1 min-w-0">
              {editingId === session.id ? (
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onBlur={() => submitRename(session.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") submitRename(session.id);
                    if (e.key === "Escape") setEditingId(null);
                  }}
                  className="w-full bg-transparent text-sm outline-none border-b"
                  style={{ color: "var(--text-primary)", borderColor: "var(--accent)" }}
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="text-sm truncate block" style={{ color: "var(--text-primary)" }}>
                  {session.name}
                </span>
              )}
            </div>

            {/* Action buttons */}
            <div className="hidden group-hover:flex items-center gap-1">
              <button
                onClick={(e) => { e.stopPropagation(); startRename(session); }}
                className="p-1 rounded hover:bg-white/10 text-xs"
                title="Rename"
              >
                &#9998;
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id); }}
                className="p-1 rounded hover:bg-red-500/20 text-xs text-red-400"
                title="Delete"
              >
                &#128465;
              </button>
            </div>
          </div>
        ))}

        {sessions.length === 0 && (
          <p className="text-center text-sm py-8" style={{ color: "var(--text-secondary)" }}>
            No debate sessions yet.<br />Click &quot;+ New Debate&quot; to start.
          </p>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t text-xs" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
        Built by Evan Lu
      </div>
    </div>
  );
}
