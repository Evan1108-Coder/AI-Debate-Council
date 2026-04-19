"use client";

import type { ChatSession } from "@/types";

type SidebarProps = {
  sessions: ChatSession[];
  selectedId: string | null;
  maxSessions: number;
  onNew: () => void;
  onSelect: (id: string) => void;
  onCouncilSettings: () => void;
  councilSettingsActive: boolean;
};

export function Sidebar({
  sessions,
  selectedId,
  maxSessions,
  onNew,
  onSelect,
  onCouncilSettings,
  councilSettingsActive
}: SidebarProps) {
  const limitReached = sessions.length >= maxSessions;

  return (
    <aside className="flex h-full w-full flex-col border-r border-zinc-300 bg-white md:w-80">
      <div className="border-b border-zinc-300 p-4">
        <img
          src="https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=640&q=80"
          alt=""
          className="mb-3 h-24 w-full rounded-md object-cover"
        />
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-zinc-950">AI Debate Council</h1>
            <p className="text-sm text-zinc-600">{sessions.length}/10 sessions</p>
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
        {limitReached ? (
          <p className="mt-2 text-sm text-red-700">Delete a session before creating another.</p>
        ) : null}
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto p-3">
        {sessions.length === 0 ? (
          <p className="px-2 py-3 text-sm text-zinc-600">Create a session to begin.</p>
        ) : null}

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
      </nav>

      <div className="border-t border-zinc-300 p-3">
        <button
          type="button"
          onClick={onCouncilSettings}
          className={`flex w-full items-center justify-between rounded-md px-3 py-3 text-left text-sm font-semibold ${
            councilSettingsActive
              ? "bg-zinc-950 text-white"
              : "text-zinc-800 hover:bg-zinc-100"
          }`}
        >
          <span>Council Settings</span>
          <span aria-hidden="true">⚙</span>
        </button>
      </div>
    </aside>
  );
}
