from __future__ import annotations

from collections import Counter, defaultdict
from math import exp, log
import re
from typing import Any


STANCE_LABELS = ("support", "oppose", "mixed")
ROLE_STANCE_BIAS = {
    "advocate": "support",
    "critic": "oppose",
    "researcher": "mixed",
    "devils_advocate": "oppose",
    "lead_advocate": "support",
    "rebuttal_critic": "oppose",
    "evidence_researcher": "mixed",
    "cross_examiner": "oppose",
}
SUPPORT_TERMS = {
    "benefit",
    "effective",
    "improve",
    "advantage",
    "support",
    "strong",
    "positive",
    "worth",
    "works",
    "should",
    "valuable",
    "promising",
}
OPPOSE_TERMS = {
    "risk",
    "flaw",
    "harm",
    "problem",
    "cost",
    "oppose",
    "against",
    "weak",
    "fail",
    "negative",
    "concern",
    "tradeoff",
    "however",
    "unless",
}
MIXED_TERMS = {
    "depends",
    "unclear",
    "mixed",
    "condition",
    "evidence",
    "research",
    "uncertain",
    "context",
    "data",
    "measure",
}
EVIDENCE_MARKERS = {
    "because",
    "evidence",
    "data",
    "study",
    "studies",
    "example",
    "research",
    "observed",
    "measured",
    "survey",
}
REBUTTAL_MARKERS = {
    "but",
    "however",
    "although",
    "flaw",
    "counter",
    "rebut",
    "risk",
    "unless",
    "yet",
}
HEDGE_TERMS = {"maybe", "might", "could", "unclear", "uncertain", "possibly", "depends"}
ASSERTIVE_TERMS = {"clear", "strong", "likely", "therefore", "because", "evidence"}
STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "and",
    "are",
    "because",
    "been",
    "being",
    "but",
    "can",
    "could",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "its",
    "more",
    "not",
    "one",
    "only",
    "our",
    "out",
    "should",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "through",
    "topic",
    "under",
    "use",
    "was",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
}


def analyze_debate(topic: str, transcript: list[dict[str, Any]]) -> dict[str, Any]:
    turns = [_analyze_turn(topic, turn, transcript[:index]) for index, turn in enumerate(transcript)]
    if not turns:
        return _empty_analysis()

    weighted_votes = {label: 0.0 for label in STANCE_LABELS}
    raw_votes = {label: 0 for label in STANCE_LABELS}
    confidence_by_role: dict[str, float] = {}
    credibility_by_role: dict[str, float] = {}
    elo_by_role: dict[str, int] = {}
    stance_by_role: dict[str, str] = {}

    role_gate = _mixture_of_experts(topic, turns)
    for turn in turns:
        label = turn["stance"]
        role = turn["role"]
        raw_votes[label] += 1
        weight = (
            turn["confidence"]
            * turn["novelty"]
            * turn["credibility"]
            * role_gate["raw_role_weights"].get(role, 1.0)
        )
        weighted_votes[label] += weight
        confidence_by_role[turn["speaker"]] = round(turn["confidence"], 3)
        credibility_by_role[turn["speaker"]] = round(turn["credibility"], 3)
        elo_by_role[turn["speaker"]] = turn["elo"]
        stance_by_role[turn["speaker"]] = label

    bayesian = _bayesian_aggregation(turns, role_gate["raw_role_weights"])
    graph = _argument_graph(turns)
    attention = _attention_terms(topic, transcript)
    delphi = _delphi_convergence(turns)
    majority_vote = max(raw_votes, key=raw_votes.get)
    weighted_vote = max(weighted_votes, key=weighted_votes.get)
    auction_winner = max(turns, key=lambda turn: turn["bid"])

    return {
        "turn_count": len(turns),
        "round": max(int(turn.get("round", 1)) for turn in turns),
        "method_notes": [
            "Ensemble votes combine stance labels from each role.",
            "Bayesian probabilities update a symmetric prior with confidence-weighted evidence.",
            "Argument mining uses lightweight claim, evidence, and rebuttal heuristics.",
            "Argument graph nodes are mined claims and edges are support or attack relations.",
            "MoE weights are deterministic gates over active debate roles based on the topic and turn quality.",
        ],
        "ensemble": {
            "majority_vote": majority_vote,
            "weighted_vote": weighted_vote,
            "votes": raw_votes,
            "weighted_votes": _rounded_dict(weighted_votes),
        },
        "bayesian": bayesian,
        "argument_mining": {
            "claims": _top_claims(turns, limit=5),
            "evidence_count": sum(len(turn["evidence"]) for turn in turns),
            "rebuttal_count": sum(len(turn["rebuttals"]) for turn in turns),
            "redundancy_count": sum(1 for turn in turns if turn["redundant"]),
        },
        "stance": {"by_role": stance_by_role},
        "confidence": {
            "average": round(sum(turn["confidence"] for turn in turns) / len(turns), 3),
            "by_role": confidence_by_role,
        },
        "credibility": {
            "elo_by_role": elo_by_role,
            "normalized_by_role": credibility_by_role,
        },
        "game_theory": {
            "auction_winner": auction_winner["speaker"],
            "auction_stance": auction_winner["stance"],
            "winning_bid": round(auction_winner["bid"], 3),
            "nash_pressure": round(_disagreement_pressure(weighted_votes), 3),
        },
        "argument_graph": graph,
        "attention": {"top_terms": attention},
        "delphi": delphi,
        "mixture_of_experts": {
            "role_weights": role_gate["normalized_role_weights"],
            "lead_expert": role_gate["lead_expert"],
        },
    }


