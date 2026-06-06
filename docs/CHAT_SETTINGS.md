# Chat Settings

Each session stores its own settings. Changes take effect on the next turn — even mid-debate for settings like debaters per team. Settings are accessible from the Chat Settings panel in the UI.

The settings panel is organized into sections: Overall Model, Debating Flow (debaters per team, discussion messages per team, debate rounds, with a live flow preview), Debaters & Teams or Practice Agents, Council Assistant, Debate Intelligence, Judgment Quality, Prompt & Tone, Output & Display, and Advanced.

## Session-Level Settings

| Setting | Default | Range | Description |
| --- | --- | --- | --- |
| Overall Model | (none) | Any unlocked model | Default model for all roles in this chat. |
| Debaters per team | 2 | 1–4 | Number of debater roles active per team. |
| Discussion Messages Per Team | 3 | 1–4 | Advocate messages allowed for each team in each discussion phase. |
| Debate rounds | 2 | 1–6 | Number of advocate-led discussion phases in the professional flow. |
| Judge Assistant | On | On/Off | Whether the Judge Assistant audits before the verdict. |
| Judge Panel Size | 1 | 1, 3, 5 | Number of independent Judge Panelists. 3 and 5 are more robust but cost more model calls. |
| Analytics Weight | 0.25 | 0–0.75 | How much structured analytics can influence the final verdict compared with the AI Judge or panel votes. |
| Allow Verdict Challenge / Override | On | On/Off | Allows the user to challenge the verdict or override the saved winner in Debate Intelligence. |
| Temperature | 0.55 | 0.00–1.00 | Default temperature for all roles. |
| Max tokens | 700 | 120–2000 | Default max tokens for all roles. |
| Debate tone | Academic | Academic, Casual, Formal, Aggressive | Injected into all system prompts. |
| Language | English | English, Chinese, Cantonese | Injected into all system prompts. |
| Response length | Normal | Concise, Normal, Detailed | Controls word limits in debater prompts. |
| Context window | 2 | 0–6 | How many rounds of recent debate history are included in debater prompts. |
| Auto-scroll | On | On/Off | Auto-scroll to latest message. |
| Show timestamps | Off | On/Off | Show message timestamps. |
| Show token count | Off | On/Off | Show estimated token counts. |
| Show money cost | On | On/Off | Display estimated API cost. Council Assistant messages show their own cost; debate messages show the final total by default. |
| Cost currency | USD | USD, CNY, HKD, EUR, JPY, GBP, AUD, CAD, SGD | Currency for cost display. |
| Show model costs | Off | On/Off | Show per-model cost breakdown in addition to the total. |
| Show Every Message Cost In Debate | Off | On/Off | Show individual debater, Judge Assistant, and Judge message costs during debates, plus the final overall debate cost. |
| Fact-check mode | Off | On/Off | Flag uncertain claims (reserved for tool integration). |
| Export format | Markdown | Markdown, PDF, JSON | Reserved for future export feature. |
| Auto-save interval | 30 | 5–300 seconds | Reserved for future auto-save feature. |

## Per-Agent Settings

Each agent role can override model and generation settings. This includes Advocate, Rebuttal Critic, Evidence Researcher, Cross-Examiner, Judge Assistant, Judge, Council Assistant, Practice Debater, and Debate Trainer.

| Setting | Default | Description |
| --- | --- | --- |
| Model | Use overall model | Override model for this role only. |
| Temperature | Inherits session default | Override temperature for this role. |
| Max tokens | Inherits session default | Override max tokens for this role. |
| Response length | Inherits session default | Override word limit for this role. |
| Web search | Off | Evidence Researcher only: flag for web search integration. |
| Always On | Off | Council Assistant only: bypass intent classifier, always use chat mode. |

Team role settings (Advocate, Rebuttal Critic, etc.) apply to both the Pro and Con versions of that role.
