const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

export async function fetchModels(): Promise<string[]> {
  const data = await fetchAPI("/api/models");
  return data.models;
}

export async function fetchSessions() {
  return fetchAPI("/api/sessions");
}

export async function createSession(model?: string) {
  return fetchAPI("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ model: model || "gpt-4o" }),
  });
}

export async function deleteSession(id: number) {
  return fetchAPI(`/api/sessions/${id}`, { method: "DELETE" });
}

export async function renameSession(id: number, name: string) {
  return fetchAPI(`/api/sessions/${id}/rename`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export async function updateSessionModel(id: number, model: string) {
  return fetchAPI(`/api/sessions/${id}/model`, {
    method: "PATCH",
    body: JSON.stringify({ model }),
  });
}

export async function fetchMessages(sessionId: number) {
  const data = await fetchAPI(`/api/sessions/${sessionId}/messages`);
  return data.messages;
}

export function getWebSocketURL(sessionId: number): string {
  const wsBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    .replace("http://", "ws://")
    .replace("https://", "wss://");
  return `${wsBase}/ws/debate/${sessionId}`;
}