def format_analytics_report(analysis: dict[str, Any]) -> str:
    if not analysis.get("turn_count"):
        return "No debate analytics are available yet."

    probabilities = analysis["bayesian"]["probabilities"]
    graph = analysis["argument_graph"]
    claims = analysis["argument_mining"]["claims"]
    return "\n".join(
        [
            f"Ensemble majority vote: {analysis['ensemble']['majority_vote']}",
            f"Weighted vote: {analysis['ensemble']['weighted_vote']}",
            f"Bayesian probabilities: support={probabilities['support']}, oppose={probabilities['oppose']}, mixed={probabilities['mixed']}",
            f"Average calibrated confidence: {analysis['confidence']['average']}",
            f"Delphi convergence: {analysis['delphi']['convergence']}",
            f"Auction winner: {analysis['game_theory']['auction_winner']} ({analysis['game_theory']['auction_stance']})",
            f"MoE lead expert: {analysis['mixture_of_experts']['lead_expert']}",
            f"Argument graph: {graph['node_count']} nodes, {graph['support_edges']} support edges, {graph['attack_edges']} attack edges",
            f"Top attention terms: {', '.join(analysis['attention']['top_terms']) or 'none'}",
            "Strong mined claims:",
            *[f"- {claim['speaker']}: {claim['text']}" for claim in claims[:3]],
        ]
    )


def _empty_analysis() -> dict[str, Any]:
    return {
        "turn_count": 0,
        "round": 0,
        "method_notes": [],
        "ensemble": {
            "majority_vote": "mixed",
            "weighted_vote": "mixed",
            "votes": {label: 0 for label in STANCE_LABELS},
            "weighted_votes": {label: 0.0 for label in STANCE_LABELS},
        },
        "bayesian": {
            "leader": "mixed",
            "probabilities": {label: round(1 / 3, 3) for label in STANCE_LABELS},
        },
        "argument_mining": {"claims": [], "evidence_count": 0, "rebuttal_count": 0, "redundancy_count": 0},
        "stance": {"by_role": {}},
        "confidence": {"average": 0.0, "by_role": {}},
        "credibility": {"elo_by_role": {}, "normalized_by_role": {}},
        "game_theory": {"auction_winner": None, "auction_stance": "mixed", "winning_bid": 0.0, "nash_pressure": 0.0},
        "argument_graph": {
            "node_count": 0,
            "edge_count": 0,
            "support_edges": 0,
            "attack_edges": 0,
            "strongest_claims": [],
        },
        "attention": {"top_terms": []},
        "delphi": {"convergence": 0.0, "rounds_analyzed": 0, "last_round_distribution": {}},
        "mixture_of_experts": {"role_weights": {}, "lead_expert": None},
    }


