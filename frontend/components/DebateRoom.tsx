"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import type {
  ChatSession,
  DebateAnalytics,
  DebateAssignment,
  DebateMessage,
  DebateRecord,
  ModelsResponse,
  SessionSettings,
  SupportedModel
} from "@/types";

export type RoomPanel = "chat" | "stats" | "settings";

type DebateRoomProps = {
  selectedSession: ChatSession | null;
  messages: DebateMessage[];
  partialMessages: Record<string, DebateMessage>;
  models: ModelsResponse | null;
  topic: string;
  status: string;
  error: string | null;
  assignments: DebateAssignment[];
  debates: DebateRecord[];
  selectedDebateId: string;
  analytics: DebateAnalytics | null;
  analyticsHistory: DebateAnalytics[];
  settings: SessionSettings | null;
  isRunning: boolean;
  selectedModelName: string;
  activePanel: RoomPanel;
  renamingSessionId: string | null;
  onPanelChange: (panel: RoomPanel) => void;
  onTopicChange: (topic: string) => void;
  onModelChange: (modelName: string) => void;
  onDebateChange: (debateId: string) => void;
  onSend: () => void;
  onSettingsChange: (updates: Partial<SessionSettings>) => void;
  onRename: (session: ChatSession, name: string) => Promise<boolean>;
  onRenameDebate: (debate: DebateRecord, name: string) => Promise<boolean>;
  onDeleteRequest: (session: ChatSession) => void;
  onDeleteDebateRequest: (session: ChatSession, debate: DebateRecord) => void;
  onClearRequest: (session: ChatSession, mode: "history" | "memory") => void;
};

const roleStyles: Record<string, string> = {
  user: "border-l-4 border-l-zinc-950",
  assistant: "border-l-4 border-l-cyan-700",
  advocate: "border-l-4 border-l-emerald-600",
  critic: "border-l-4 border-l-red-600",
  researcher: "border-l-4 border-l-cyan-700",
  devils_advocate: "border-l-4 border-l-yellow-500",
  pro_lead_advocate: "border-l-4 border-l-emerald-600",
  pro_rebuttal_critic: "border-l-4 border-l-emerald-700",
  pro_evidence_researcher: "border-l-4 border-l-cyan-700",
  pro_cross_examiner: "border-l-4 border-l-teal-700",
  con_lead_advocate: "border-l-4 border-l-red-600",
  con_rebuttal_critic: "border-l-4 border-l-rose-700",
  con_evidence_researcher: "border-l-4 border-l-sky-700",
  con_cross_examiner: "border-l-4 border-l-amber-600",
  judge_assistant: "border-l-4 border-l-zinc-500",
  judge: "border-l-4 border-l-zinc-950"
};

const panels: Array<{ id: RoomPanel; label: string }> = [
  { id: "chat", label: "Debating Chats" },
  { id: "stats", label: "Graphs & Statistics" },
  { id: "settings", label: "Chat Settings" }
];

const teamRoleSettings = [
  {
    key: "lead_advocate",
    label: "Lead Advocate",
    minDebaters: 1,
    description: "Builds the main case for each team."
  },
  {
    key: "rebuttal_critic",
    label: "Rebuttal Critic",
    minDebaters: 2,
    description: "Attacks the other team's strongest claims."
  },
  {
    key: "evidence_researcher",
    label: "Evidence Researcher",
    minDebaters: 3,
    description: "Adds evidence, context, and uncertainty notes."
  },
  {
    key: "cross_examiner",
    label: "Cross-Examiner",
    minDebaters: 4,
    description: "Asks pressure questions and exposes contradictions."
  }
];

const neutralRoleSettings = [
  {
    key: "judge_assistant",
    label: "Judge Assistant",
    description: "Audits missed points and statistics before the verdict."
  },
  {
    key: "judge",
    label: "Judge",
    description: "Makes the final decision."
  }
];

