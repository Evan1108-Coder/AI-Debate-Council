"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { DebateRoom, type RoomPanel } from "@/components/DebateRoom";
import { Sidebar } from "@/components/Sidebar";
import {
  clearSessionHistory,
  clearSessionMemory,
  createSession,
  deleteDebateStatistics,
  deleteSession,
  getModels,
  getSessionAnalytics,
  getSessionSettings,
  listDebates,
  listMessages,
  listSessions,
  recordRuntimeDiary,
  renameDebate,
  renameSession,
  updateSessionSettings,
  WS_BASE
} from "@/lib/api";
import type {
  ChatSession,
  DebateAnalytics,
  DebateAssignment,
  DebateEvent,
  DebateMessage,
  DebateRecord,
  ModelsResponse,
  SessionSettings
} from "@/types";

const MAX_SESSIONS = 10;
const USER_INPUT_MAX_CHARS = 5500;
const WEBSOCKET_CONNECT_RETRIES = 2;
const WEBSOCKET_RETRY_DELAY_MS = 1200;
type ClearTarget = { session: ChatSession; mode: "history" | "memory" };
type DebateDeleteTarget = { session: ChatSession; debate: DebateRecord };

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messagesBySession, setMessagesBySession] = useState<Record<string, DebateMessage[]>>({});
  const [partialBySession, setPartialBySession] = useState<
    Record<string, Record<string, DebateMessage>>
  >({});
  const [draftBySession, setDraftBySession] = useState<Record<string, string>>({});
  const [settingsBySession, setSettingsBySession] = useState<Record<string, SessionSettings>>({});
  const [modelBySession, setModelBySession] = useState<Record<string, string>>({});
  const [statusBySession, setStatusBySession] = useState<Record<string, string>>({});
  const [assignmentsBySession, setAssignmentsBySession] = useState<
    Record<string, DebateAssignment[]>
  >({});
  const [debatesBySession, setDebatesBySession] = useState<Record<string, DebateRecord[]>>({});
  const [selectedDebateBySession, setSelectedDebateBySession] = useState<Record<string, string>>(
    {}
  );
  const [analyticsBySession, setAnalyticsBySession] = useState<Record<string, DebateAnalytics>>({});
  const [analyticsHistoryBySession, setAnalyticsHistoryBySession] = useState<
    Record<string, DebateAnalytics[]>
  >({});
  const [runningBySession, setRunningBySession] = useState<Record<string, boolean>>({});
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [activePanel, setActivePanel] = useState<RoomPanel>("chat");
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ChatSession | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [clearTarget, setClearTarget] = useState<ClearTarget | null>(null);
  const [clearError, setClearError] = useState<string | null>(null);
  const [deleteDebateTarget, setDeleteDebateTarget] = useState<DebateDeleteTarget | null>(null);
  const [deleteDebateError, setDeleteDebateError] = useState<string | null>(null);
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null);
  const [renamingDebateId, setRenamingDebateId] = useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [deletingDebateId, setDeletingDebateId] = useState<string | null>(null);
  const [clearingSessionId, setClearingSessionId] = useState<string | null>(null);
  const socketRefs = useRef<Record<string, WebSocket>>({});
  const retryTimerRefs = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const selectedSession = sessions.find((session) => session.id === selectedId) ?? null;
  const selectedMessages = selectedId ? messagesBySession[selectedId] ?? [] : [];
  const selectedPartials = selectedId ? partialBySession[selectedId] ?? {} : {};
  const selectedDraft = selectedId ? draftBySession[selectedId] ?? "" : "";
  const selectedSettings = selectedId ? settingsBySession[selectedId] ?? null : null;
  const selectedModelName = selectedId
    ? selectedSettings?.overall_model || modelBySession[selectedId] || ""
    : "";
  const selectedStatus = selectedId
    ? statusBySession[selectedId] ?? "Ready for a message."
    : "No session selected.";
  const selectedAssignments = selectedId ? assignmentsBySession[selectedId] ?? [] : [];
  const selectedDebates = selectedId ? debatesBySession[selectedId] ?? [] : [];
  const selectedDebateId = selectedId ? selectedDebateBySession[selectedId] ?? "" : "";
  const selectedAnalytics = selectedId ? analyticsBySession[selectedId] ?? null : null;
  const selectedAnalyticsHistory = selectedId ? analyticsHistoryBySession[selectedId] ?? [] : [];
  const selectedRunning = selectedId ? Boolean(runningBySession[selectedId]) : false;

  const refreshSessions = useCallback(async () => {
    const nextSessions = await listSessions();
    setSessions(nextSessions);
    return nextSessions;
  }, []);

  const refreshMessages = useCallback(async (sessionId: string) => {
    const nextMessages = await listMessages(sessionId);
    setMessagesBySession((current) => ({ ...current, [sessionId]: nextMessages }));
  }, []);

  const refreshDebates = useCallback(async (sessionId: string) => {
    const nextDebates = await listDebates(sessionId);
    setDebatesBySession((current) => ({ ...current, [sessionId]: nextDebates }));
    setSelectedDebateBySession((current) => {
      const currentId = current[sessionId];
      if (currentId && nextDebates.some((debate) => debate.id === currentId)) {
        return current;
      }
      return { ...current, [sessionId]: nextDebates[0]?.id ?? "" };
    });
    return nextDebates;
  }, []);

  const refreshSettings = useCallback(async (sessionId: string) => {
    const nextSettings = await getSessionSettings(sessionId);
    setSettingsBySession((current) => ({ ...current, [sessionId]: nextSettings }));
    if (nextSettings.overall_model) {
      setModelBySession((current) => ({ ...current, [sessionId]: nextSettings.overall_model }));
    }
  }, []);

  const refreshAnalytics = useCallback(async (sessionId: string, debateId?: string) => {
    const nextAnalytics = await getSessionAnalytics(sessionId, debateId);
    if (nextAnalytics.turn_count === 0) {
      setAnalyticsBySession((current) => removeKey(current, sessionId));
      setAnalyticsHistoryBySession((current) => ({ ...current, [sessionId]: [] }));
      return;
    }
    setAnalyticsBySession((current) => ({ ...current, [sessionId]: nextAnalytics }));
    if (nextAnalytics.source?.debate_id) {
      setSelectedDebateBySession((current) => ({
        ...current,
        [sessionId]: nextAnalytics.source?.debate_id ?? ""
      }));
    }
    setAnalyticsHistoryBySession((current) => ({
      ...current,
      [sessionId]: mergeAnalyticsHistory(current[sessionId] ?? [], nextAnalytics)
    }));
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        const [sessionList, modelData] = await Promise.all([listSessions(), getModels()]);
        if (cancelled) {
          return;
        }
        setModels(modelData);

        setSessions(sessionList);
        setSelectedId(sessionList[0]?.id ?? null);
        recordRuntimeDiary(
          "frontend boot",
          `Loaded ${sessionList.length} session(s) and ${modelData.available_model_count} unlocked model(s).`
        );
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : "Startup failed.");
        recordRuntimeDiary(
          "frontend boot failed",
          exc instanceof Error ? exc.message : "Startup failed."
        );
      }
    }

    boot();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      Object.values(retryTimerRefs.current).forEach((timer) => clearTimeout(timer));
      Object.values(socketRefs.current).forEach((socket) => socket.close());
    };
  }, []);

  useEffect(() => {
    if (!selectedId) {
      return;
    }
    setActivePanel("chat");
    refreshMessages(selectedId).catch((exc) => {
      setError(exc instanceof Error ? exc.message : "Could not load messages.");
    });
    refreshSettings(selectedId).catch((exc) => {
      setError(exc instanceof Error ? exc.message : "Could not load settings.");
    });
    refreshDebates(selectedId).catch(() => undefined);
    refreshAnalytics(selectedId).catch(() => undefined);
  }, [selectedId, refreshMessages, refreshSettings, refreshDebates, refreshAnalytics]);

  useEffect(() => {
    if (!models || !selectedId) {
      return;
    }
    const savedModel = settingsBySession[selectedId]?.overall_model ?? "";
    setModelBySession((current) => {
      const currentName = savedModel || current[selectedId];
      if (models.models.some((model) => model.name === currentName)) {
        return current[selectedId] === currentName ? current : { ...current, [selectedId]: currentName };
      }
      return { ...current, [selectedId]: models.models[0]?.name ?? "" };
    });
  }, [models, selectedId, settingsBySession]);

  async function handleNewSession() {
    setError(null);
    try {
      const created = await createSession();
      setSessions((current) => [created, ...current]);
      setSelectedId(created.id);
      setStatusBySession((current) => ({ ...current, [created.id]: "Ready for a message." }));
      setActivePanel("chat");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not create session.");
    }
  }

  function handleSelect(id: string) {
    setSelectedId(id);
    setError(null);
  }

  async function handleRename(session: ChatSession, name: string) {
    const cleaned = name.trim();
    if (!cleaned || cleaned === session.name) {
      return false;
    }

    const previousSessions = sessions;
    const optimisticSession = {
      ...session,
      name: cleaned,
      updated_at: new Date().toISOString()
    };
    setError(null);
    setRenamingSessionId(session.id);
    setSessions((current) =>
      current.map((item) => (item.id === session.id ? optimisticSession : item))
    );

    try {
      const renamed = await renameSession(session.id, cleaned);
      setSessions((current) =>
        current.map((item) => (item.id === renamed.id ? renamed : item))
      );
      return true;
    } catch (exc) {
      setSessions(previousSessions);
      setError(exc instanceof Error ? exc.message : "Could not rename session.");
      return false;
    } finally {
      setRenamingSessionId(null);
    }
  }

  async function handleConfirmDelete() {
    if (!deleteTarget || deletingSessionId) {
      return;
    }

    const target = deleteTarget;
    const nextSessions = sessions.filter((session) => session.id !== target.id);
    setDeletingSessionId(target.id);
    setDeleteError(null);
    setError(null);

    try {
      await deleteSession(target.id);
      clearSocketRetry(target.id);
      socketRefs.current[target.id]?.close();
      delete socketRefs.current[target.id];
      setSessions(nextSessions);
      setMessagesBySession((current) => removeKey(current, target.id));
      setPartialBySession((current) => removeKey(current, target.id));
      setDraftBySession((current) => removeKey(current, target.id));
      setSettingsBySession((current) => removeKey(current, target.id));
      setModelBySession((current) => removeKey(current, target.id));
      setStatusBySession((current) => removeKey(current, target.id));
      setAssignmentsBySession((current) => removeKey(current, target.id));
      setDebatesBySession((current) => removeKey(current, target.id));
      setSelectedDebateBySession((current) => removeKey(current, target.id));
      setAnalyticsBySession((current) => removeKey(current, target.id));
      setAnalyticsHistoryBySession((current) => removeKey(current, target.id));
      setRunningBySession((current) => removeKey(current, target.id));
      if (selectedId === target.id) {
        setSelectedId(nextSessions[0]?.id ?? null);
      }
      setDeleteTarget(null);
    } catch (exc) {
      const message = exc instanceof Error ? exc.message : "Could not delete session.";
      setDeleteError(message);
      setError(message);
    } finally {
      setDeletingSessionId(null);
    }
  }

  async function handleConfirmClear() {
    if (!clearTarget || clearingSessionId) {
      return;
    }

    const { session, mode } = clearTarget;
    setClearingSessionId(session.id);
    setClearError(null);
    setError(null);

    try {
      if (mode === "history") {
        await clearSessionHistory(session.id);
      } else {
        await clearSessionMemory(session.id);
      }
      setMessagesBySession((current) => ({ ...current, [session.id]: [] }));
      setPartialBySession((current) => ({ ...current, [session.id]: {} }));
      setAssignmentsBySession((current) => ({ ...current, [session.id]: [] }));
      setDebatesBySession((current) => ({ ...current, [session.id]: [] }));
      setSelectedDebateBySession((current) => ({ ...current, [session.id]: "" }));
      setAnalyticsBySession((current) => removeKey(current, session.id));
      setAnalyticsHistoryBySession((current) => ({ ...current, [session.id]: [] }));
      setStatusBySession((current) => ({
        ...current,
        [session.id]:
          mode === "history"
            ? "Visible chat history cleared. Memory kept."
            : "Chat history and memory cleared."
      }));
      setClearTarget(null);
      refreshSessions().catch(() => undefined);
    } catch (exc) {
      const message =
        exc instanceof Error
          ? exc.message
          : mode === "history"
            ? "Could not clear chat history."
            : "Could not clear chat memory.";
      setClearError(message);
      setError(message);
    } finally {
      setClearingSessionId(null);
    }
  }

  async function handleDebateChange(debateId: string) {
    if (!selectedId) {
      return;
    }
    const sessionId = selectedId;
    setSelectedDebateBySession((current) => ({ ...current, [sessionId]: debateId }));
    setAnalyticsHistoryBySession((current) => ({ ...current, [sessionId]: [] }));
    try {
      await refreshAnalytics(sessionId, debateId || undefined);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not load debate statistics.");
    }
  }

  async function handleRenameDebate(debate: DebateRecord, name: string) {
    const cleaned = name.trim();
    if (!selectedId || !cleaned || cleaned === debate.name) {
      return false;
    }
    const sessionId = selectedId;
    setRenamingDebateId(debate.id);
    setError(null);

    try {
      const renamed = await renameDebate(sessionId, debate.id, cleaned);
      setDebatesBySession((current) => ({
        ...current,
        [sessionId]: (current[sessionId] ?? []).map((item) =>
          item.id === renamed.id ? renamed : item
        )
      }));
      return true;
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not rename debate.");
      return false;
    } finally {
      setRenamingDebateId(null);
    }
  }

  async function handleConfirmDeleteDebate() {
    if (!deleteDebateTarget || deletingDebateId) {
      return;
    }
    const { session, debate } = deleteDebateTarget;
    setDeletingDebateId(debate.id);
    setDeleteDebateError(null);
    setError(null);

    try {
      await deleteDebateStatistics(session.id, debate.id);
      const nextDebates = (debatesBySession[session.id] ?? []).filter(
        (item) => item.id !== debate.id
      );
      setDebatesBySession((current) => ({ ...current, [session.id]: nextDebates }));
      const nextSelected = nextDebates[0]?.id ?? "";
      setSelectedDebateBySession((current) => ({ ...current, [session.id]: nextSelected }));
      setAnalyticsHistoryBySession((current) => ({ ...current, [session.id]: [] }));
      if (nextSelected) {
        await refreshAnalytics(session.id, nextSelected);
      } else {
        setAnalyticsBySession((current) => removeKey(current, session.id));
      }
      setDeleteDebateTarget(null);
      refreshSessions().catch(() => undefined);
    } catch (exc) {
      const message = exc instanceof Error ? exc.message : "Could not delete debate statistics.";
      setDeleteDebateError(message);
      setError(message);
    } finally {
      setDeletingDebateId(null);
    }
  }

  async function handleUpdateSettings(updates: Partial<SessionSettings>) {
    if (!selectedId) {
      return;
    }
    const sessionId = selectedId;
    setSettingsBySession((current) => ({
      ...current,
      ...(current[sessionId] ? { [sessionId]: { ...current[sessionId], ...updates } } : {})
    }));
    if (typeof updates.overall_model === "string") {
      setModelBySession((current) => ({ ...current, [sessionId]: updates.overall_model ?? "" }));
    }
    try {
      const saved = await updateSessionSettings(sessionId, updates);
      setSettingsBySession((current) => ({ ...current, [sessionId]: saved }));
      setModelBySession((current) => ({ ...current, [sessionId]: saved.overall_model }));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not save settings.");
      refreshSettings(sessionId).catch(() => undefined);
    }
  }

  function handleDraftChange(value: string) {
    if (!selectedId) {
      return;
    }
    setDraftBySession((current) => ({ ...current, [selectedId]: value }));
  }

  function handleModelChange(modelName: string) {
    if (!selectedId) {
      return;
    }
    setModelBySession((current) => ({ ...current, [selectedId]: modelName }));
    handleUpdateSettings({ overall_model: modelName }).catch(() => undefined);
  }

  function clearSocketRetry(sessionId: string) {
    const timer = retryTimerRefs.current[sessionId];
    if (timer) {
      clearTimeout(timer);
      delete retryTimerRefs.current[sessionId];
    }
  }

  function openInteractionSocket(
    sessionId: string,
    content: string,
    modelName: string,
    attempt: number
  ) {
    clearSocketRetry(sessionId);
    let serverStarted = false;
    let sentStart = false;
    let finished = false;
    const websocket = new WebSocket(`${WS_BASE}/ws/debates/${sessionId}`);
    socketRefs.current[sessionId] = websocket;

    websocket.onopen = () => {
      websocket.send(JSON.stringify({ type: "start_interaction", topic: content, model: modelName }));
      sentStart = true;
      recordRuntimeDiary("websocket opened", `Started interaction with ${modelName}.`, sessionId);
      setDraftBySession((current) => ({ ...current, [sessionId]: "" }));
      setStatusBySession((current) => ({
        ...current,
        [sessionId]: attempt > 0 ? "Reconnected. Council is working." : "Council is working."
      }));
    };

    websocket.onmessage = (event) => {
      serverStarted = true;
      const payload = JSON.parse(event.data) as DebateEvent;
      if (
        payload.type === "debate_completed" ||
        payload.type === "interaction_completed" ||
        payload.type === "error"
      ) {
        finished = true;
      }
      if (payload.type === "error") {
        recordRuntimeDiary("websocket server error", formatErrorMessage(payload.message), sessionId);
      }
      handleDebateEvent(sessionId, payload);
    };

    websocket.onerror = () => {
      recordRuntimeDiary("websocket error", "Browser reported a WebSocket error.", sessionId);
      if (!sentStart && !serverStarted && attempt < WEBSOCKET_CONNECT_RETRIES) {
        setStatusBySession((current) => ({
          ...current,
          [sessionId]: `Connection failed. Retrying (${attempt + 1}/${WEBSOCKET_CONNECT_RETRIES})...`
        }));
        return;
      }
      if (!finished) {
        setError("WebSocket connection failed.");
        setStatusBySession((current) => ({ ...current, [sessionId]: "Connection failed." }));
      }
    };

    websocket.onclose = () => {
      if (socketRefs.current[sessionId] === websocket) {
        delete socketRefs.current[sessionId];
      }
      if (finished) {
        recordRuntimeDiary("websocket closed", "Interaction completed and socket closed.", sessionId);
        return;
      }
      recordRuntimeDiary(
        "websocket closed early",
        serverStarted
          ? "Connection closed before the council finished."
          : "Connection closed before the council started.",
        sessionId
      );
      if (!sentStart && !serverStarted && attempt < WEBSOCKET_CONNECT_RETRIES) {
        retryTimerRefs.current[sessionId] = setTimeout(() => {
          openInteractionSocket(sessionId, content, modelName, attempt + 1);
        }, WEBSOCKET_RETRY_DELAY_MS);
        return;
      }
      setRunningBySession((current) => ({ ...current, [sessionId]: false }));
      setPartialBySession((current) => ({ ...current, [sessionId]: {} }));
      setStatusBySession((current) => ({
        ...current,
        [sessionId]: serverStarted
          ? "Connection dropped. Saved messages were reloaded."
          : "Connection closed before the council started."
      }));
      setError(
        serverStarted
          ? "WebSocket disconnected before the council finished. I reloaded saved messages; send again if you want to continue."
          : "WebSocket connection closed before the council started."
      );
      refreshMessages(sessionId).catch(() => undefined);
      refreshDebates(sessionId).catch(() => undefined);
      refreshAnalytics(sessionId).catch(() => undefined);
    };
  }

  function handleSend() {
    if (!selectedId || !selectedSession || runningBySession[selectedId]) {
      return;
    }
    const content = (draftBySession[selectedId] ?? "").trim();
    const modelName = selectedModelName;
    if (!content) {
      return;
    }
    if ((draftBySession[selectedId] ?? "").length > USER_INPUT_MAX_CHARS) {
      setError(`Please shorten your message to ${USER_INPUT_MAX_CHARS} characters or less.`);
      return;
    }
    if (!modelName) {
      setError("Choose one unlocked model before sending.");
      return;
    }

    const sessionId = selectedId;
    setError(null);
    setStatusBySession((current) => ({ ...current, [sessionId]: "Connecting the council..." }));
    setPartialBySession((current) => ({ ...current, [sessionId]: {} }));
    setAssignmentsBySession((current) => ({ ...current, [sessionId]: [] }));
    setRunningBySession((current) => ({ ...current, [sessionId]: true }));
    openInteractionSocket(sessionId, content, modelName, 0);
  }

  function handleDebateEvent(sessionId: string, event: DebateEvent) {
    if (event.type === "debate_started") {
      setAssignmentsBySession((current) => ({ ...current, [sessionId]: event.assignments }));
      setDebatesBySession((current) => {
        const currentDebates = current[sessionId] ?? [];
        const withoutCurrent = currentDebates.filter((debate) => debate.id !== event.debate.id);
        return { ...current, [sessionId]: [event.debate, ...withoutCurrent] };
      });
      setSelectedDebateBySession((current) => ({ ...current, [sessionId]: event.debate.id }));
      setAnalyticsBySession((current) => removeKey(current, sessionId));
      setAnalyticsHistoryBySession((current) => ({ ...current, [sessionId]: [] }));
      setStatusBySession((current) => ({
        ...current,
        [sessionId]: event.positions
          ? `${event.positions.pro} ${event.positions.con}`
          : `Pro argues that this position is correct: ${event.topic}. Con argues that this position is wrong or too weak: ${event.topic}.`
      }));
      return;
    }

    if (event.type === "interaction_started") {
      setAssignmentsBySession((current) => ({ ...current, [sessionId]: [] }));
      setStatusBySession((current) => ({ ...current, [sessionId]: "Chat response in progress." }));
      return;
    }

    if (event.type === "message_started") {
      setPartialBySession((current) => ({
        ...current,
        [sessionId]: {
          ...(current[sessionId] ?? {}),
          [event.stream_id]: event.message
        }
      }));
      return;
    }

    if (event.type === "message_delta") {
      setPartialBySession((current) => {
        const sessionPartials = current[sessionId] ?? {};
        const existing = sessionPartials[event.stream_id];
        if (!existing) {
          return current;
        }
        return {
          ...current,
          [sessionId]: {
            ...sessionPartials,
            [event.stream_id]: {
              ...existing,
              content: existing.content + event.delta
            }
          }
        };
      });
      return;
    }

    if (event.type === "message_replaced") {
      setPartialBySession((current) => {
        const sessionPartials = current[sessionId] ?? {};
        const existing = sessionPartials[event.stream_id];
        if (!existing) {
          return current;
        }
        return {
          ...current,
          [sessionId]: {
            ...sessionPartials,
            [event.stream_id]: {
              ...existing,
              content: event.content
            }
          }
        };
      });
      return;
    }

    if (event.type === "message_completed") {
      setMessagesBySession((current) => {
        const currentMessages = current[sessionId] ?? [];
        return {
          ...current,
          [sessionId]: [
            ...currentMessages.filter((message) => message.id !== event.message.id),
            event.message
          ].sort((left, right) => left.sequence - right.sequence)
        };
      });
      setPartialBySession((current) => {
        const sessionPartials = { ...(current[sessionId] ?? {}) };
        delete sessionPartials[event.stream_id];
        return { ...current, [sessionId]: sessionPartials };
      });
      return;
    }

    if (event.type === "analysis_updated") {
      setAnalyticsBySession((current) => ({ ...current, [sessionId]: event.analysis }));
      setAnalyticsHistoryBySession((current) => ({
        ...current,
        [sessionId]: mergeAnalyticsHistory(current[sessionId] ?? [], event.analysis)
      }));
      return;
    }

    if (event.type === "debate_completed" || event.type === "interaction_completed") {
      setStatusBySession((current) => ({
        ...current,
        [sessionId]: event.type === "debate_completed" ? "Judge verdict complete." : "Response complete."
      }));
      setRunningBySession((current) => ({ ...current, [sessionId]: false }));
      socketRefs.current[sessionId]?.close();
      refreshSessions().catch(() => undefined);
      refreshMessages(sessionId).catch(() => undefined);
      refreshDebates(sessionId).catch(() => undefined);
      refreshAnalytics(sessionId).catch(() => undefined);
      return;
    }

    if (event.type === "error") {
      setError(formatErrorMessage(event.message));
      setStatusBySession((current) => ({ ...current, [sessionId]: "Stopped." }));
      setRunningBySession((current) => ({ ...current, [sessionId]: false }));
      socketRefs.current[sessionId]?.close();
    }
  }

  return (
    <div className="flex h-screen min-h-screen flex-col md:flex-row">
      <Sidebar
        sessions={sessions}
        selectedId={selectedId}
        maxSessions={MAX_SESSIONS}
        onNew={handleNewSession}
        onSelect={handleSelect}
      />
      <DebateRoom
        selectedSession={selectedSession}
        messages={selectedMessages}
        partialMessages={selectedPartials}
        models={models}
        topic={selectedDraft}
        status={selectedStatus}
        error={error}
        assignments={selectedAssignments}
        debates={selectedDebates}
        selectedDebateId={selectedDebateId}
        analytics={selectedAnalytics}
        analyticsHistory={selectedAnalyticsHistory}
        settings={selectedSettings}
        isRunning={selectedRunning}
        selectedModelName={selectedModelName}
        activePanel={activePanel}
        renamingSessionId={renamingSessionId}
        onPanelChange={setActivePanel}
        onTopicChange={handleDraftChange}
        onModelChange={handleModelChange}
        onDebateChange={handleDebateChange}
        onSend={handleSend}
        onSettingsChange={handleUpdateSettings}
        onRename={handleRename}
        onRenameDebate={handleRenameDebate}
        onDeleteRequest={(session) => {
          setDeleteError(null);
          setDeleteTarget(session);
        }}
        onDeleteDebateRequest={(session, debate) => {
          setDeleteDebateError(null);
          setDeleteDebateTarget({ session, debate });
        }}
        onClearRequest={(session, mode) => {
          setClearError(null);
          setClearTarget({ session, mode });
        }}
      />
      {deleteTarget ? (
        <ConfirmDialog
          title="Delete chat"
          body={`Delete "${deleteTarget.name}"? This removes its messages and settings.`}
          confirmLabel="Delete"
          isWorking={deletingSessionId === deleteTarget.id}
          error={deleteError}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={handleConfirmDelete}
        />
      ) : null}
      {clearTarget ? (
        <ConfirmDialog
          title={
            clearTarget.mode === "history"
              ? "Clear chat history"
              : "Clear chat memory and history"
          }
          body={
            clearTarget.mode === "history"
              ? `Clear visible history for "${clearTarget.session.name}"? Messages, debates, and graphs will disappear from this chat, but Council Assistant memory will still be kept for future follow-ups.`
              : `Clear memory and visible history for "${clearTarget.session.name}"? Messages, debates, graphs, and saved chat memory for this chat will be permanently removed.`
          }
          confirmLabel={clearTarget.mode === "history" ? "Clear History" : "Clear Memory"}
          isWorking={clearingSessionId === clearTarget.session.id}
          error={clearError}
          onCancel={() => setClearTarget(null)}
          onConfirm={handleConfirmClear}
        />
      ) : null}
      {deleteDebateTarget ? (
        <ConfirmDialog
          title="Delete debate statistics"
          body={`Delete graphs and statistics for "${deleteDebateTarget.debate.name}"? The debate messages will stay visible in Debating Chats.`}
          confirmLabel="Delete Statistics"
          isWorking={deletingDebateId === deleteDebateTarget.debate.id}
          error={deleteDebateError}
          onCancel={() => setDeleteDebateTarget(null)}
          onConfirm={handleConfirmDeleteDebate}
        />
      ) : null}
    </div>
  );
}

function mergeAnalyticsHistory(history: DebateAnalytics[], next: DebateAnalytics) {
  const filtered = history.filter((item) => item.round !== next.round);
  return [...filtered, next].sort((left, right) => left.round - right.round);
}

function removeKey<T>(record: Record<string, T>, key: string) {
  const next = { ...record };
  delete next[key];
  return next;
}

function formatErrorMessage(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => formatErrorMessage(item)).join("; ");
  }
  if (value && typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "Something went wrong.";
    }
  }
  return String(value || "Something went wrong.");
}

function ConfirmDialog({
  title,
  body,
  confirmLabel,
  isWorking,
  error,
  onCancel,
  onConfirm
}: {
  title: string;
  body: string;
  confirmLabel: string;
  isWorking: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-md rounded-md border border-zinc-300 bg-white p-5 shadow-xl">
        <h2 className="text-lg font-semibold text-zinc-950">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-zinc-700">{body}</p>
        {error ? (
          <p className="mt-3 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </p>
        ) : null}
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={isWorking}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-100"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isWorking}
            className="rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            {isWorking ? "Deleting..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