def _analyze_turn(topic: str, turn: dict[str, Any], previous_turns: list[dict[str, Any]]) -> dict[str, Any]:
    content = str(turn.get("content", ""))
    role = str(turn.get("role", "")).lower()
    speaker = str(turn.get("speaker", role or "Agent"))
    sentences = _sentences(content)
    claims = _extract_claims(sentences)
    evidence = _extract_by_markers(sentences, EVIDENCE_MARKERS)
    rebuttals = _extract_by_markers(sentences, REBUTTAL_MARKERS)
    stance = _detect_stance(content, role)
    novelty = _novelty(content, previous_turns)
    confidence = _calibrated_confidence(content, claims, evidence)
    redundant = novelty < 0.35
    elo = _elo_rating(confidence, novelty, len(evidence), redundant)
    credibility = _normalize_elo(elo)

    return {
        "role": role,
        "speaker": speaker,
        "model": turn.get("model", ""),
        "round": int(turn.get("round", 1)),
        "content": content,
        "stance": stance,
        "claims": claims,
        "evidence": evidence,
        "rebuttals": rebuttals,
        "novelty": novelty,
        "confidence": confidence,
        "redundant": redundant,
        "elo": elo,
        "credibility": credibility,
        "bid": round(confidence * novelty * credibility, 3),
        "topic_similarity": _jaccard(_tokens(topic), _tokens(content)),
    }


def _sentences(content: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", content)
        if sentence.strip()
    ]


def _extract_claims(sentences: list[str]) -> list[str]:
    claims = []
    claim_markers = ("should", "is", "are", "will", "must", "means", "causes", "creates")
    for sentence in sentences:
        lower = sentence.lower()
        if any(marker in lower.split() for marker in claim_markers) or len(claims) == 0:
            claims.append(_clip(sentence))
        if len(claims) == 3:
            break
    return claims


def _extract_by_markers(sentences: list[str], markers: set[str]) -> list[str]:
    matches = []
    for sentence in sentences:
        words = set(_tokens(sentence))
        if words & markers:
            matches.append(_clip(sentence))
    return matches[:3]


def _detect_stance(content: str, role: str) -> str:
    words = _tokens(content)
    counts = {
        "support": sum(1 for word in words if word in SUPPORT_TERMS),
        "oppose": sum(1 for word in words if word in OPPOSE_TERMS),
        "mixed": sum(1 for word in words if word in MIXED_TERMS),
    }
    if role.startswith("pro_"):
        counts["support"] += 1.8
    if role.startswith("con_"):
        counts["oppose"] += 1.8
    archetype = role.removeprefix("pro_").removeprefix("con_")
    biased_label = ROLE_STANCE_BIAS.get(role) or ROLE_STANCE_BIAS.get(archetype)
    if biased_label:
        counts[biased_label] += 1.25
    return max(counts, key=counts.get)


def _calibrated_confidence(content: str, claims: list[str], evidence: list[str]) -> float:
    words = _tokens(content)
    raw = 0.52
    raw += min(len(claims), 3) * 0.035
    raw += min(len(evidence), 3) * 0.055
    raw += min(sum(1 for word in words if word in ASSERTIVE_TERMS), 5) * 0.018
    raw -= min(sum(1 for word in words if word in HEDGE_TERMS), 5) * 0.03
    return round(_temperature_scale(_clip_float(raw, 0.08, 0.95), temperature=1.35), 3)


def _temperature_scale(probability: float, temperature: float) -> float:
    probability = _clip_float(probability, 0.001, 0.999)
    logit = log(probability / (1 - probability))
    return 1 / (1 + exp(-(logit / temperature)))