export function DebateRoom({
  selectedSession,
  messages,
  partialMessages,
  models,
  topic,
  status,
  error,
  assignments,
  debates,
  selectedDebateId,
  analytics,
  analyticsHistory,
  settings,
  isRunning,
  selectedModelName,
  activePanel,
  renamingSessionId,
  onPanelChange,
  onTopicChange,
  onModelChange,
  onDebateChange,
  onSend,
  onSettingsChange,
  onRename,
  onRenameDebate,
  onDeleteRequest,
  onDeleteDebateRequest,
  onClearRequest
}: DebateRoomProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const partialList = Object.values(partialMessages);
  const unlockedModels = models?.models ?? [];
  const canSend =
    Boolean(selectedSession) &&
    Boolean(selectedModelName) &&
    topic.trim().length > 0 &&
    !isRunning &&
    unlockedModels.length > 0;

  useEffect(() => {
    if (settings?.auto_scroll && activePanel === "chat") {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, partialList.length, settings?.auto_scroll, activePanel]);

  if (!selectedSession) {
    return (
      <main className="flex h-full min-w-0 flex-1 items-center justify-center bg-[#f5f7f6] p-6">
        <p className="max-w-md text-center text-xl font-semibold text-zinc-950">
          Once you create a session, it will show the contents here.
        </p>
      </main>
    );
  }

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-[#f5f7f6]">
      <section className="border-b border-zinc-300 bg-white p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium text-emerald-700">Council room</p>
            <h2 className="truncate text-2xl font-semibold text-zinc-950">
              {selectedSession?.name ?? "No session selected"}
            </h2>
            <p className="mt-1 text-sm text-zinc-600">{status}</p>
          </div>

          <ProviderReadiness models={models} />
        </div>
      </section>

      <div className="min-h-0 flex flex-1">
        <aside className="hidden w-52 shrink-0 border-r border-zinc-300 bg-white p-3 lg:block">
          <div className="space-y-2">
            {panels.map((panel) => (
              <button
                key={panel.id}
                type="button"
                onClick={() => onPanelChange(panel.id)}
                className={`w-full rounded-md px-3 py-3 text-left text-sm font-semibold ${
                  activePanel === panel.id
                    ? "bg-zinc-950 text-white"
                    : "text-zinc-700 hover:bg-zinc-100"
                }`}
              >
                {panel.label}
              </button>
            ))}
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <div className="border-b border-zinc-300 bg-white p-2 lg:hidden">
            <div className="grid grid-cols-3 gap-2">
              {panels.map((panel) => (
                <button
                  key={panel.id}
                  type="button"
                  onClick={() => onPanelChange(panel.id)}
                  className={`rounded-md px-2 py-2 text-xs font-semibold ${
                    activePanel === panel.id
                      ? "bg-zinc-950 text-white"
                      : "border border-zinc-300 text-zinc-700"
                  }`}
                >
                  {panel.label}
                </button>
              ))}
            </div>
          </div>

          {activePanel === "chat" ? (
            <>
              <section className="min-h-0 flex-1 overflow-y-auto p-4">
                {assignments.length > 0 ? <AssignmentStrip assignments={assignments} /> : null}
                {messages.length === 0 && partialList.length === 0 ? (
                  <div className="mx-auto flex h-full max-w-2xl flex-col justify-center text-center">
                    <p className="text-2xl font-semibold text-zinc-950">
                      Bring a question to the table.
                    </p>
                    <p className="mt-2 text-zinc-600">
                      Ask normally, or request a debate when you want the council to argue.
                    </p>
                  </div>
                ) : (
                  <div className="mx-auto flex max-w-4xl flex-col gap-3">
                    {messages.map((message) => (
                      <MessageBubble key={message.id} message={message} settings={settings} />
                    ))}
                    {partialList.map((message) => (
                      <MessageBubble key={message.id} message={message} settings={settings} pending />
                    ))}
                    <div ref={bottomRef} />
                  </div>
                )}
              </section>

              <Composer
                models={models}
                topic={topic}
                selectedModelName={selectedModelName}
                isRunning={isRunning}
                canSend={canSend}
                error={error}
                onTopicChange={onTopicChange}
                onModelChange={onModelChange}
                onSend={onSend}
              />
            </>
          ) : null}

          {activePanel === "stats" ? (
            <StatsPanel
              analytics={analytics}
              history={analyticsHistory}
              debates={debates}
              selectedDebateId={selectedDebateId}
              onDebateChange={onDebateChange}
            />
          ) : null}

          {activePanel === "settings" ? (
            <SettingsPanel
              session={selectedSession}
              settings={settings}
              models={models}
              selectedModelName={selectedModelName}
              isRenaming={renamingSessionId === selectedSession?.id}
              isRunning={isRunning}
              debates={debates}
              onModelChange={onModelChange}
              onSettingsChange={onSettingsChange}
              onRename={onRename}
              onRenameDebate={onRenameDebate}
              onDeleteRequest={onDeleteRequest}
              onDeleteDebateRequest={onDeleteDebateRequest}
              onClearRequest={onClearRequest}
            />
          ) : null}
        </section>
      </div>
    </main>
  );
}

function ProviderReadiness({ models }: { models: ModelsResponse | null }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:w-[520px]">
      {models?.providers.map((provider) => (
        <div
          key={provider.provider}
          className="flex items-center justify-between gap-3 rounded-md border border-zinc-300 bg-[#fbfcfb] px-3 py-2"
        >
          <span className="truncate text-sm font-medium text-zinc-900">
            {provider.provider_label}
          </span>
          <span
            className={`shrink-0 rounded px-2 py-1 text-xs font-semibold ${
              provider.configured ? "bg-emerald-100 text-emerald-800" : "bg-zinc-200 text-zinc-700"
            }`}
          >
            {provider.configured ? `${provider.unlocked_model_count} unlocked` : provider.api_key_env}
          </span>
        </div>
      ))}
    </div>
  );
}

