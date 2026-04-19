export type ChatSession = {
  id: string;
  name: string;
  default_index: number;
  created_at: string;
  updated_at: string;
};

export type DebateMessage = {
  id: string;
  session_id: string;
  debate_id: string;
  role: string;
  speaker: string;
  model: string;
  content: string;
  cost_summary: CostSummary | null;
  debate_cost_summary: CostSummary | null;
  phase_key: string | null;
  phase_title: string | null;
  phase_index: number | null;
  phase_total: number | null;
  phase_kind: string | null;
  sequence: number;
  created_at: string;
};

export type CouncilSettings = {
  universal_experience: boolean;
  use_agent_identity_profiles: boolean;
  debate_intelligence_depth: "Light" | "Normal" | "Deep";
  use_value_consequence_system: boolean;
  default_judge_mode: "Debate Performance" | "Truth-Seeking" | "Hybrid";
};

export type DebateIntelligenceRecord = {
  id: string;
  session_id: string;
  debate_id: string;
  record_type: string;
  team: string;
  role: string;
  agent_id: string;
  title: string;
  content: string;
  status: string;
  confidence: number;
  payload: Record<string, unknown>;
  basis: unknown[];
  created_at: string;
  updated_at: string;
};

export type AgentExperienceRecord = {
  id: string;
  scope: string;
  session_id: string | null;
  agent_id: string;
  lesson_type: string;
  lesson: string;
  confidence: string;
  basis: unknown[];
  created_at: string;
  last_used_at: string | null;
  use_count: number;
};

export type DebateIntelligence = {
  debate: DebateRecord | null;
  records: DebateIntelligenceRecord[];
  claims: DebateIntelligenceRecord[];
  challenges: DebateIntelligenceRecord[];
  evidence: DebateIntelligenceRecord[];
  scorecards: DebateIntelligenceRecord[];
  values: DebateIntelligenceRecord[];
  memories: DebateIntelligenceRecord[];
  reviews: DebateIntelligenceRecord[];
  team_rooms: { pro: DebateIntelligenceRecord[]; con: DebateIntelligenceRecord[] };
  experiences: AgentExperienceRecord[];
  feedback_questions: Array<{ key: string; question: string; options: string[] }>;
};

export type SessionSettings = {
  overall_model: string;
  debaters_per_team: number;
  discussion_messages_per_team: number;
  judge_assistant_enabled: boolean;
  agent_settings: Record<
    string,
    {
      model: string;
      temperature: number;
      max_tokens: number;
      response_length: string;
      web_search: boolean;
      always_on: boolean;
    }
  >;
  role_models: Record<string, string>;
  temperature: number;
  max_tokens: number;
  debate_tone: string;
  language: string;
  response_length: string;
  auto_scroll: boolean;
  show_timestamps: boolean;
  show_token_count: boolean;
  show_money_cost: boolean;
  cost_currency: string;
  show_model_costs: boolean;
  show_every_message_cost_in_debate: boolean;
  context_window: number;
  debate_rounds: number;
  researcher_web_search: boolean;
  fact_check_mode: boolean;
  export_format: string;
  auto_save_interval: number;
  use_experience: boolean;
  judge_mode: string;
  evidence_strictness: string;
  updated_at?: string;
};

export type CostSummary = {
  currency: string;
  total: number;
  total_usd: number;
  input_tokens: number;
  output_tokens: number;
  calls: number;
  estimated: boolean;
  rate_source: string;
  models: Array<{
    model: string;
    input_tokens: number;
    output_tokens: number;
    calls: number;
    cost: number;
    cost_usd: number;
    input_usd_per_1m: number;
    output_usd_per_1m: number;
  }>;
};

export type SupportedModel = {
  name: string;
  provider: string;
  provider_label: string;
  api_key_env: string;
  litellm_model: string;
  configured: boolean;
};

export type ProviderSummary = {
  provider: string;
  provider_label: string;
  api_key_env: string;
  configured: boolean;
  unlocked_model_count: number;
  total_model_count: number;
  models: SupportedModel[];
};

export type ModelsResponse = {
  models: SupportedModel[];
  providers: ProviderSummary[];
  available_model_count: number;
  real_available_model_count: number;
  minimum_debate_models: number;
  selection_required: boolean;
  mock_mode: boolean;
};

