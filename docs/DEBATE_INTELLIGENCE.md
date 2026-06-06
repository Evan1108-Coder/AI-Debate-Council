# Debate Intelligence and Analytics

The backend includes a lightweight analytics engine in `backend/app/analytics.py`. It requires no extra ML dependencies — all scoring is done with Python standard library math. Each debate transcript is analyzed and the results are streamed to the frontend, included in the Judge prompt, and optionally weighted into the final verdict.

## Scoring Methods

| Method | Description |
| --- | --- |
| **Ensemble Voting** | Each role gets a stance label (support, oppose, mixed). The app reports both majority vote and confidence-weighted vote. |
| **Bayesian Inference** | A symmetric prior is updated with confidence-weighted, credibility-adjusted stance evidence. Produces probabilities for support, oppose, and mixed. |
| **Argument Mining** | Heuristics extract claims (sentences with "should", "is", "must", etc.), evidence cues ("because", "study", "data", etc.), rebuttals ("however", "but", "counter", etc.), and flags redundant turns. |
| **Argument Graph** | Claims become nodes. Similar claims (by Jaccard similarity) create support edges (same stance) or attack edges (opposing stance). Node strength is adjusted by edge relationships. |
| **Game Theory** | An auction score lets high-confidence, novel arguments bid for influence. Nash pressure estimates the level of disagreement. |
| **ELO-Style Credibility** | Each turn earns an ELO rating based on confidence, novelty, evidence count, and redundancy. Ratings are normalized to a 0.2–1.25 credibility multiplier. |
| **Confidence Calibration** | Raw confidence is computed from claim count, evidence count, assertive terms, and hedge terms. Temperature scaling softens extreme values to avoid false certainty. |
| **Attention Mechanisms** | Frequent high-salience terms from the transcript (excluding stopwords) become attention terms shown in the UI and available to the Judge. Topic-related terms get double weight. |
| **Delphi Convergence** | Round-by-round stance distributions are compared. Convergence measures how much the debate has stabilized (1.0 = fully converged, 0.0 = maximum shift). |
| **Mixture of Experts (MoE)** | Deterministic role gates weight which archetype should matter most based on topic keywords (e.g., "evidence"/"data" boosts researchers, "risk"/"safety" boosts critics). Gate weights are combined with per-turn quality scores. |

## Analytics in the UI

The Graphs & Statistics panel shows:

- **Phase timeline**: A visual progress bar showing each debate phase, the current phase, and completed/total counts.
- **Metrics row**: Weighted vote, Bayesian leader, average confidence, Delphi convergence.
- **Bayesian pie chart**: Support vs. oppose vs. mixed probabilities.
- **Role weights bar chart**: MoE-normalized weights per active role.
- **Stance votes bar chart**: Weighted vote totals per stance.
- **Bayesian trend line chart**: Round-by-round probability history with labeled axes (X = analytics update number, Y = probability %).
- **Game and graph stats**: Auction winner, Nash pressure, node count, edge counts.
- **Session charts** (cross-debate):
  - **Win Rate by Team**: Pro vs. Con win counts and rates across all completed debates in the session.
  - **Cost Breakdown by Phase**: Estimated USD cost grouped by debate phase (Constructive, Cross-exam, Evidence, Rebuttal, Discussion, Closing, Judgment).
  - **Debate Duration**: Wall-clock duration of each completed debate.
  - **Messages per Role**: Pie chart showing message counts by role group (Advocate, Critic, Researcher, Examiner, Judge).
  - **Citation Box**: URLs cited by Evidence Researchers across all debates, with speaker, debate name, phase, and domain.
- **Argument mining details**: Evidence cue count, rebuttal cue count, redundant turn count, strongest mined claims.
- **Attention terms**: Top 8 salient terms from the transcript.

## Debate Intelligence Tab

The Debate Intelligence tab stores structured records created from the actual transcript:

- **Claim Ledger**: tracked claims that can later be supported, challenged, answered, dropped, conceded, or used by the Judge.
- **Challenge And Resolution Tracker**: critic/examiner attacks and whether they were answered, ignored, or left unresolved.
- **Evidence Ledger**: evidence records, uncertainty notes, and URL citations when researchers provide source links.
- **Judge Scorecard**: claim count, challenge count, evidence count, unanswered challenges, judge mode, and detected winner.
- **Verdict Review**: user challenges and winner overrides. Overrides affect charts such as Win Rate by Team but do not rewrite the original Judge message.
- **Team Rooms**: view-only Pro and Con private notebooks generated during team preparation.
