"use client";

import type { ChatSession } from "@/types";

export type SidebarWorkspaceView =
  | "session"
  | "aiExperiences"
  | "userProfile"
  | "councilSettings";

type SidebarProps = {
  sessions: ChatSession[];
  selectedId: string | null;
  maxSessions: number;
  workspaceView: SidebarWorkspaceView;
  onNew: () => void;
  onDeleteAll: () => void;
  onSelect: (id: string) => void;
  onAiExperiences: () => void;
  onUserProfile: () => void;
  onCouncilSettings: () => void;
};

export function Sidebar({
  sessions,
  selectedId,
  maxSessions,
  workspaceView,
  onNew,
  onDeleteAll,
  onSelect,
  onAiExperiences,
  onUserProfile,
  onCouncilSettings,
}: SidebarProps) {
  const limitReached = sessions.length >= maxSessions;
  const aiSessions = sessions.filter((session) => session.mode !== "ai_vs_human");
  const practiceSessions = sessions.filter((session) => session.mode === "ai_vs_human");

  return (
    <aside className="flex h-full w-full flex-col border-r border-zinc-300 bg-white md:w-80">
      <div className="border-b border-zinc-300 p-4">
        <div className="mb-3 rounded-md border border-zinc-300 bg-zinc-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Debate Coach
          </p>
          <p className="mt-2 text-sm leading-6 text-zinc-700">
            Train like a debater, inspect the council, and keep real memory across the whole workspace.
          </p>
        </div>
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-zinc-950">AI Debate Coach & Council</h1>
            <p className="text-sm text-zinc-600">{sessions.length}/{maxSessions} sessions</p>
          </div>
          <button
            type="button"
            onClick={onNew}
            disabled={limitReached}
            className="rounded-md bg-zinc-950 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            New
          </button>
        </div>
        {sessions.length > 0 ? (
          <button
            type="button"
            onClick={onDeleteAll}
            className="mt-3 rounded-md border border-red-300 px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50"
          >
            Delete All Chats
          </button>
        ) : null}
        {limitReached ? (
          <p className="mt-2 text-sm text-red-700">Delete a session before creating another.</p>
        ) : null}
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto p-3">
        {sessions.length === 0 && workspaceView === "session" ? (
          <p className="px-2 py-3 text-sm text-zinc-600">Create a session to begin.</p>
        ) : null}

        <SessionGroup
          title="AI vs AI"
          sessions={aiSessions}
          selectedId={workspaceView === "session" ? selectedId : null}
          onSelect={onSelect}
        />
        <SessionGroup
          title="AI vs Human"
          sessions={practiceSessions}
          selectedId={workspaceView === "session" ? selectedId : null}
          onSelect={onSelect}
        />

        <div className="mt-6 border-t border-zinc-200 pt-4">
          <p className="mb-2 px-2 text-xs font-semibold uppercase text-zinc-500">
            Global Intelligence
          </p>
          <div className="space-y-2">
            <SidebarButton
              label="AI Debater Experiences"
              active={workspaceView === "aiExperiences"}
              onClick={onAiExperiences}
            />
            <SidebarButton
              label="User Debate Profile"
              active={workspaceView === "userProfile"}
              onClick={onUserProfile}
            />
          </div>
        </div>
      </nav>

      <div className="border-t border-zinc-300 p-3">
        <button
          type="button"
          onClick={onCouncilSettings}
          className={`flex w-full items-center justify-between rounded-md px-3 py-3 text-left text-sm font-semibold ${
            workspaceView === "councilSettings"
              ? "bg-zinc-950 text-white"
              : "text-zinc-800 hover:bg-zinc-100"
          }`}
        >
          <span>Council Settings</span>
          <span aria-hidden="true" className="text-2xl leading-none">
            ⚙
          </span>
        </button>
      </div>
    </aside>
  );
}

function SidebarButton({
  label,
  active,
  onClick
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`block w-full rounded-md px-3 py-3 text-left text-sm font-semibold ${
        active ? "bg-zinc-950 text-white" : "text-zinc-800 hover:bg-zinc-100"
      }`}
    >
      {label}
    </button>
  );
}

function SessionGroup({
  title,
  sessions,
  selectedId,
  onSelect
}: {
  title: string;
  sessions: ChatSession[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  if (sessions.length === 0) {
    return null;
  }
  return (
    <div className="mb-4">
      <p className="mb-2 px-2 text-xs font-semibold uppercase text-zinc-500">{title}</p>
      <div className="space-y-2">
        {sessions.map((session) => {
          const selected = selectedId === session.id;
          return (
            <div
              key={session.id}
              className={`rounded-md border p-2 ${
                selected ? "border-zinc-950 bg-zinc-100" : "border-zinc-300 bg-white"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(session.id)}
                className="block w-full truncate rounded px-2 py-2 text-left text-sm font-medium text-zinc-950 hover:bg-zinc-100"
                title={session.name}
              >
                {session.name}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
