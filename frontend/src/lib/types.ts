export interface Session {
  id: number;
  name: string;
  session_number: number;
  model: string;
  topic: string | null;
  status: "idle" | "debating" | "completed";
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  session_id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface DebateEvent {
  type: "status" | "round" | "debater_start" | "debater_end" | "token" | "complete" | "error";
  message?: string;
  role?: string;
  content?: string;
  round?: number;
  total_rounds?: number;
  topic?: string;
}

export const ROLE_COLORS: Record<string, string> = {
  Advocate: "text-green-400",
  Critic: "text-red-400",
  Researcher: "text-blue-400",
  "Devil's Advocate": "text-amber-400",
  Judge: "text-purple-400",
  user: "text-indigo-400",
};

export const ROLE_BG_COLORS: Record<string, string> = {
  Advocate: "bg-green-500/10 border-green-500/30",
  Critic: "bg-red-500/10 border-red-500/30",
  Researcher: "bg-blue-500/10 border-blue-500/30",
  "Devil's Advocate": "bg-amber-500/10 border-amber-500/30",
  Judge: "bg-purple-500/10 border-purple-500/30",
  user: "bg-indigo-500/10 border-indigo-500/30",
};

export const ROLE_ICONS: Record<string, string> = {
  Advocate: "\u2705",
  Critic: "\u274C",
  Researcher: "\uD83D\uDD0D",
  "Devil's Advocate": "\uD83D\uDE08",
  Judge: "\u2696\uFE0F",
  user: "\uD83D\uDCAC",
};