function AssignmentStrip({ assignments }: { assignments: DebateAssignment[] }) {
  return (
    <div className="mx-auto mb-4 grid max-w-4xl gap-2 sm:grid-cols-2 xl:grid-cols-5">
      {assignments.map((assignment) => (
        <div key={assignment.role} className="rounded-md border border-zinc-300 bg-white p-3">
          <p className="text-sm font-semibold text-zinc-950">{assignment.speaker}</p>
          <p className="mt-1 truncate text-xs text-zinc-600" title={assignment.model}>
            {assignment.model}
          </p>
        </div>
      ))}
    </div>
  );
}

function Composer({
  models,
  topic,
  selectedModelName,
  isRunning,
  canSend,
  error,
  onTopicChange,
  onModelChange,
  onSend
}: {
  models: ModelsResponse | null;
  topic: string;
  selectedModelName: string;
  isRunning: boolean;
  canSend: boolean;
  error: string | null;
  onTopicChange: (topic: string) => void;
  onModelChange: (modelName: string) => void;
  onSend: () => void;
}) {
  const unlockedModels = models?.models ?? [];
  const modelsByProvider = unlockedModels.reduce<Record<string, typeof unlockedModels>>(
    (groups, model) => {
      const provider = model.provider_label;
      groups[provider] = groups[provider] ?? [];
      groups[provider].push(model);
      return groups;
    },
    {}
  );

  return (
    <section className="border-t border-zinc-300 bg-white p-4">
      <div className="mx-auto max-w-4xl">
        {error ? (
          <p className="mb-3 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </p>
        ) : null}
        <div className="mb-3 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <label htmlFor="model" className="mb-2 block text-sm font-medium text-zinc-900">
              Overall Model
            </label>
            <select
              id="model"
              value={selectedModelName}
              onChange={(event) => onModelChange(event.target.value)}
              disabled={unlockedModels.length === 0 || isRunning}
              className="h-12 w-full rounded-md border border-zinc-300 bg-white px-3 text-zinc-950 disabled:cursor-not-allowed disabled:bg-zinc-100 disabled:text-zinc-500"
            >
              {unlockedModels.length === 0 ? <option value="">No unlocked models</option> : null}
              {Object.entries(modelsByProvider).map(([provider, providerModels]) => (
                <optgroup key={provider} label={provider}>
                  {providerModels.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          <p className="text-sm text-zinc-600 md:max-w-xs">
            The router decides whether this is a normal chat or a debate.
          </p>
        </div>
        <label htmlFor="topic" className="mb-2 block text-sm font-medium text-zinc-900">
          Message
        </label>
        <div className="flex flex-col gap-3 md:flex-row">
          <textarea
            id="topic"
            value={topic}
            onChange={(event) => onTopicChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                if (canSend) {
                  onSend();
                }
              }
            }}
            placeholder="Say hello, ask a follow-up, or ask the council to debate a topic."
            rows={3}
            className="min-h-24 flex-1 resize-none rounded-md border border-zinc-300 bg-white px-3 py-3 text-zinc-950 placeholder:text-zinc-500"
          />
          <button
            type="button"
            onClick={onSend}
            disabled={!canSend}
            className="h-12 rounded-md bg-emerald-700 px-5 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-zinc-400 md:h-auto"
          >
            {isRunning ? "Working" : "Send"}
          </button>
        </div>
        <p className="mt-2 text-sm text-zinc-600">
          {models?.mock_mode
            ? "Mock responses are enabled."
            : `${models?.available_model_count ?? 0} unlocked model(s). One is required.`}
        </p>
      </div>
    </section>
  );
}

function MessageBubble({
  message,
  settings,
  pending = false
}: {
  message: DebateMessage;
  settings: SessionSettings | null;
  pending?: boolean;
}) {
  return (
    <article
      className={`rounded-md border border-zinc-300 bg-white p-4 ${
        roleStyles[message.role] ?? "border-l-4 border-l-zinc-400"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-zinc-950">{message.speaker}</h3>
        <span className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-600">{message.model}</span>
        {settings?.show_timestamps ? (
          <span className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-600">
            {new Date(message.created_at).toLocaleTimeString()}
          </span>
        ) : null}
        {settings?.show_token_count ? (
          <span className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-600">
            {estimateTokens(message.content)} tokens
          </span>
        ) : null}
        {pending ? (
          <span className="rounded bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800">
            Streaming
          </span>
        ) : null}
      </div>
      <MarkdownText text={message.content || "Thinking..."} />
    </article>
  );
}

function StatsPanel({
  analytics,
  history,
  debates,
  selectedDebateId,
  onDebateChange
}: {
  analytics: DebateAnalytics | null;
  history: DebateAnalytics[];
  debates: DebateRecord[];
  selectedDebateId: string;
  onDebateChange: (debateId: string) => void;
}) {
  if (!analytics) {
    return (
      <section className="min-h-0 flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-semibold text-zinc-950">Graphs & Statistics</h2>
          <p className="mt-2 text-zinc-600">
            Start a debate to generate real analytics from the council transcript.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-0 flex-1 overflow-y-auto p-4">
      <div className="mx-auto max-w-6xl">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-zinc-950">Graphs & Statistics</h2>
            <p className="text-sm text-zinc-600">
              Round {analytics.round} from {analytics.turn_count} debater turn(s)
            </p>
            {analytics.source ? (
              <p className="text-xs text-zinc-500">
                {analytics.source.name || "Selected debate"} statistics. This chat has{" "}
                {analytics.source.debate_count} saved debate(s).
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-2 sm:items-end">
            {debates.length >= 2 ? (
              <label className="text-sm font-medium text-zinc-900">
                Switch Debate
                <select
                  value={selectedDebateId || analytics.source?.debate_id || ""}
                  onChange={(event) => onDebateChange(event.target.value)}
                  className="mt-1 h-10 w-full rounded-md border border-zinc-300 bg-white px-3 sm:w-64"
                >
                  {debates.map((debate) => (
                    <option key={debate.id} value={debate.id}>
                      {debate.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <p className="text-sm font-medium text-emerald-800">
              MoE lead: {analytics.mixture_of_experts.lead_expert ?? "Pending"}
            </p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Weighted vote" value={analytics.ensemble.weighted_vote} />
          <Metric label="Bayesian leader" value={analytics.bayesian.leader} />
          <Metric label="Confidence" value={toPercent(analytics.confidence.average)} />
          <Metric label="Convergence" value={toPercent(analytics.delphi.convergence)} />
        </div>

        <div className="mt-3 grid gap-3 xl:grid-cols-3">
          <Panel title="Bayesian pie">
            <PieChart values={analytics.bayesian.probabilities} />
          </Panel>
          <Panel title="Role weights">
            {Object.entries(analytics.mixture_of_experts.role_weights).map(([role, value]) => (
              <Bar key={role} label={role.replace("_", " ")} value={value} />
            ))}
          </Panel>
          <Panel title="Stance votes">
            {Object.entries(analytics.ensemble.weighted_votes).map(([label, value]) => (
              <Bar key={label} label={label} value={value / maxVote(analytics)} />
            ))}
          </Panel>
        </div>

        <div className="mt-3 grid gap-3 xl:grid-cols-[2fr_1fr]">
          <Panel title="Bayesian trend">
            <LineChart history={history.length > 0 ? history : [analytics]} />
          </Panel>
          <Panel title="Game and graph">
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="text-zinc-500">Auction</dt>
              <dd className="truncate text-right font-medium text-zinc-900">
                {analytics.game_theory.auction_winner ?? "Pending"}
              </dd>
              <dt className="text-zinc-500">Pressure</dt>
              <dd className="text-right font-medium text-zinc-900">
                {toPercent(analytics.game_theory.nash_pressure)}
              </dd>
              <dt className="text-zinc-500">Nodes</dt>
              <dd className="text-right font-medium text-zinc-900">
                {analytics.argument_graph.node_count}
              </dd>
              <dt className="text-zinc-500">Edges</dt>
              <dd className="text-right font-medium text-zinc-900">
                {analytics.argument_graph.support_edges} support,{" "}
                {analytics.argument_graph.attack_edges} attack
              </dd>
            </dl>
          </Panel>
        </div>

        <div className="mt-3 grid gap-3 xl:grid-cols-2">
          <Panel title="Argument mining">
            <p className="text-sm text-zinc-700">
              {analytics.argument_mining.evidence_count} evidence cue(s),{" "}
              {analytics.argument_mining.rebuttal_count} rebuttal cue(s),{" "}
              {analytics.argument_mining.redundancy_count} redundant turn(s)
            </p>
            <div className="mt-2 space-y-2">
              {analytics.argument_graph.strongest_claims.map((claim, index) => (
                <p key={`${claim.speaker}-${index}`} className="text-sm text-zinc-900">
                  <span className="font-semibold">{claim.speaker}:</span> {claim.text}
                </p>
              ))}
            </div>
          </Panel>
          <Panel title="Attention terms">
            <div className="flex flex-wrap gap-2">
              {analytics.attention.top_terms.map((term) => (
                <span key={term} className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                  {term}
                </span>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </section>
  );
}

function SettingsPanel({
  session,
  settings,
  models,
  selectedModelName,
  isRenaming,
  isRunning,
  debates,
  onModelChange,
  onSettingsChange,
  onRename,
  onRenameDebate,
  onDeleteRequest,
  onDeleteDebateRequest,
  onClearRequest
}: {
  session: ChatSession | null;
  settings: SessionSettings | null;
  models: ModelsResponse | null;
  selectedModelName: string;
  isRenaming: boolean;
  isRunning: boolean;
  debates: DebateRecord[];
  onModelChange: (modelName: string) => void;
  onSettingsChange: (updates: Partial<SessionSettings>) => void;
  onRename: (session: ChatSession, name: string) => Promise<boolean>;
  onRenameDebate: (debate: DebateRecord, name: string) => Promise<boolean>;
  onDeleteRequest: (session: ChatSession) => void;
  onDeleteDebateRequest: (session: ChatSession, debate: DebateRecord) => void;
  onClearRequest: (session: ChatSession, mode: "history" | "memory") => void;
}) {
  const [title, setTitle] = useState(session?.name ?? "");
  const [renameNotice, setRenameNotice] = useState<string | null>(null);
  const unlockedModels = models?.models ?? [];

  useEffect(() => {
    setTitle(session?.name ?? "");
    setRenameNotice(null);
  }, [session?.id, session?.name]);

  if (!session || !settings) {
    return (
      <section className="min-h-0 flex-1 overflow-y-auto p-6">
        <p className="text-zinc-600">Select a chat to edit settings.</p>
      </section>
    );
  }

  const handleRenameClick = async () => {
    setRenameNotice(null);
    const saved = await onRename(session, title);
    if (saved) {
      setTitle(title.trim());
      setRenameNotice("Chat title updated.");
    }
  };

  const updateAgentSetting = (
    roleKey: string,
    updates: Partial<SessionSettings["agent_settings"][string]>
  ) => {
    const currentAgent = settings.agent_settings[roleKey] ?? {
      model: "",
      temperature: settings.temperature,
      max_tokens: settings.max_tokens,
      response_length: settings.response_length,
      web_search: false,
      always_on: false
    };
    onSettingsChange({
      agent_settings: {
        ...settings.agent_settings,
        [roleKey]: { ...currentAgent, ...updates }
      }
    });
  };

  const visibleTeamRoles = teamRoleSettings.filter(
    (role) => role.minDebaters <= settings.debaters_per_team
  );
  const visibleNeutralRoles = neutralRoleSettings.filter(
    (role) => role.key !== "judge_assistant" || settings.judge_assistant_enabled
  );

  return (
    <section className="min-h-0 flex-1 overflow-y-auto p-4">
      <div className="mx-auto max-w-5xl space-y-4">
        <h2 className="text-2xl font-semibold text-zinc-950">Chat Settings</h2>

        <Panel title="Chat meta">
          <label className="block text-sm font-medium text-zinc-900" htmlFor="chat-title">
            Chat title
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              id="chat-title"
              value={title}
              onChange={(event) => {
                setTitle(event.target.value);
                setRenameNotice(null);
              }}
              className="h-11 flex-1 rounded-md border border-zinc-300 px-3"
            />
            <button
              type="button"
              onClick={handleRenameClick}
              disabled={isRenaming || !title.trim() || title.trim() === session.name}
              className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-zinc-400"
            >
              {isRenaming ? "Renaming..." : "Rename Chat"}
            </button>
            <button
              type="button"
              onClick={() => onDeleteRequest(session)}
              className="rounded-md border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50"
            >
              Delete Chat
            </button>
          </div>
          {renameNotice ? <p className="mt-2 text-sm text-emerald-700">{renameNotice}</p> : null}
        </Panel>

        <Panel title="History & memory">
          <p className="text-sm text-zinc-600">
            Clear Chat History hides the visible transcript and graphs, but keeps the hidden memory
            available for follow-up questions. Clear Chat Memory removes both visible history and
            saved memory for this chat.
          </p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => onClearRequest(session, "history")}
              disabled={isRunning}
              className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-semibold text-zinc-800 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:bg-zinc-100 disabled:text-zinc-500"
            >
              Clear Chat History
            </button>
            <button
              type="button"
              onClick={() => onClearRequest(session, "memory")}
              disabled={isRunning}
              className="rounded-md border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-100 disabled:text-zinc-500"
            >
              Clear Chat Memory (Also History)
            </button>
          </div>
          {isRunning ? (
            <p className="mt-2 text-sm text-zinc-600">
              Clearing is disabled while this chat is working.
            </p>
          ) : null}
        </Panel>

        <Panel title="Debates In Chat">
          {debates.length === 0 ? (
            <p className="text-sm text-zinc-600">
              No saved debate statistics yet. New debates will appear here as Debate #1, Debate #2,
              and so on.
            </p>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-zinc-600">
                Rename or delete saved statistics for debates in this chat. Deleting a debate here
                removes only its graphs and statistics; the messages stay in Debating Chats.
              </p>
              <div className="divide-y divide-zinc-200 border-y border-zinc-200">
                {debates.map((debate) => (
                  <DebateSettingsRow
                    key={debate.id}
                    debate={debate}
                    isRunning={isRunning}
                    onRename={onRenameDebate}
                    onDelete={() => onDeleteDebateRequest(session, debate)}
                  />
                ))}
              </div>
            </div>
          )}
        </Panel>

        <Panel title="Debaters & Teams">
          <div className="grid gap-3 md:grid-cols-2">
            <SelectSetting
              label="Debater amount per team"
              value={String(settings.debaters_per_team)}
              options={["1", "2", "3", "4"]}
              onChange={(value) => onSettingsChange({ debaters_per_team: Number(value) })}
            />
            <ToggleSetting
              label="Judge Assistant, highly recommended"
              value={settings.judge_assistant_enabled}
              onChange={(value) => onSettingsChange({ judge_assistant_enabled: value })}
            />
            <label className="text-sm font-medium text-zinc-900 md:col-span-2">
              Overall model
              <select
                value={selectedModelName}
                onChange={(event) => onModelChange(event.target.value)}
                disabled={unlockedModels.length === 0}
                className="mt-1 h-11 w-full rounded-md border border-zinc-300 bg-white px-3 disabled:cursor-not-allowed disabled:bg-zinc-100"
              >
                {unlockedModels.length === 0 ? <option value="">No unlocked models</option> : null}
                {unlockedModels.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.name}
                  </option>
                ))}
              </select>
              <span className="mt-1 block text-xs font-normal text-zinc-600">
                Used when an individual agent keeps model set to default.
              </span>
            </label>
          </div>

          <div className="mt-4 space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-zinc-950">Shared team roles</h4>
              <p className="text-sm text-zinc-600">
                These settings apply equally to the Pro and Con version of each role.
              </p>
              <div className="mt-2 divide-y divide-zinc-200 border-y border-zinc-200">
                {visibleTeamRoles.map((role) => (
                  <AgentSettingsRow
                    key={role.key}
                    roleKey={role.key}
                    label={role.label}
                    description={role.description}
                    settings={settings}
                    unlockedModels={unlockedModels}
                    selectedModelName={selectedModelName}
                    onChange={updateAgentSetting}
                    showWebSearch={role.key === "evidence_researcher"}
                  />
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-zinc-950">Neutral roles</h4>
              <p className="text-sm text-zinc-600">
                These settings affect only the single neutral agent shown here.
              </p>
              <div className="mt-2 divide-y divide-zinc-200 border-y border-zinc-200">
                {visibleNeutralRoles.map((role) => (
                  <AgentSettingsRow
                    key={role.key}
                    roleKey={role.key}
                    label={role.label}
                    description={role.description}
                    settings={settings}
                    unlockedModels={unlockedModels}
                    selectedModelName={selectedModelName}
                    onChange={updateAgentSetting}
                  />
                ))}
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Council Assistant">
          <p className="mb-3 text-sm text-zinc-600">
            This is the normal chat agent. When Always On is off, the router decides whether the
            Council Assistant or the debaters should respond.
          </p>
          <AgentSettingsRow
            roleKey="council_assistant"
            label="Council Assistant"
            description="Answers normal chat messages and follow-up questions using this chat's memory."
            settings={settings}
            unlockedModels={unlockedModels}
            selectedModelName={selectedModelName}
            onChange={updateAgentSetting}
            showAlwaysOn
          />
        </Panel>

        <Panel title="Prompt & tone">
          <div className="grid gap-3 md:grid-cols-2">
            <SelectSetting
              label="Debate tone"
              value={settings.debate_tone}
              options={["Academic", "Casual", "Formal", "Aggressive"]}
              onChange={(value) => onSettingsChange({ debate_tone: value })}
            />
            <SelectSetting
              label="Language"
              value={settings.language}
              options={["English", "Chinese", "Cantonese"]}
              onChange={(value) => onSettingsChange({ language: value })}
            />
          </div>
        </Panel>

        <Panel title="Output & display">
          <div className="grid gap-3 md:grid-cols-3">
            <ToggleSetting
              label="Auto-scroll"
              value={settings.auto_scroll}
              onChange={(value) => onSettingsChange({ auto_scroll: value })}
            />
            <ToggleSetting
              label="Show timestamps"
              value={settings.show_timestamps}
              onChange={(value) => onSettingsChange({ show_timestamps: value })}
            />
            <ToggleSetting
              label="Show token count"
              value={settings.show_token_count}
              onChange={(value) => onSettingsChange({ show_token_count: value })}
            />
          </div>
        </Panel>

        <Panel title="Advanced">
          <div className="grid gap-3 md:grid-cols-3">
            <NumberSetting
              label="Context window"
              value={settings.context_window}
              min={0}
              max={6}
              onChange={(value) => onSettingsChange({ context_window: value })}
            />
            <NumberSetting
              label="Debate rounds"
              value={settings.debate_rounds}
              min={1}
              max={6}
              onChange={(value) => onSettingsChange({ debate_rounds: value })}
            />
            <SelectSetting
              label="Export format"
              value={settings.export_format}
              options={["Markdown", "PDF", "JSON"]}
              onChange={(value) => onSettingsChange({ export_format: value })}
            />
            <NumberSetting
              label="Auto-save interval"
              value={settings.auto_save_interval}
              min={5}
              max={300}
              onChange={(value) => onSettingsChange({ auto_save_interval: value })}
            />
            <ToggleSetting
              label="Fact-check mode"
              value={settings.fact_check_mode}
              onChange={(value) => onSettingsChange({ fact_check_mode: value })}
            />
          </div>
          <p className="mt-3 text-sm text-zinc-600">
            Fact-check mode is saved as a chat setting and reserved for provider/tool integration.
          </p>
        </Panel>
      </div>
    </section>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-zinc-300 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase text-zinc-500">{title}</h3>
      {children}
    </section>
  );
}

function DebateSettingsRow({
  debate,
  isRunning,
  onRename,
  onDelete
}: {
  debate: DebateRecord;
  isRunning: boolean;
  onRename: (debate: DebateRecord, name: string) => Promise<boolean>;
  onDelete: () => void;
}) {
  const [name, setName] = useState(debate.name);
  const [notice, setNotice] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);

  useEffect(() => {
    setName(debate.name);
    setNotice(null);
  }, [debate.id, debate.name]);

  const handleRename = async () => {
    setNotice(null);
    setIsRenaming(true);
    const saved = await onRename(debate, name);
    setIsRenaming(false);
    if (saved) {
      setNotice("Debate name updated.");
    }
  };

  return (
    <div className="py-3">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
        <div className="min-w-0 flex-1">
          <input
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setNotice(null);
            }}
            className="h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
            aria-label={`Rename ${debate.name}`}
          />
          <p className="mt-1 truncate text-xs text-zinc-600" title={debate.topic}>
            {debate.topic}
          </p>
        </div>
        <button
          type="button"
          onClick={handleRename}
          disabled={isRunning || isRenaming || !name.trim() || name.trim() === debate.name}
          className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-zinc-400"
        >
          {isRenaming ? "Renaming..." : "Rename"}
        </button>
        <button
          type="button"
          onClick={onDelete}
          disabled={isRunning}
          className="rounded-md border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-100 disabled:text-zinc-500"
        >
          Delete Statistics
        </button>
      </div>
      {notice ? <p className="mt-1 text-sm text-emerald-700">{notice}</p> : null}
    </div>
  );
}

function AgentSettingsRow({
  roleKey,
  label,
  description,
  settings,
  unlockedModels,
  selectedModelName,
  onChange,
  showWebSearch = false,
  showAlwaysOn = false
}: {
  roleKey: string;
  label: string;
  description: string;
  settings: SessionSettings;
  unlockedModels: SupportedModel[];
  selectedModelName: string;
  onChange: (
    roleKey: string,
    updates: Partial<SessionSettings["agent_settings"][string]>
  ) => void;
  showWebSearch?: boolean;
  showAlwaysOn?: boolean;
}) {
  const agent = settings.agent_settings[roleKey] ?? {
    model: "",
    temperature: settings.temperature,
    max_tokens: settings.max_tokens,
    response_length: settings.response_length,
    web_search: false,
    always_on: false
  };

  return (
    <div className="py-4">
      <div className="mb-3">
        <p className="font-semibold text-zinc-950">{label}</p>
        <p className="text-sm text-zinc-600">{description}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="text-sm font-medium text-zinc-900">
          Model
          <select
            value={agent.model}
            onChange={(event) => onChange(roleKey, { model: event.target.value })}
            className="mt-1 h-11 w-full rounded-md border border-zinc-300 bg-white px-3"
          >
            <option value="">Use overall model ({selectedModelName || "none"})</option>
            {unlockedModels.map((model) => (
              <option key={model.name} value={model.name}>
                {model.name}
              </option>
            ))}
          </select>
        </label>
        <SelectSetting
          label="Response length"
          value={agent.response_length}
          options={["Concise", "Normal", "Detailed"]}
          onChange={(value) => onChange(roleKey, { response_length: value })}
        />
        <RangeSetting
          label="Temperature"
          value={agent.temperature}
          min={0}
          max={1}
          step={0.05}
          onChange={(value) => onChange(roleKey, { temperature: value })}
        />
        <NumberSetting
          label="Max tokens"
          value={agent.max_tokens}
          min={120}
          max={2000}
          onChange={(value) => onChange(roleKey, { max_tokens: value })}
        />
        {showWebSearch ? (
          <ToggleSetting
            label="Web search for researchers"
            value={agent.web_search}
            onChange={(value) => onChange(roleKey, { web_search: value })}
          />
        ) : null}
        {showAlwaysOn ? (
          <div>
            <ToggleSetting
              label="Always On, off highly recommended"
              value={agent.always_on}
              onChange={(value) => onChange(roleKey, { always_on: value })}
            />
            <p className="mt-1 text-xs text-zinc-600">
              When on, this chat always uses the Council Assistant, even for debate-like messages.
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-300 bg-white p-3">
      <p className="text-xs font-semibold uppercase text-zinc-500">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-zinc-950">{value}</p>
    </div>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  const width = `${Math.max(3, Math.min(100, Math.round(value * 100)))}%`;
  return (
    <div className="mb-2">
      <div className="mb-1 flex justify-between gap-2 text-xs">
        <span className="truncate capitalize text-zinc-700">{label}</span>
        <span className="font-medium text-zinc-900">{toPercent(value)}</span>
      </div>
      <div className="h-2 rounded bg-zinc-100">
        <div className="h-2 rounded bg-emerald-700" style={{ width }} />
      </div>
    </div>
  );
}

function PieChart({ values }: { values: Record<string, number> }) {
  const support = Math.round((values.support ?? 0) * 100);
  const oppose = Math.round((values.oppose ?? 0) * 100);
  const mixed = Math.max(0, 100 - support - oppose);
  const background = `conic-gradient(#047857 0 ${support}%, #dc2626 ${support}% ${
    support + oppose
  }%, #0891b2 ${support + oppose}% 100%)`;
  return (
    <div className="flex items-center gap-4">
      <div className="h-36 w-36 rounded-full border border-zinc-300" style={{ background }} />
      <div className="space-y-2 text-sm">
        <Legend color="bg-emerald-700" label="Support" value={support} />
        <Legend color="bg-red-600" label="Oppose" value={oppose} />
        <Legend color="bg-cyan-700" label="Mixed" value={mixed} />
      </div>
    </div>
  );
}

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`h-3 w-3 rounded ${color}`} />
      <span className="text-zinc-700">
        {label}: {value}%
      </span>
    </div>
  );
}

function LineChart({ history }: { history: DebateAnalytics[] }) {
  const labels = ["support", "oppose", "mixed"] as const;
  const colors = { support: "#047857", oppose: "#dc2626", mixed: "#0891b2" };
  const width = 620;
  const height = 220;
  const pad = 28;

  const pathFor = (label: (typeof labels)[number]) =>
    history
      .map((item, index) => {
        const x = pad + (index / Math.max(1, history.length - 1)) * (width - pad * 2);
        const y = height - pad - (item.bayesian.probabilities[label] ?? 0) * (height - pad * 2);
        return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-60 min-w-[520px]">
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#d4d4d8" />
        <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="#d4d4d8" />
        {[0.25, 0.5, 0.75].map((tick) => (
          <line
            key={tick}
            x1={pad}
            y1={height - pad - tick * (height - pad * 2)}
            x2={width - pad}
            y2={height - pad - tick * (height - pad * 2)}
            stroke="#f4f4f5"
          />
        ))}
        {labels.map((label) => (
          <path key={label} d={pathFor(label)} fill="none" stroke={colors[label]} strokeWidth={3} />
        ))}
      </svg>
      <div className="flex gap-4 text-xs">
        <Legend color="bg-emerald-700" label="Support" value={0} />
        <Legend color="bg-red-600" label="Oppose" value={0} />
        <Legend color="bg-cyan-700" label="Mixed" value={0} />
      </div>
    </div>
  );
}

function SelectSetting({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-sm font-medium text-zinc-900">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 h-11 w-full rounded-md border border-zinc-300 bg-white px-3"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function NumberSetting({
  label,
  value,
  min,
  max,
  onChange
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="text-sm font-medium text-zinc-900">
      {label}
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 h-11 w-full rounded-md border border-zinc-300 px-3"
      />
    </label>
  );
}

function RangeSetting({
  label,
  value,
  min,
  max,
  step,
  onChange
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="text-sm font-medium text-zinc-900">
      {label}: {value.toFixed(2)}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-3 w-full"
      />
    </label>
  );
}

function ToggleSetting({
  label,
  value,
  onChange
}: {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-md border border-zinc-300 px-3 py-3 text-sm font-medium text-zinc-900">
      {label}
      <input
        type="checkbox"
        checked={value}
        onChange={(event) => onChange(event.target.checked)}
        className="h-5 w-5"
      />
    </label>
  );
}

function MarkdownText({ text }: { text: string }) {
  const lines = text.split(/\n+/);
  const elements: ReactNode[] = [];
  let listItems: ReactNode[] = [];
  let ordered = false;

  const flushList = () => {
    if (listItems.length === 0) {
      return;
    }
    const ListTag = ordered ? "ol" : "ul";
    elements.push(
      <ListTag key={`list-${elements.length}`} className={`mt-3 ${ordered ? "list-decimal" : "list-disc"} pl-6 text-sm leading-6 text-zinc-800`}>
        {listItems}
      </ListTag>
    );
    listItems = [];
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }
    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushList();
      const size = heading[1].length === 1 ? "text-lg" : "text-base";
      elements.push(
        <h4 key={index} className={`mt-4 font-semibold text-zinc-950 ${size}`}>
          {renderInline(heading[2])}
        </h4>
      );
      return;
    }
    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    const numbered = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (bullet || numbered) {
      if (listItems.length > 0 && ordered !== Boolean(numbered)) {
        flushList();
      }
      ordered = Boolean(numbered);
      listItems.push(<li key={index}>{renderInline((bullet ?? numbered)?.[1] ?? trimmed)}</li>);
      return;
    }
    flushList();
    elements.push(
      <p key={index} className="mt-3 whitespace-pre-wrap text-sm leading-6 text-zinc-800">
        {renderInline(trimmed)}
      </p>
    );
  });
  flushList();

  return <div className="mt-3">{elements}</div>;
}

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function estimateTokens(text: string) {
  return Math.ceil(text.trim().split(/\s+/).filter(Boolean).length * 1.3);
}

function maxVote(analytics: DebateAnalytics) {
  return Math.max(0.001, ...Object.values(analytics.ensemble.weighted_votes));
}

function toPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
