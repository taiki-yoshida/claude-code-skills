---
name: azure-openai
description: Integrate Azure OpenAI services including GPT Realtime API (gpt-realtime-1.5) for real-time audio conversations via WebRTC. Use when user wants to build voice/audio AI apps, integrate Azure OpenAI realtime API, create conversational AI with speech, or connect to gpt-realtime models.
---

# Azure OpenAI Integration

Build applications that integrate with Azure OpenAI services, with a focus on the GPT Realtime API for real-time audio conversations. This skill captures patterns from production implementations.

## When to use

- User wants to build a voice/audio AI application
- User mentions Azure OpenAI Realtime API, gpt-realtime, or speech-to-speech
- User wants WebRTC audio streaming with GPT models
- User needs to integrate Azure OpenAI into a web application

## Supported Models

### GPT Realtime Models (Audio)

| Model | Version | Regions |
|-------|---------|---------|
| `gpt-realtime-1.5` | 2026-02-23 | East US 2, Sweden Central |
| `gpt-realtime` | 2025-08-28 | East US 2, Sweden Central |
| `gpt-realtime-mini` | 2025-12-15 | East US 2, Sweden Central |
| `gpt-4o-realtime-preview` | 2024-12-17 | East US 2, Sweden Central |

### Standard Chat/Completion Models

| Model | Use Case |
|-------|----------|
| `gpt-4o` | Multimodal (text + vision) |
| `gpt-4o-mini` | Fast, cost-effective |
| `gpt-4` | Complex reasoning |

## GPT Realtime API Architecture

```
┌──────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│   Browser        │     │   Your Backend      │     │   Azure OpenAI       │
│   (WebRTC)       │     │   (Token Service)   │     │   (Realtime API)     │
├──────────────────┤     ├─────────────────────┤     ├──────────────────────┤
│ 1. Request token │────▶│ 2. Generate         │     │                      │
│                  │     │    ephemeral token  │────▶│ /v1/realtime/        │
│                  │◀────│    with session cfg │◀────│ client_secrets       │
│ 3. WebRTC offer  │─────────────────────────────────▶│                      │
│                  │◀────────────────────────────────│ 4. SDP answer        │
│ 5. Audio stream  │◀═══════════════════════════════▶│ 6. Audio response    │
└──────────────────┘     └─────────────────────┘     └──────────────────────┘
```

## Backend: Token Generation (.NET)

Your backend generates ephemeral tokens with session configuration. **Never expose your API key to the browser.**

```csharp
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Configuration;

public class TokenApi
{
    private readonly IConfiguration _config;
    private readonly HttpClient _httpClient;

    public TokenApi(IConfiguration config, IHttpClientFactory httpClientFactory)
    {
        _config = config;
        _httpClient = httpClientFactory.CreateClient();
    }

    [Function("GetRealtimeToken")]
    public async Task<IActionResult> GetRealtimeToken(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "realtime/token")] HttpRequest req)
    {
        var body = await JsonSerializer.DeserializeAsync<TokenRequest>(req.Body,
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

        var resource = _config["AZURE_OPENAI_RESOURCE"];
        var apiKey = _config["AZURE_OPENAI_API_KEY"];
        var model = _config["AZURE_OPENAI_MODEL"] ?? "gpt-realtime-1.5";

        // Session configuration
        var sessionConfig = new
        {
            session = new
            {
                type = "realtime",
                model = model,
                instructions = body?.SystemPrompt ?? "You are a helpful assistant.",
                audio = new
                {
                    output = new
                    {
                        voice = body?.Voice ?? "alloy"  // alloy|ash|ballad|coral|echo|sage|shimmer|verse|marin
                    }
                }
            }
        };

        // GA endpoint (not preview)
        var url = $"https://{resource}.openai.azure.com/openai/v1/realtime/client_secrets";

        var requestContent = new StringContent(
            JsonSerializer.Serialize(sessionConfig),
            Encoding.UTF8,
            "application/json");

        _httpClient.DefaultRequestHeaders.Clear();
        _httpClient.DefaultRequestHeaders.Add("api-key", apiKey);

        var response = await _httpClient.PostAsync(url, requestContent);
        var responseBody = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
        {
            return new ObjectResult(new { error = responseBody }) { StatusCode = (int)response.StatusCode };
        }

        var tokenResponse = JsonSerializer.Deserialize<JsonElement>(responseBody);
        var ephemeralToken = tokenResponse.GetProperty("value").GetString();

        return new OkObjectResult(new
        {
            token = ephemeralToken,
            endpoint = $"https://{resource}.openai.azure.com"
        });
    }

    private record TokenRequest(string? SystemPrompt, string? Voice);
}
```