def _novelty(content: str, previous_turns: list[dict[str, Any]]) -> float:
    if not previous_turns:
        return 1.0
    current_tokens = set(_tokens(content))
    similarities = [
        _jaccard(current_tokens, set(_tokens(str(turn.get("content", "")))))
        for turn in previous_turns
    ]
    return round(1 - max(similarities or [0.0]), 3)


def _elo_rating(confidence: float, novelty: float, evidence_count: int, redundant: bool) -> int:
    rating = 1000
    rating += round((confidence - 0.5) * 130)
    rating += round(novelty * 55)
    rating += evidence_count * 18
    if redundant:
        rating -= 45
    return rating


def _normalize_elo(elo: int) -> float:
    return round(_clip_float((elo - 900) / 260, 0.2, 1.25), 3)


def _bayesian_aggregation(
    turns: list[dict[str, Any]], raw_role_weights: dict[str, float]
) -> dict[str, Any]:
    alpha = {label: 1.0 for label in STANCE_LABELS}
    for turn in turns:
        update = (
            turn["confidence"]
            * turn["credibility"]
            * turn["novelty"]
            * raw_role_weights.get(turn["role"], 1.0)
        )
        alpha[turn["stance"]] += update
    total = sum(alpha.values())
    probabilities = {label: round(alpha[label] / total, 3) for label in STANCE_LABELS}
    return {"leader": max(probabilities, key=probabilities.get), "probabilities": probabilities}


def _argument_graph(turns: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    for index, turn in enumerate(turns, start=1):
        claim_text = turn["claims"][0] if turn["claims"] else _clip(turn["content"])
        nodes.append(
            {
                "id": f"c{index}",
                "speaker": turn["speaker"],
                "stance": turn["stance"],
                "text": claim_text,
                "tokens": set(_tokens(claim_text)),
                "strength": turn["confidence"] * turn["novelty"] * turn["credibility"],
            }
        )

    edges = []
    for left_index, left in enumerate(nodes):
        for right in nodes[left_index + 1 :]:
            similarity = _jaccard(left["tokens"], right["tokens"])
            if similarity < 0.12:
                continue
            relation = "support" if left["stance"] == right["stance"] else "attack"
            edges.append({"source": left["id"], "target": right["id"], "relation": relation, "weight": similarity})
            if relation == "support":
                left["strength"] += similarity * 0.15
                right["strength"] += similarity * 0.15
            else:
                left["strength"] -= similarity * 0.08
                right["strength"] -= similarity * 0.08

    strongest = sorted(nodes, key=lambda node: node["strength"], reverse=True)[:3]
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "support_edges": sum(1 for edge in edges if edge["relation"] == "support"),
        "attack_edges": sum(1 for edge in edges if edge["relation"] == "attack"),
        "strongest_claims": [
            {
                "speaker": node["speaker"],
                "stance": node["stance"],
                "strength": round(node["strength"], 3),
                "text": node["text"],
            }
            for node in strongest
        ],
    }


def _attention_terms(topic: str, transcript: list[dict[str, Any]]) -> list[str]:
    topic_tokens = set(_tokens(topic))
    counter: Counter[str] = Counter()
    for turn in transcript:
        for token in _tokens(str(turn.get("content", ""))):
            if token not in STOPWORDS and len(token) > 3:
                counter[token] += 2 if token in topic_tokens else 1
    return [token for token, _count in counter.most_common(8)]


def _delphi_convergence(turns: list[dict[str, Any]]) -> dict[str, Any]:
    by_round: dict[int, dict[str, float]] = defaultdict(lambda: {label: 0.0 for label in STANCE_LABELS})
    for turn in turns:
        by_round[turn["round"]][turn["stance"]] += turn["confidence"] * turn["credibility"]

    distributions = []
    for round_number in sorted(by_round):
        total = sum(by_round[round_number].values()) or 1.0
        distributions.append(
            {
                label: by_round[round_number][label] / total
                for label in STANCE_LABELS
            }
        )

    if len(distributions) < 2:
        convergence = 0.0
    else:
        distance = sum(
            abs(distributions[-1][label] - distributions[-2][label])
            for label in STANCE_LABELS
        ) / 2
        convergence = 1 - distance

    return {
        "convergence": round(convergence, 3),
        "rounds_analyzed": len(distributions),
        "last_round_distribution": _rounded_dict(distributions[-1] if distributions else {}),
    }


