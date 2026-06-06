# Team Roles and Debate Flow

## Team Structure

Each debate has two teams (Pro and Con) with 1 to 4 debaters per team. The number of debaters is configurable per chat session in Chat Settings.

| Debaters Per Team | Active Roles |
| --- | --- |
| 1 | Advocate |
| 2 | Advocate, Rebuttal Critic |
| 3 | Advocate, Rebuttal Critic, Evidence Researcher |
| 4 | Advocate, Rebuttal Critic, Evidence Researcher, Cross-Examiner |

## Role Descriptions

| Role | Job |
| --- | --- |
| **Advocate** | Build the team's central case, keep the argument coherent, and defend the main thesis. |
| **Rebuttal Critic** | Attack the opposing team's strongest point and protect your team from direct criticism. |
| **Evidence Researcher** | Add evidence, examples, missing context, and careful uncertainty notes for your team. |
| **Cross-Examiner** | Ask pressure questions, expose contradictions, and force the other team to answer clearly. |
| **Judge Assistant** (neutral, optional) | Audit the debate for missed points, unanswered claims, evidence gaps, statistics, and scoring risks. Does not choose the final winner. |
| **Judge Panelist** (neutral, optional) | In 3/5-judge mode, each panelist votes independently before the final weighted consensus is computed. |
| **Judge** (neutral) | Use the debate transcript, Judge Assistant audit, panel votes, and analytics to make or summarize the final decision. |

## Debate Flow

1. **User sends a message.** The intent classifier determines whether to start a debate or a chat.
2. **Constructive phase.** Pro and Con Advocates build their opening cases.
3. **Cross-examination and evidence phases.** Critics or Examiners ask pointed questions, and Researchers add evidence when those roles are active.
4. **Discussion Time.** Advocates speak as team spokespersons. Discussion Time 1 opens with Pro Advocate; Discussion Time 2 opens with Con Advocate. One-debater mode uses one Open Discussion block with Pro-open and Con-open mini-rounds.
5. **Rebuttal and closing phases.** Critics attack the strongest opposing points, then Advocates close.
6. **Judge Assistant audits** (if enabled) the full transcript and analytics.
7. **Judge delivers verdict**. In single-judge mode, the Judge verdict is combined with the configured analytics weight. In panel mode, 3 or 5 Judge Panelists vote independently and the final Judge message summarizes the panel votes, analytics signal, weighted scores, clear winner, and why.

## Discussion Rules

- Discussion Messages Per Team caps each team at 1–4 Advocate messages per discussion phase.
- Advocates may use teammate material from Researchers, Critics, and Examiners, but only Advocates speak during discussion.
- Agents address specific argument content directly. They avoid narration like "my opponent says" and avoid referring to turn numbers as arguments.
- Cross-examination turns ask 2–4 questions after a short setup sentence; they do not answer their own questions or become full rebuttals.

## Streaming

All debate content streams token by token over WebSocket. The frontend renders each delta as it arrives. A `StreamingSanitizer` strips any `<think>` blocks that some models emit, so reasoning traces never appear in the UI. Each saved message includes phase metadata (`phase_key`, `phase_title`, `phase_index`, `phase_total`, `phase_kind`) so the UI can reconstruct the debate flow from saved messages.

## Truncation Handling

If a model response hits the max-token limit (`finish_reason: "length"`), the system automatically sends a continuation request to the same model, asking it to pick up where it stopped. If the continuation also truncates, a notice is appended suggesting the user increase the role's max tokens in Chat Settings.

## Retry Logic

Provider errors (overloaded, rate limit, timeout, connection errors) are retried up to 3 times with increasing delays, but only if no output has been streamed yet. Once output has started streaming, the error is surfaced to the user.