**Program.cs** - Register HttpClientFactory:

```csharp
var builder = FunctionsApplication.CreateBuilder(args);
builder.ConfigureFunctionsWebApplication();
builder.Services.AddHttpClient();
builder.Build().Run();
```

## Frontend: WebRTC Connection (TypeScript)

```typescript
export interface SessionConfig {
  systemPrompt: string;
  voice: string;
  prePrompt: string;  // Initial message to start conversation
  inputDeviceId?: string;
  outputDeviceId?: string;
  onTranscript?: (text: string, role: 'user' | 'assistant') => void;
  onStateChange?: (state: string) => void;
}

export async function createRealtimeSession(config: SessionConfig) {
  // 1. Get ephemeral token from your backend
  const tokenRes = await fetch('/api/realtime/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      systemPrompt: config.systemPrompt,
      voice: config.voice
    })
  });
  const { token, endpoint } = await tokenRes.json();

  // 2. Create RTCPeerConnection
  const peerConnection = new RTCPeerConnection();

  // 3. Set up audio playback
  const audioElement = document.createElement('audio');
  audioElement.autoplay = true;

  // Set output device if specified
  if (config.outputDeviceId && 'setSinkId' in audioElement) {
    await (audioElement as any).setSinkId(config.outputDeviceId);
  }

  peerConnection.ontrack = (event) => {
    if (event.streams.length > 0) {
      audioElement.srcObject = event.streams[0];
    }
  };

  // 4. Get microphone
  const mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: config.inputDeviceId
      ? { deviceId: { exact: config.inputDeviceId } }
      : true
  });
  peerConnection.addTrack(mediaStream.getAudioTracks()[0]);

  // 5. Create data channel for events
  const dataChannel = peerConnection.createDataChannel('realtime-channel');

  dataChannel.onopen = () => {
    config.onStateChange?.('Connected');

    // Send pre-prompt to start conversation
    if (config.prePrompt) {
      dataChannel.send(JSON.stringify({
        type: 'conversation.item.create',
        item: {
          type: 'message',
          role: 'user',
          content: [{ type: 'input_text', text: config.prePrompt }]
        }
      }));
      dataChannel.send(JSON.stringify({ type: 'response.create' }));
    }
  };

  dataChannel.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    // Handle transcription events
    if (msg.type === 'conversation.item.input_audio_transcription.completed') {
      config.onTranscript?.(msg.transcript, 'user');
    } else if (msg.type === 'response.output_audio_transcript.done') {
      config.onTranscript?.(msg.transcript, 'assistant');
    }
  };

  // 6. Create and send SDP offer
  const offer = await peerConnection.createOffer();
  await peerConnection.setLocalDescription(offer);

  // 7. Send to Azure OpenAI WebRTC endpoint
  const webrtcUrl = `${endpoint}/openai/v1/realtime/calls?webrtcfilter=on`;
  const sdpResponse = await fetch(webrtcUrl, {
    method: 'POST',
    body: offer.sdp,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/sdp',
    },
  });

  const answerSdp = await sdpResponse.text();
  await peerConnection.setRemoteDescription({ type: 'answer', sdp: answerSdp });

  // Return cleanup function
  return {
    close: () => {
      dataChannel.close();
      peerConnection.close();
      mediaStream.getTracks().forEach(track => track.stop());
    }
  };
}
```

## Critical Gotchas

### 1. GA vs Preview Endpoints

**Use GA endpoints** (not preview):

