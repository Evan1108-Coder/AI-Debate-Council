# WebSocket Protocol

## Client to Server

```json
{
  "type": "start_interaction",
  "topic": "Should AI be regulated?",
  "model": "claude-sonnet-4-6"
}
```

## Server to Client Events

| Event Type | Description |
| --- | --- |
| `debate_started` | Debate created. Includes debate record, assignments, judge info. |
| `interaction_started` | Chat mode started. Includes mode and selected model. |
| `practice_state_updated` | Practice debate state changed, including side, flow, and rounds left. |
| `team_preparation_started` / `team_preparation_completed` | Pro and Con private notebooks are being prepared or have finished. |
| `message_started` | A new message is about to stream. Includes speaker, role, model, round. |
| `message_delta` | A token chunk for the current stream. |
| `message_replaced` | Replace the entire content of a streaming message (used on errors). |
| `message_completed` | A message finished streaming. Includes the saved message record and `cost_summary`. |
| `analysis_updated` | Analytics recalculated after a debater turn. |
| `debate_completed` | Debate finished. Includes judge summary, active debate count, and `cost_summary`. |
| `interaction_completed` | Chat finished. Includes `cost_summary`. |
| `error` | An error occurred. Includes error message string. |
