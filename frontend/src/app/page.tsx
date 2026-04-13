"use client";

import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import { Session } from "@/lib/types";
import { fetchSessions, fetchModels, createSession, deleteSession, renameSession } from "@/lib/api";

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [activeDebates, setActiveDebates] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    try {
      const data = await fetchSessions();
      setSessions(data.sessions);
      setActiveDebates(data.active_debates);
    } catch {
      setError("Failed to connect to backend. Is the server running?");
    }
  }, []);

  useEffect(() => {
    loadSessions();
    fetchModels().then(setModels).catch(() => {});
    const interval = setInterval(loadSessions, 5000);
    return () => clearInterval(interval);
  }, [loadSessions]);

  const handleCreateSession = async () => {
    try {
      setError(null);
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    }
  };

  const handleDeleteSession = async (id: number) => {
    try {
      setError(null);
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) setActiveSessionId(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete session");
    }
  };

  const handleRenameSession = async (id: number, name: string) => {
    try {
      setError(null);
      const updated = await renameSession(id, name);
      setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to rename session");
    }
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        activeDebates={activeDebates}
      />
      <div className="flex-1 flex flex-col">
        {error && (
          <div className="px-6 py-2 text-sm text-red-400 border-b"
            style={{ background: "rgba(239,68,68,0.1)", borderColor: "var(--border)" }}>
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">dismiss</button>
          </div>
        )}
        <ChatArea
          session={activeSession}
          models={models}
          onDebateComplete={loadSessions}
        />
      </div>
    </div>
  );
}