| Purpose | GA Endpoint |
|---------|-------------|
| Token generation | `/openai/v1/realtime/client_secrets` |
| WebRTC calls | `/openai/v1/realtime/calls` |

**Preview endpoints (deprecated)**:
- `/openai/realtimeapi/sessions` — DO NOT USE

### 2. Authentication Methods

**Backend (token generation)**: Use API key in `api-key` header
```
api-key: YOUR_API_KEY
```

**Frontend (WebRTC)**: Use ephemeral token in `Authorization` header
```
Authorization: Bearer EPHEMERAL_TOKEN
```

### 3. WebRTC Filter Parameter

Add `?webrtcfilter=on` to limit data channel messages and keep prompts private:
```typescript
const url = `${endpoint}/openai/v1/realtime/calls?webrtcfilter=on`;
```

With filter ON, only these events are sent to browser:
- `input_audio_buffer.speech_started/stopped`
- `output_audio_buffer.started/stopped`
- `conversation.item.input_audio_transcription.completed`
- `response.output_audio_transcript.delta/done`

### 4. Voice Options

Available voices: `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, `verse`, `marin`

Set in session config when generating token:
```json
{
  "session": {
    "audio": { "output": { "voice": "alloy" } }
  }
}
```

### 5. Audio Device Selection

Enumerate devices and request specific deviceId:
```typescript
// Get devices
const devices = await navigator.mediaDevices.enumerateDevices();
const inputs = devices.filter(d => d.kind === 'audioinput');
const outputs = devices.filter(d => d.kind === 'audiooutput');

// Use specific input
await navigator.mediaDevices.getUserMedia({
  audio: { deviceId: { exact: selectedDeviceId } }
});

// Use specific output (setSinkId)
if ('setSinkId' in audioElement) {
  await audioElement.setSinkId(outputDeviceId);
}
```

### 6. CORS Configuration

For production, configure CORS on your Azure Functions:
```bash
az functionapp cors add --name <app> --resource-group <rg> \
  --allowed-origins "https://your-frontend-domain.com"
```

### 7. Triggering Conversation Start

Send initial message + response.create to make AI start talking:
```typescript
// Create user message
dataChannel.send(JSON.stringify({
  type: 'conversation.item.create',
  item: {
    type: 'message',
    role: 'user',
    content: [{ type: 'input_text', text: 'Tell me about Japan.' }]
  }
}));

// Trigger AI response
dataChannel.send(JSON.stringify({ type: 'response.create' }));
```

## Environment Variables

```bash
# Azure Functions local.settings.json or App Settings
AZURE_OPENAI_RESOURCE=your-resource-name
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_MODEL=gpt-realtime-1.5
DEFAULT_SYSTEM_PROMPT=You are a helpful assistant.
DEFAULT_VOICE=alloy
```

## Session Configuration Options

| Field | Required | Description |
|-------|----------|-------------|
| `session.type` | Yes | Must be `"realtime"` |
| `session.model` | Yes | Model deployment name |
| `session.instructions` | No | System prompt |
| `session.audio.output.voice` | No | Voice selection |

## Troubleshooting

### 401 Unauthorized
- Verify API key is correct
- Check ephemeral token hasn't expired (tokens are short-lived)
- Ensure resource name is correct (no `.openai.azure.com` suffix)

### WebRTC Connection Failed
- Ensure HTTPS (getUserMedia requires secure context)
- Check browser supports WebRTC
- Verify microphone permissions granted

### No Audio Output
- Check `audioElement.autoplay = true`
- Browser may block autoplay — user interaction required first
- Verify output device selection

### Model Not Found
- Confirm model is deployed in your Azure OpenAI resource
- Check deployment name matches exactly (case-sensitive)
- Verify region supports the model (East US 2 or Sweden Central)

## When to pair with other skills

- Pair with `azure-swa-functions-stack` for a complete web app with frontend and backend
- Pair with `azure-functions-mcp` if you also want to expose MCP tools

## References

- [GPT Realtime API via WebRTC](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/realtime-audio-webrtc)
- [Supported models](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/realtime-audio)
- [Realtime API events reference](https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-reference)
