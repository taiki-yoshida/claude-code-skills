---
name: azure-swa-functions-stack
description: Scaffold and deploy a React+Vite frontend on Azure Static Web Apps (free plan) paired with a standalone Azure Functions backend. Use when user wants a full-stack app on Azure using SWA + Functions, needs cheap hosting for an admin/demo tool, asks about CORS setup between SWA and Functions, or wants a production-ready React+Functions deployment pattern.
---

# Azure SWA + Functions Full-Stack

Ship a React admin/tool UI on Azure Static Web Apps (free plan) that calls a standalone Azure Functions backend. Captures the patterns and gotchas from a production deployment.

## When to use

- User wants a full-stack app on Azure with a React frontend and C#/TypeScript Functions backend
- User mentions "Static Web Apps + Functions", "SWA free plan", or needs cheap Azure hosting
- User needs the standalone Functions app (not SWA's built-in managed Functions) because they're using Flex Consumption or non-Consumption plans

## Architecture

```
┌─────────────────────────────────┐         ┌────────────────────────────┐
│ Azure Static Web Apps (free)    │         │ Azure Functions (Flex)     │
│ ─────────────────────────────── │  CORS   │ ────────────────────────── │
│ React + Vite SPA                │ ──────▶ │ REST API (/api/*)          │
│ dist/ served from CDN           │         │ MCP tools (optional)       │
│ staticwebapp.config.json        │         │ Azure Storage backed       │
└─────────────────────────────────┘         └────────────────────────────┘
```

**Why standalone Functions** instead of SWA's built-in API:
- SWA managed Functions only support Consumption plan (no Flex, no Premium)
- You can't add the MCP extension to managed Functions
- You need more than 60s execution time

## Project layout

```
my-app/
├── frontend/                    # React SPA → Azure Static Web Apps
│   ├── src/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── staticwebapp.config.json
│   └── package.json
├── functions/                   # Azure Functions → standalone deploy
│   ├── host.json
│   ├── local.settings.json
│   └── (.NET or TypeScript project)
├── swa-cli.config.json          # Optional local orchestration
└── .gitignore
```

## Frontend scaffold

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router-dom @tanstack/react-query lucide-react
npm install -D tailwindcss @tailwindcss/vite
```

### vite.config.ts (CRITICAL for local dev)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:7071',
        changeOrigin: true
      }
    }
  }
})
```

The `/api` proxy is essential — it forwards frontend calls at `localhost:5173/api/*` to the Functions app at `localhost:7071/api/*`, eliminating CORS issues during local dev.

### staticwebapp.config.json

```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/assets/*", "/api/*"]
  }
}
```

This makes client-side routing work — any URL that isn't a static asset or API call gets served `index.html` so React Router can handle it.

### src/main.css

```css
@import "tailwindcss";
```

## API client pattern

`src/services/api.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function authHeaders(): Record<string, string> {
  const token = sessionStorage.getItem('auth');
  return token ? { 'X-Auth-Token': token } : {};
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...options?.headers },
  });
  if (res.status === 401) {
    sessionStorage.removeItem('auth');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}
```

**Key pattern**: `VITE_API_BASE_URL` defaults to `/api` for local dev (uses the Vite proxy). In production, it's overridden at build time to point to the Functions app directly:

```bash
VITE_API_BASE_URL="https://<func-app>.azurewebsites.net/api" npx vite build
```

## Functions backend (see also: azure-functions-mcp skill)

`functions/local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated"
  },
  "Host": {
    "LocalHttpPort": 7071,
    "CORS": "http://localhost:5173",
    "CORSCredentials": false
  }
}
```

## CORS configuration (PRODUCTION — CRITICAL)

**SWA free plan has NO built-in API proxy**. The frontend is served from `*.azurestaticapps.net` and makes cross-origin calls to the Functions app. You MUST configure CORS on the Functions app:

```bash
az functionapp cors add \
  --name <function-app-name> \
  --resource-group <rg> \
  --allowed-origins "https://<swa-name>.azurestaticapps.net"
```

Verify:

```bash
az functionapp cors show --name <app> --resource-group <rg>
```

Should list your SWA origin. If you add a custom domain to the SWA later, add that origin too.

## Simple password auth pattern (optional)

For admin/demo tools where you just need a gate (not full user accounts):

**Backend** (`AuthApi.cs`):

```csharp
public class AuthApi
{
    private readonly string _password;
    public AuthApi(IConfiguration config) { _password = config["ADMIN_PASSWORD"] ?? "demo"; }

    [Function("Login")]
    public async Task<IActionResult> Login(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "auth/login")] HttpRequest req)
    {
        var body = await JsonSerializer.DeserializeAsync<LoginRequest>(req.Body, new() { PropertyNameCaseInsensitive = true });
        if (body?.Password != _password) return new UnauthorizedObjectResult(new { error = "Invalid password." });
        return new OkObjectResult(new { ok = true });
    }

    private record LoginRequest(string Password);
}
```

Set the password as an app setting (don't commit to repo):

```bash
az functionapp config appsettings set --name <app> --resource-group <rg> \
  --settings 'ADMIN_PASSWORD=<your-password>'
```

**Frontend**: store the password itself as the "token" in `sessionStorage.setItem('auth', password)` after successful login, and send as `X-Auth-Token` header. All protected endpoints check the header against the same env var.

Wrap routes with a guard component:

```tsx
function RequireAuth({ children }: { children: ReactNode }) {
  if (!sessionStorage.getItem('auth')) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/*" element={<RequireAuth><Layout>...</Layout></RequireAuth>} />
</Routes>
```

This is session-only — closing the tab logs you out. Good enough for demo tools. NOT suitable for multi-user production apps.

## Local dev workflow

```bash
# Terminal 1: storage emulator (if backend needs it)
azurite --silent --location .azurite

# Terminal 2: backend
cd functions && func start     # → http://localhost:7071

# Terminal 3: frontend
cd frontend && npm run dev     # → http://localhost:5173
```

Vite proxy forwards `/api/*` to 7071, so everything "just works" cross-origin-free.

## Production deployment

### 1. Deploy Functions

```bash
cd functions
func azure functionapp publish <function-app-name> --dotnet-isolated
```

### 2. Build frontend with production URLs

```bash
cd frontend
VITE_API_BASE_URL="https://<func-app>.azurewebsites.net/api" \
  npx vite build
```

### 3. Deploy to Static Web Apps

Get the deployment token from the Azure portal (SWA → Overview → Manage deployment token), then:

```bash
npx @azure/static-web-apps-cli deploy dist \
  --deployment-token "<token>" \
  --env production
```

**Always use `--env production`** — omitting it deploys to a preview environment that isn't visible at the main URL.

### 4. Configure CORS (one-time)

```bash
az functionapp cors add --name <func-app> --resource-group <rg> \
  --allowed-origins "https://<swa>.azurestaticapps.net"
```

## Gotchas

### 1. Flex Consumption + SWA managed API don't mix

If you want Flex Consumption (better cold start, more memory), you MUST use a standalone Functions app — SWA's built-in API is Consumption-only. That's why this skill uses the standalone pattern.

### 2. Environment variables at build time vs runtime

`VITE_*` env vars are INLINED into the JS bundle at build time, not runtime. Changing `VITE_API_BASE_URL` after deploy requires a rebuild. If you need runtime config, fetch a `/config.json` from the public folder instead.

### 3. Preview vs production deploy

`swa deploy` without `--env production` creates a preview environment at a different URL (e.g., `https://<swa>-preview.azurestaticapps.net`). Your main URL stays on the old build. Always pass `--env production` for real deployments.

### 4. CORS + custom domain

If you add a custom domain to your SWA, you must add that origin to the Functions CORS list separately — the `*.azurestaticapps.net` origin does not cover it.

### 5. Trailing slashes on API paths

Azure Functions HTTP triggers are picky about trailing slashes. `GET /api/modules` and `GET /api/modules/` may behave differently. Be consistent in your API client.

## When to pair with other skills

- Pair with `azure-functions-mcp` if the backend also exposes MCP tools. The same Functions app can serve both the REST API (for the frontend) and MCP endpoints (for Claude/Copilot) — just make sure function names are unique across the two.
