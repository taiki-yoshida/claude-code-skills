# azure-openai

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) for integrating Azure OpenAI services, with a focus on the GPT Realtime API for real-time audio conversations via WebRTC.

## What it does

When your prompt mentions building voice/audio AI apps with Azure OpenAI, or integrating the GPT Realtime API, Claude automatically loads this skill and applies the patterns inside. The skill covers:

- GPT Realtime API architecture (token service + WebRTC)
- Ephemeral token generation in .NET backend
- WebRTC connection setup in TypeScript/JavaScript
- Audio device selection (input/output)
- Session configuration (voice, system prompt, pre-prompt)
- Conversation triggering and transcript handling

## Installation

```bash
# Install to your Claude Code skills directory
cp -r azure-openai ~/.claude/skills/
```

Or see the [parent README](../README.md) for other installation options.

## Triggers

Claude will load this skill when you say things like:

- "Build a voice chat app with Azure OpenAI"
- "Integrate gpt-realtime-1.5 for audio conversations"
- "How do I use the Azure OpenAI Realtime API?"
- "Create a speech-to-speech AI assistant"
- "Connect WebRTC to Azure OpenAI"

## Key gotchas (why this skill exists)

The skill captures several painful lessons from real builds:

### GA vs Preview endpoints

The Realtime API has moved to GA. Use these endpoints:
- **Token**: `/openai/v1/realtime/client_secrets` (not `/openai/realtimeapi/sessions`)
- **WebRTC**: `/openai/v1/realtime/calls` (not regional preview URLs)

### Two-step authentication

1. **Backend** uses API key to generate ephemeral token
2. **Frontend** uses ephemeral token for WebRTC connection

Never expose your API key to the browser.

### WebRTC filter parameter

Add `?webrtcfilter=on` to keep your system prompt private. Without it, all events (including your instructions) are sent to the browser.

### Triggering conversation start

The AI won't speak first unless you send an initial message + `response.create`:
```javascript
dataChannel.send(JSON.stringify({
  type: 'conversation.item.create',
  item: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'Hello!' }] }
}));
dataChannel.send(JSON.stringify({ type: 'response.create' }));
```

### Audio device selection

Browser `getUserMedia` and `setSinkId` have quirks:
- Must request permission before `enumerateDevices` returns labels
- `setSinkId` for output device is not supported in all browsers
- Always use `{ deviceId: { exact: id } }` for specific device selection

## Supported models

| Model | Version | Regions |
|-------|---------|---------|
| `gpt-realtime-1.5` | 2026-02-23 | East US 2, Sweden Central |
| `gpt-realtime` | 2025-08-28 | East US 2, Sweden Central |
| `gpt-realtime-mini` | 2025-12-15 | East US 2, Sweden Central |

## See also

- [GPT Realtime API documentation](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/realtime-audio-webrtc)
- Companion skill: [`azure-swa-functions-stack`](../azure-swa-functions-stack) — pairs with a React frontend on Static Web Apps
- Companion skill: [`azure-functions-mcp`](../azure-functions-mcp) — if you also need MCP tools
