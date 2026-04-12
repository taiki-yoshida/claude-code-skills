# azure-swa-functions-stack

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) for scaffolding and deploying a React + Vite frontend on Azure Static Web Apps (free plan) paired with a standalone Azure Functions backend.

## What it does

When your prompt mentions building a full-stack app on Azure with React + Functions (or similar), Claude automatically loads this skill. The skill covers:

- Project layout (`frontend/` + `functions/`)
- Vite config with dev proxy (eliminates local CORS issues)
- `staticwebapp.config.json` for SPA routing
- Production CORS setup on Functions
- Build-time env var pattern (`VITE_API_BASE_URL`)
- SWA CLI deployment with tokens
- Optional: simple password gate pattern for demo/admin tools

## Installation

```bash
cp -r azure-swa-functions-stack ~/.claude/skills/
```

Or see the [parent README](../README.md) for other installation options.

## Triggers

Claude will load this skill when you say things like:

- "Build a React app on Azure Static Web Apps with a Functions backend"
- "Deploy React + Vite to SWA with standalone Functions"
- "How do I set up CORS between SWA and Azure Functions?"
- "I want cheap Azure hosting for an admin tool"

## Why standalone Functions instead of SWA managed API?

SWA's built-in "managed" Functions have limitations that bite in production:

- **Consumption plan only** — can't use Flex Consumption, Premium, or Dedicated
- **No custom extensions** — can't add the MCP extension, Durable Functions, etc.
- **60-second timeout** — not enough for longer operations

Using a standalone Functions app lets you pick any plan, add any extension, and set longer timeouts. The trade-off: you configure CORS yourself (the skill shows exactly how).

## Key gotchas (why this skill exists)

### CORS is mandatory on SWA free plan

SWA free plan does NOT proxy API calls. The frontend at `*.azurestaticapps.net` makes cross-origin requests directly to the Functions app. You MUST run:

```bash
az functionapp cors add --name <func-app> --resource-group <rg> \
  --allowed-origins "https://<swa>.azurestaticapps.net"
```

Skip this and every API call fails with a CORS error in the browser.

### `VITE_*` env vars are build-time only

These variables are inlined into the JS bundle during `vite build`. You cannot change them after deploy — you must rebuild. The skill shows how to set `VITE_API_BASE_URL` at build time to point to the production Functions URL while defaulting to `/api` (Vite proxy) for local dev.

### `swa deploy` defaults to preview

Without `--env production`, `swa deploy` creates a preview environment at a different URL. Your main URL stays on the old build. Always pass `--env production` for real releases.

### Vite dev proxy is your friend

Setting `server.proxy['/api']` in `vite.config.ts` to `http://localhost:7071` makes local development work with zero CORS config. The `authHeaders()` pattern in the skill handles auth tokens consistently across local and prod.

## Simple password gate

The skill includes a complete password-gate pattern for demo/admin tools where you need "keep randos out" but don't need full user accounts:

- Backend: `AuthApi` function that checks against `ADMIN_PASSWORD` app setting
- Frontend: `sessionStorage` token + route guard + auto-redirect on 401

Session-only — closing the tab logs you out. Good for demos, not for multi-user production apps.

## See also

- Companion skill: [`azure-functions-mcp`](../azure-functions-mcp) — add MCP tool endpoints to the same Functions app to expose tools to Claude Desktop / Copilot
- [Azure Static Web Apps docs](https://learn.microsoft.com/en-us/azure/static-web-apps/)
