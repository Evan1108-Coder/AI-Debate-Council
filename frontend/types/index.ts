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
  sequence: number;
  created_at: string;
};

export type SessionSettings = {
  overall_model: string;
  debaters_per_team: number;
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
  context_window: number;
  debate_rounds: number;
  researcher_web_search: boolean;
  fact_check_mode: boolean;
  export_format: string;
  auto_save_interval: number;
  updated_at?: string;
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
};

export type DebateEvent =
  | {
      type: "debate_started";
      debate: DebateRecord;
      topic: string;
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
    }
  | {
      type: "interaction_completed";
      mode: "chat";
      debate_id: string;
    }
  | {
      type: "error";
      message: unknown;
    };
