import type {
  ChatSession,
  DebateAnalytics,
  DebateMessage,
  DebateRecord,
  ModelsResponse,
  SessionSettings
} from "@/types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, "") ??
  API_BASE.replace(/^http/, "ws");

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {})
      }
    });
  } catch (error) {
    const message =
      error instanceof Error && error.message !== "Failed to fetch" ? ` ${error.message}` : "";
    throw new Error(
      `Backend is not reachable at ${API_BASE}.${message} Start the FastAPI server on port 8000, then try again.`
    );
  }

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = formatApiError(body.detail ?? body.message ?? message);
    } catch {
      // Keep the HTTP status text when no JSON body is available.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getModels() {
  return request<ModelsResponse>("/api/models");
}

export function listSessions() {
  return request<ChatSession[]>("/api/sessions");
}

export function createSession() {
  return request<ChatSession>("/api/sessions", { method: "POST" });
}

export function renameSession(sessionId: string, name: string) {
  return request<ChatSession>(`/api/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ name })
  });
}

export function deleteSession(sessionId: string) {
  return request<void>(`/api/sessions/${sessionId}`, { method: "DELETE" });
}

export function clearSessionHistory(sessionId: string) {
  return request<void>(`/api/sessions/${sessionId}/clear-history`, { method: "POST" });
}

export function clearSessionMemory(sessionId: string) {
  return request<void>(`/api/sessions/${sessionId}/clear-memory`, { method: "POST" });
}

export function listMessages(sessionId: string) {
  return request<DebateMessage[]>(`/api/sessions/${sessionId}/messages`);
}

export function listDebates(sessionId: string) {
  return request<DebateRecord[]>(`/api/sessions/${sessionId}/debates`);
}

export function renameDebate(sessionId: string, debateId: string, name: string) {
  return request<DebateRecord>(`/api/sessions/${sessionId}/debates/${debateId}`, {
    method: "PATCH",
    body: JSON.stringify({ name })
  });
}

export function deleteDebateStatistics(sessionId: string, debateId: string) {
  return request<void>(`/api/sessions/${sessionId}/debates/${debateId}`, { method: "DELETE" });
}

export function getSessionSettings(sessionId: string) {
  return request<SessionSettings>(`/api/sessions/${sessionId}/settings`);
}

export function updateSessionSettings(sessionId: string, updates: Partial<SessionSettings>) {
  return request<SessionSettings>(`/api/sessions/${sessionId}/settings`, {
    method: "PATCH",
    body: JSON.stringify(updates)
  });
}

export function getSessionAnalytics(sessionId: string, debateId?: string) {
  const suffix = debateId ? `?debate_id=${encodeURIComponent(debateId)}` : "";
  return request<DebateAnalytics>(`/api/sessions/${sessionId}/analytics${suffix}`);
}

function formatApiError(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          const record = item as Record<string, unknown>;
          const location = Array.isArray(record.loc) ? record.loc.join(".") : "";
          const message = typeof record.msg === "string" ? record.msg : JSON.stringify(record);
          return location ? `${location}: ${message}` : message;
        }
        return String(item);
      })
      .join("; ");
  }
  if (value && typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "Request failed.";
    }
  }
  return String(value || "Request failed.");
}
