"use client";

import { useMemo, useState, type ReactNode } from "react";

import type {
  AgentExperienceOverview,
  ChatSession,
  ModelsResponse,
  UserDebateProfileOverview
} from "@/types";

type GlobalWorkspaceProps = {
  view: "welcome" | "aiExperiences" | "userProfile";
  sessions: ChatSession[];
  models: ModelsResponse | null;
  experiences: AgentExperienceOverview | null;
  profileOverview: UserDebateProfileOverview | null;
  onCreateSession: (mode?: ChatSession["mode"]) => void;
};

export function GlobalWorkspace({
  view,
  sessions,
  models,
  experiences,
  profileOverview,
  onCreateSession
}: GlobalWorkspaceProps) {
  if (view === "aiExperiences") {
    return <AiDebaterExperiencesPage sessions={sessions} overview={experiences} />;
  }
  if (view === "userProfile") {
    return <UserDebateProfilePage overview={profileOverview} onCreateSession={onCreateSession} />;
  }
  return <WelcomePage models={models} onCreateSession={onCreateSession} />;
}

function WelcomePage({
  models,
  onCreateSession
}: {
  models: ModelsResponse | null;
  onCreateSession: (mode?: ChatSession["mode"]) => void;
}) {
  const providers = models?.providers ?? [];
  const available = models?.available_model_count ?? 0;
  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-[#f5f7f6]">
      <section className="electron-drag border-b border-zinc-300 bg-white p-6">
        <p className="text-sm font-medium text-emerald-700">AI Debate Coach & Council</p>
        <h1 className="mt-1 text-3xl font-semibold text-zinc-950">
          Train your arguments or watch a full council debate.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-zinc-600">
          The app is now organized around two jobs: helping you improve at debate, and letting
          you inspect how a structured AI council reasons through the same question. Start with
          training if you want the most value fast.
        </p>
      </section>

      <section className="min-h-0 flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr]">
            <Panel title="Start with the flagship mode">
              <div className="grid gap-3 md:grid-cols-2">
                <ChoiceCard
                  eyebrow="Recommended"
                  title="AI vs Human Debate Training"
                  description="Debate one Practice Debater, then get a Judge verdict and a coach-style Debate Trainer report."
                  bullets={[
                    "Best for improving rebuttal, clarity, and closing strength",
                    "Builds your global User Debate Profile across chats",
                    "Lets the trainer recommend what to practice next"
                  ]}
                  cta="Start Training Chat"
                  onClick={() => onCreateSession("ai_vs_human")}
                />
                <ChoiceCard
                  eyebrow="Council lab"
                  title="AI vs AI Debate"
                  description="Watch Pro and Con teams argue in specialist roles, then inspect claims, challenges, evidence, and verdict logic."
                  bullets={[
                    "Best for comparing ideas and pressure-testing both sides",
                    "Feeds the global AI Debater Experiences page",
                    "Great for observing strategy before practicing yourself"
                  ]}
                  cta="Start Council Chat"
                  onClick={() => onCreateSession("ai_vs_ai")}
                />
              </div>
            </Panel>

            <Panel title="First 60 seconds">
              <div className="grid gap-3 md:grid-cols-2">
                <MetricCard label="Verified Models" value={String(available)} />
                <MetricCard label="Providers Ready" value={String(providers.filter((item) => item.configured).length)} />
              </div>
              <ol className="mt-4 space-y-3 text-sm leading-6 text-zinc-700">
                <li>1. Create a chat in the mode you want.</li>
                <li>2. Pick one verified model from the Overall Model menu.</li>
                <li>3. Start with a clear topic like “Should schools ban phones in class?”</li>
                <li>4. Use Debate Intelligence and the global profile pages after the debate to see what actually improved.</li>
              </ol>
            </Panel>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
            <Panel title="Why this app feels different now">
              <div className="grid gap-3 md:grid-cols-2">
                <Callout
                  title="Training loop"
                  body="Practice debates feed a real user profile, so later coaching can react to your past strengths, weaknesses, side balance, and trainer notes."
                />
                <Callout
                  title="Visible memory"
                  body="AI Debater Experiences and Debate Intelligence make the system's long-term memory inspectable instead of hiding it behind vague prompts."
                />
                <Callout
                  title="Judge with structure"
                  body="Claims, challenges, evidence, scorecards, and verdict review all give the Judge more than pure vibes to work with."
                />
                <Callout
                  title="Shareable output"
                  body="Each chat already supports Markdown, JSON, and printable PDF exports, so debates can become reports instead of disappearing into a transcript."
                />
              </div>
            </Panel>

            <Panel title="Provider readiness">
              <div className="space-y-2">
                {providers.length === 0 ? (
                  <p className="text-sm text-zinc-600">
                    No providers are configured yet. Add one API key in `.env`, restart the backend,
                    and the model menu will populate automatically.
                  </p>
                ) : (
                  providers.map((provider) => (
                    <div
                      key={provider.provider}
                      className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-zinc-900">
                          {provider.provider_label}
                        </span>
                        <span
                          className={`rounded px-2 py-1 text-xs font-semibold ${
                            provider.configured
                              ? "bg-emerald-100 text-emerald-800"
                              : provider.status_label === "Unavailable"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-zinc-200 text-zinc-700"
                          }`}
                        >
                          {provider.status_label}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-5 text-zinc-600">
                        {provider.status_reason || `${provider.unlocked_model_count} verified model(s) ready.`}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>
        </div>
      </section>
    </main>
  );
}

function AiDebaterExperiencesPage({
  sessions,
  overview
}: {
  sessions: ChatSession[];
  overview: AgentExperienceOverview | null;
}) {
  const [copied, setCopied] = useState(false);
  const sessionNames = useMemo(
    () => Object.fromEntries(sessions.map((session) => [session.id, session.name])),
    [sessions]
  );
  const copySummary = async () => {
    if (!overview) {
      return;
    }
    const topAgents = overview.by_agent
      .slice(0, 5)
      .map((item) => `${formatAgentLabel(item.agent_id)} (${item.record_count})`)
      .join(", ");
    const text = [
      "AI Debater Experiences",
      `Experience records: ${overview.summary.total_records}`,
      `Distinct agents: ${overview.summary.distinct_agents}`,
      `Universal records: ${overview.summary.universal_records}`,
      `Chat records: ${overview.summary.chat_records}`,
      `Top identities: ${topAgents || "None yet"}`
    ].join("\n");
    await safeCopy(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-[#f5f7f6]">
      <section className="electron-drag border-b border-zinc-300 bg-white p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-emerald-700">Global memory layer</p>
            <h1 className="mt-1 text-3xl font-semibold text-zinc-950">AI Debater Experiences</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-zinc-600">
              This page shows what the council has actually stored about its roles over time.
              These are factual, user-visible records built from claims, challenges, evidence,
              scorecards, and feedback, not invented personalities.
            </p>
          </div>
          <button
            type="button"
            onClick={() => copySummary().catch(() => undefined)}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-semibold text-zinc-800 hover:bg-zinc-100"
          >
            {copied ? "Copied" : "Copy Overview"}
          </button>
        </div>
      </section>

      <section className="min-h-0 flex-1 overflow-y-auto p-6">
        {!overview ? (
          <LoadingPanel message="Loading AI debater experiences..." />
        ) : (
          <div className="mx-auto max-w-6xl space-y-4">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Experience Records" value={String(overview.summary.total_records)} />
              <MetricCard label="Tracked Identities" value={String(overview.summary.distinct_agents)} />
              <MetricCard
                label="Universal / Chat"
                value={`${overview.summary.universal_records} / ${overview.summary.chat_records}`}
              />
              <MetricCard label="Total Reuses" value={String(overview.summary.total_uses)} />
            </div>

            <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
              <Panel title="What the council is currently carrying forward">
                <p className="mb-3 text-sm leading-6 text-zinc-600">
                  The top rows below are the strongest active identity records by use count, confidence,
                  and recency. This is the memory that most visibly shapes future turns.
                </p>
                <div className="space-y-3">
                  {overview.experiences.length === 0 ? (
                    <p className="text-sm text-zinc-600">
                      No experience records exist yet. Finish a full council debate or practice debate first.
                    </p>
                  ) : (
                    overview.experiences.slice(0, 8).map((experience) => (
                      <div key={experience.id} className="rounded-md border border-zinc-200 bg-zinc-50 p-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold text-zinc-950">
                            {formatAgentLabel(experience.agent_id)}
                          </span>
                          <Tag>{experience.scope === "chat" ? "Chat-scoped" : "Universal"}</Tag>
                          <Tag>{formatAgentLabel(experience.lesson_type)}</Tag>
                          <Tag>{experience.confidence}</Tag>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-zinc-700">{experience.lesson}</p>
                        <p className="mt-2 text-xs text-zinc-500">
                          Uses: {experience.use_count} · Session:{" "}
                          {experience.session_id ? sessionNames[experience.session_id] || "Unknown Session" : "All chats"}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </Panel>

              <Panel title="Memory guardrails">
                <div className="space-y-3 text-sm leading-6 text-zinc-700">
                  <Callout
                    title="No fake personality"
                    body="Identity stays empty until the system has real recorded activity. The app avoids inventing strengths, weaknesses, or values out of thin air."
                  />
                  <Callout
                    title="Visible source trail"
                    body="Experience is backed by saved debate objects such as claims, challenges, evidence, judge scorecards, and user feedback."
                  />
                  <Callout
                    title="Global by default"
                    body="Universal experience lets roles learn across chats, while chat-scoped lessons still stay local when a session needs its own behavior."
                  />
                </div>
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Identity load by agent">
                <div className="space-y-3">
                  {overview.by_agent.length === 0 ? (
                    <p className="text-sm text-zinc-600">No agent identities have been recorded yet.</p>
                  ) : (
                    overview.by_agent.map((item) => (
                      <div key={item.agent_id} className="rounded-md border border-zinc-200 bg-zinc-50 p-3">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-zinc-950">
                              {formatAgentLabel(item.agent_id)}
                            </p>
                            <p className="text-xs text-zinc-500">
                              {item.record_count} record(s) · {item.high_confidence_count} high confidence
                            </p>
                          </div>
                          <span className="text-sm font-semibold text-zinc-800">
                            {item.use_count} reuse(s)
                          </span>
                        </div>
                        <div className="mt-3">
                          <Bar value={item.record_count} max={Math.max(1, overview.by_agent[0]?.record_count || 1)} />
                        </div>
                        <p className="mt-2 text-xs text-zinc-500">
                          Most common lesson types: {Object.keys(item.lesson_types).slice(0, 3).map(formatAgentLabel).join(", ") || "None"}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </Panel>

              <Panel title="Lesson types in memory">
                <div className="space-y-3">
                  {Object.keys(overview.by_lesson_type).length === 0 ? (
                    <p className="text-sm text-zinc-600">No lesson types have been captured yet.</p>
                  ) : (
                    Object.entries(overview.by_lesson_type)
                      .sort((left, right) => right[1] - left[1])
                      .map(([type, count]) => (
                        <div key={type}>
                          <div className="mb-1 flex items-center justify-between gap-2 text-sm">
                            <span className="font-medium text-zinc-900">{formatAgentLabel(type)}</span>
                            <span className="text-zinc-600">{count}</span>
                          </div>
                          <Bar value={count} max={Math.max(...Object.values(overview.by_lesson_type), 1)} />
                        </div>
                      ))
                  )}
                </div>
              </Panel>
            </div>

            <Panel title="Recent memory and review saves">
              <div className="space-y-3">
                {overview.memory_events.length === 0 ? (
                  <p className="text-sm text-zinc-600">
                    No memory-save, review, or scorecard records have been created yet.
                  </p>
                ) : (
                  overview.memory_events.map((record) => (
                    <div key={record.id} className="rounded-md border border-zinc-200 bg-white p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-zinc-950">{record.title}</span>
                        <Tag>{formatAgentLabel(record.record_type)}</Tag>
                        {record.role ? <Tag>{formatAgentLabel(record.role)}</Tag> : null}
                        {record.team ? <Tag>{record.team.toUpperCase()}</Tag> : null}
                      </div>
                      <p className="mt-2 text-sm leading-6 text-zinc-700">{record.content}</p>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>
        )}
      </section>
    </main>
  );
}

function UserDebateProfilePage({
  overview,
  onCreateSession
}: {
  overview: UserDebateProfileOverview | null;
  onCreateSession: (mode?: ChatSession["mode"]) => void;
}) {
  const [copied, setCopied] = useState(false);
  const copySummary = async () => {
    if (!overview) {
      return;
    }
    const profile = overview.profile;
    const text = [
      "User Debate Profile",
      `Practice debates completed: ${profile.practice_debates_completed}`,
      `Strengths: ${profile.strengths.join("; ") || "None yet"}`,
      `Improvement targets: ${profile.weaknesses.join("; ") || "None yet"}`,
      `Coach summary: ${overview.coach_summary}`
    ].join("\n");
    await safeCopy(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-[#f5f7f6]">
      <section className="electron-drag border-b border-zinc-300 bg-white p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-emerald-700">Global coaching layer</p>
            <h1 className="mt-1 text-3xl font-semibold text-zinc-950">User Debate Profile</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-zinc-600">
              This is the long-term training dashboard. It tracks how your practice debates have
              been judged, what the trainer keeps noticing, and what the system thinks you should
              work on next.
            </p>
          </div>
          <button
            type="button"
            onClick={() => copySummary().catch(() => undefined)}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-semibold text-zinc-800 hover:bg-zinc-100"
          >
            {copied ? "Copied" : "Copy Training Snapshot"}
          </button>
        </div>
      </section>

      <section className="min-h-0 flex-1 overflow-y-auto p-6">
        {!overview ? (
          <LoadingPanel message="Loading user debate profile..." />
        ) : (
          <div className="mx-auto max-w-6xl space-y-4">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Practice Debates"
                value={String(overview.profile.practice_debates_completed)}
              />
              <MetricCard
                label="Decided Verdicts"
                value={String((overview.profile.wins.pro || 0) + (overview.profile.wins.con || 0))}
              />
              <MetricCard
                label="Less Practiced Side"
                value={overview.less_practiced_side.toUpperCase()}
              />
              <MetricCard
                label="Last Updated"
                value={formatShortDate(overview.profile.last_updated_at)}
              />
            </div>

            <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
              <Panel title="Coach summary">
                <p className="text-sm leading-7 text-zinc-700">{overview.coach_summary}</p>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-950">Recommended next drills</h3>
                    <ul className="mt-2 space-y-2 text-sm leading-6 text-zinc-700">
                      {overview.recommendations.map((item, index) => (
                        <li key={`${item}-${index}`} className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-950">Best next session setup</h3>
                    <div className="mt-2 rounded-md border border-zinc-200 bg-zinc-50 p-3 text-sm leading-6 text-zinc-700">
                      <p>Mode: AI vs Human Debate Training</p>
                      <p>Human side: {overview.less_practiced_side.toUpperCase()}</p>
                      <p>
                        Flow:{" "}
                        {overview.profile.practice_debates_completed < 3 ? "Free for fluency" : "Structured for deliberate reps"}
                      </p>
                      <p>
                        Focus:{" "}
                        {overview.profile.weaknesses.length > 0 ? "Target your latest weakness" : "Full Debate"}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => onCreateSession("ai_vs_human")}
                      className="mt-3 rounded-md bg-zinc-950 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800"
                    >
                      Start Training Chat
                    </button>
                  </div>
                </div>
              </Panel>

              <Panel title="Performance snapshot">
                <div className="space-y-4">
                  <SnapshotRow
                    label="Won as Pro"
                    value={overview.profile.wins.pro || 0}
                    max={Math.max(1, overview.profile.practice_debates_completed)}
                  />
                  <SnapshotRow
                    label="Won as Con"
                    value={overview.profile.wins.con || 0}
                    max={Math.max(1, overview.profile.practice_debates_completed)}
                  />
                  <SnapshotRow
                    label="Unclear outcomes"
                    value={overview.profile.wins.unclear || 0}
                    max={Math.max(1, overview.profile.practice_debates_completed)}
                  />
                  <SnapshotRow
                    label="Auto side usage"
                    value={overview.profile.side_history.auto || 0}
                    max={Math.max(1, overview.profile.practice_debates_completed)}
                  />
                </div>
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Strengths">
                <BulletList
                  items={overview.profile.strengths}
                  emptyText="No confirmed strengths have been recorded yet. Finish a few practice debates first."
                />
              </Panel>
              <Panel title="Improvement targets">
                <BulletList
                  items={overview.profile.weaknesses}
                  emptyText="No recurring weaknesses have been recorded yet."
                />
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Style tags">
                {overview.profile.style_tags.length === 0 ? (
                  <p className="text-sm text-zinc-600">No style tags recorded yet.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {overview.profile.style_tags.map((tag) => (
                      <Tag key={tag}>{tag}</Tag>
                    ))}
                  </div>
                )}
              </Panel>
              <Panel title="Trainer notes">
                <BulletList
                  items={overview.profile.trainer_notes}
                  emptyText="No trainer notes have been saved yet."
                />
              </Panel>
            </div>

            <Panel title="Recent practice history">
              {overview.recent_practice_debates.length === 0 ? (
                <p className="text-sm text-zinc-600">
                  No completed practice debates yet. Start one training chat and finish the debate to populate this history.
                </p>
              ) : (
                <div className="space-y-3">
                  {overview.recent_practice_debates.map((debate) => (
                    <div key={debate.id} className="rounded-md border border-zinc-200 bg-white p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-zinc-950">{debate.name}</span>
                        <Tag>{debate.session_name}</Tag>
                        <Tag>{debate.winner.toUpperCase()}</Tag>
                        <Tag>{debate.human_side.toUpperCase()}</Tag>
                        <Tag>{debate.practice_flow}</Tag>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-zinc-700">{debate.topic}</p>
                      <p className="mt-2 text-xs text-zinc-500">
                        Finished {formatShortDate(debate.finished_at || debate.started_at)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>
        )}
      </section>
    </main>
  );
}

function LoadingPanel({ message }: { message: string }) {
  return (
    <section className="flex h-full min-w-0 flex-1 items-center justify-center p-6">
      <p className="text-sm text-zinc-600">{message}</p>
    </section>
  );
}

function ChoiceCard({
  eyebrow,
  title,
  description,
  bullets,
  cta,
  onClick
}: {
  eyebrow: string;
  title: string;
  description: string;
  bullets: string[];
  cta: string;
  onClick: () => void;
}) {
  return (
    <div className="rounded-md border border-zinc-300 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">{eyebrow}</p>
      <h3 className="mt-2 text-lg font-semibold text-zinc-950">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-zinc-600">{description}</p>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-700">
        {bullets.map((bullet) => (
          <li key={bullet}>• {bullet}</li>
        ))}
      </ul>
      <button
        type="button"
        onClick={onClick}
        className="mt-4 rounded-md bg-zinc-950 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800"
      >
        {cta}
      </button>
    </div>
  );
}

function Callout({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50 p-3">
      <p className="text-sm font-semibold text-zinc-950">{title}</p>
      <p className="mt-1 text-sm leading-6 text-zinc-700">{body}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-zinc-300 bg-white p-4">
      <h2 className="text-lg font-semibold text-zinc-950">{title}</h2>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-300 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-zinc-950">{value}</p>
    </div>
  );
}

function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="rounded bg-zinc-100 px-2 py-1 text-xs font-semibold text-zinc-700">
      {children}
    </span>
  );
}

function Bar({ value, max }: { value: number; max: number }) {
  const width =
    value <= 0
      ? "0%"
      : `${Math.max(4, Math.round((Math.max(0, value) / Math.max(1, max)) * 100))}%`;
  return (
    <div className="h-2 rounded-full bg-zinc-200">
      <div className="h-2 rounded-full bg-emerald-700" style={{ width }} />
    </div>
  );
}

function SnapshotRow({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2 text-sm">
        <span className="font-medium text-zinc-900">{label}</span>
        <span className="text-zinc-600">{value}</span>
      </div>
      <Bar value={value} max={max} />
    </div>
  );
}

function BulletList({ items, emptyText }: { items: string[]; emptyText: string }) {
  if (items.length === 0) {
    return <p className="text-sm text-zinc-600">{emptyText}</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm leading-6 text-zinc-700">
          {item}
        </li>
      ))}
    </ul>
  );
}

function formatAgentLabel(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatShortDate(value: string) {
  if (!value) {
    return "Not yet";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

async function safeCopy(text: string) {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
  } catch { /* clipboard API can throw in insecure contexts */ }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}