def _mixture_of_experts(topic: str, turns: list[dict[str, Any]]) -> dict[str, Any]:
    topic_words = set(_tokens(topic))
    active_roles = sorted({turn["role"] for turn in turns})
    weights = {role: 1.0 for role in active_roles}
    for role in active_roles:
        archetype = _role_archetype(role)
        if (
            archetype in {"researcher", "evidence_researcher"}
            and topic_words & {"evidence", "data", "research", "study", "science", "measure"}
        ):
            weights[role] += 0.45
        if topic_words & {"risk", "safety", "ethics", "regulation", "harm", "failure"}:
            if archetype in {"critic", "rebuttal_critic"}:
                weights[role] += 0.3
            if archetype in {"devils_advocate", "cross_examiner"}:
                weights[role] += 0.25
        if topic_words & {"should", "policy", "strategy", "plan", "future"}:
            if archetype in {"advocate", "lead_advocate"}:
                weights[role] += 0.2
            if archetype in {"critic", "rebuttal_critic"}:
                weights[role] += 0.15
        if (
            archetype in {"devils_advocate", "cross_examiner"}
            and topic_words & {"assumption", "alternative", "counterfactual", "incentive"}
        ):
            weights[role] += 0.35

    quality_by_role: dict[str, list[float]] = defaultdict(list)
    for turn in turns:
        quality_by_role[turn["role"]].append(turn["confidence"] * turn["novelty"] * turn["credibility"])
    for role, scores in quality_by_role.items():
        weights[role] = weights.get(role, 1.0) + (sum(scores) / len(scores))

    total = sum(weights.values()) or 1.0
    normalized = {role: round(weight / total, 3) for role, weight in weights.items()}
    lead_role = max(normalized, key=normalized.get)
    return {
        "raw_role_weights": weights,
        "normalized_role_weights": normalized,
        "lead_expert": _role_label(lead_role),
    }


def _top_claims(turns: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    claims = []
    for turn in turns:
        for claim in turn["claims"]:
            claims.append(
                {
                    "speaker": turn["speaker"],
                    "stance": turn["stance"],
                    "confidence": turn["confidence"],
                    "text": claim,
                }
            )
    return sorted(claims, key=lambda claim: claim["confidence"], reverse=True)[:limit]


def _disagreement_pressure(weighted_votes: dict[str, float]) -> float:
    total = sum(weighted_votes.values())
    if total <= 0:
        return 0.0
    ordered = sorted(weighted_votes.values(), reverse=True)
    if len(ordered) < 2:
        return 0.0
    return 1 - ((ordered[0] - ordered[1]) / total)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9']+", text.lower())


def _jaccard(left: set[str] | list[str], right: set[str] | list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _clip(text: str, limit: int = 180) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _clip_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _rounded_dict(values: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 3) for key, value in values.items()}


def _role_label(role: str) -> str:
    if role.startswith("pro_"):
        return f"Pro {_role_label(role.removeprefix('pro_'))}"
    if role.startswith("con_"):
        return f"Con {_role_label(role.removeprefix('con_'))}"
    return {
        "advocate": "Advocate",
        "critic": "Critic",
        "researcher": "Researcher",
        "devils_advocate": "Devil's Advocate",
        "lead_advocate": "Lead Advocate",
        "rebuttal_critic": "Rebuttal Critic",
        "evidence_researcher": "Evidence Researcher",
        "cross_examiner": "Cross-Examiner",
    }.get(role, role.replace("_", " ").title())


def _role_archetype(role: str) -> str:
    return role.removeprefix("pro_").removeprefix("con_")