export type DebateAssignment = {
  role: string;
  speaker: string;
  model: string;
  provider: string;
};

export type DebateRecord = {
  id: string;
  session_id: string;
  name: string;
  default_index: number;
  mode: string;
  topic: string;
  status: string;
  judge_summary: string | null;
  error: string | null;
  started_at: string;
  finished_at: string | null;
};

export type DebateAnalytics = {
  turn_count: number;
  round: number;
  method_notes: string[];
  ensemble: {
    majority_vote: string;
    weighted_vote: string;
    votes: Record<string, number>;
    weighted_votes: Record<string, number>;
  };
  bayesian: {
    leader: string;
    probabilities: Record<string, number>;
  };
  argument_mining: {
    claims: Array<{
      speaker: string;
      stance: string;
      confidence: number;
      text: string;
    }>;
    evidence_count: number;
    rebuttal_count: number;
    redundancy_count: number;
  };
  stance: {
    by_role: Record<string, string>;
  };
  confidence: {
    average: number;
    by_role: Record<string, number>;
  };
  credibility: {
    elo_by_role: Record<string, number>;
    normalized_by_role: Record<string, number>;
  };
  game_theory: {
    auction_winner: string | null;
    auction_stance: string;
    winning_bid: number;
    nash_pressure: number;
  };
  argument_graph: {
    node_count: number;
    edge_count: number;
    support_edges: number;
    attack_edges: number;
    strongest_claims: Array<{
      speaker: string;
      stance: string;
      strength: number;
      text: string;
    }>;
  };
  attention: {
    top_terms: string[];
  };
  delphi: {
    convergence: number;
    rounds_analyzed: number;
    last_round_distribution: Record<string, number>;
  };
  mixture_of_experts: {
    role_weights: Record<string, number>;
    lead_expert: string | null;
  };
  source?: {
    mode: "latest_debate" | "selected_debate";
    debate_id: string;
    name: string;
    default_index: number;
    topic: string;
    debate_count: number;
  };
  phase?: {
    current: {
      key: string;
      title: string;
      kind: string;
      index: number;
      total: number;
      speaker: string;
      team: string;
    } | null;
    completed: number;
    total: number;
    flow_name: string;
    sequence: Array<{
      key: string;
      title: string;
      kind: string;
      index: number;
      total: number;
      speaker: string;
      team: string;
    }>;
    pro_position: string;
    con_position: string;
  };
  session_charts?: {
    win_rate_by_team: {
      pro: number;
      con: number;
      unclear: number;
      resolved: number;
      total_completed: number;
      pro_rate: number;
      con_rate: number;
    };
    cost_by_phase: Record<string, number>;
    debate_durations: Array<{
      debate_id: string;
      name: string;
      status: string;
      duration_seconds: number;
    }>;
    messages_by_role: Record<string, number>;
    citations: Array<{
      speaker: string;
      url: string;
      domain: string;
      debate_id: string;
      debate_name: string;
      phase_title: string;
    }>;
  };
};

export type DebateEvent =
  | {
      type: "debate_started";
      debate: DebateRecord;
      topic: string;
      positions?: { pro: string; con: string };
      selected_model: SupportedModel;
      assignments: DebateAssignment[];
      judge: { speaker: string; model: string; provider: string };
      active_debates: number;
    }
  | {
      type: "interaction_started";
      mode: "chat";
      debate: { id: string; topic: string };
      selected_model: SupportedModel;
    }
  | {
      type: "team_preparation_started" | "team_preparation_completed";
      debate_id: string;
      message: string;
    }
  | {
      type: "message_started";
      stream_id: string;
      message: DebateMessage;
      round: number | "summary";
    }
  | {
      type: "message_delta";
      stream_id: string;
      delta: string;
    }
  | {
      type: "message_replaced";
      stream_id: string;
      content: string;
    }
  | {
      type: "message_completed";
      stream_id: string;
      message: DebateMessage;
    }
  | {
      type: "analysis_updated";
      round: number;
      analysis: DebateAnalytics;
    }
  | {
      type: "debate_completed";
      debate_id: string;
      judge_summary: string;
      active_debates: number;
      cost_summary?: CostSummary;
    }
  | {
      type: "interaction_completed";
      mode: "chat";
      debate_id: string;
      cost_summary?: CostSummary;
    }
  | {
      type: "error";
      message: unknown;
    };
