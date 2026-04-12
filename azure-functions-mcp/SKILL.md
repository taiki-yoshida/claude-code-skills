---
name: azure-functions-mcp
description: Scaffold and deploy remote MCP servers on Azure Functions using Microsoft.Azure.Functions.Worker.Extensions.Mcp (.NET isolated worker). Use when user wants to build an MCP server hosted on Azure Functions, mentions azure-functions-mcp-extension, wants to expose tools to Claude/Copilot via Azure backend, or needs to scaffold a remote MCP server with Azure.
---

# Azure Functions MCP Server

Build a remote MCP (Model Context Protocol) server using the Azure Functions MCP extension. This skill captures battle-tested patterns and gotchas from a production build.

## When to use

- User wants to expose custom tools to Claude Desktop, Copilot, or other MCP clients via a cloud-hosted backend
- User specifically mentions Azure Functions + MCP, or the `azure-functions-mcp-extension` repo
- User needs a serverless MCP server (as opposed to running one locally)

## Prerequisites

- .NET SDK (10 LTS or 8 LTS both work — this skill uses .NET 10)
- Azure Functions Core Tools v4 (`func --version` should be ≥ 4.0.7030)
- Azurite storage emulator for local dev: `npm install -g azurite`
- An Azure Functions app (Flex Consumption plan recommended for MCP workloads)

## Project scaffold

```bash
dotnet new worker --name MyMcpFunctions --output functions --framework net10.0
cd functions
```

**Critical**: Replace the generated `.csproj` — the `worker` template uses `Microsoft.NET.Sdk.Worker` which is NOT compatible with Azure Functions. Overwrite with:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <AzureFunctionsVersion>v4</AzureFunctionsVersion>
    <OutputType>Exe</OutputType>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.Azure.Functions.Worker" Version="2.51.0" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Sdk" Version="2.0.7" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore" Version="2.1.0" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.Mcp" Version="1.5.0-preview.1" />
    <PackageReference Include="Microsoft.Extensions.Azure" Version="1.13.1" />
  </ItemGroup>
  <ItemGroup>
    <None Update="host.json"><CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory></None>
    <None Update="local.settings.json">
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
      <CopyToPublishDirectory>Never</CopyToPublishDirectory>
    </None>
  </ItemGroup>
</Project>
```

Delete the auto-generated `Worker.cs`, `appsettings.json`, `appsettings.Development.json`, and `Properties/` — they are for the worker template, not Functions.

## host.json

```json
{
  "version": "2.0",
  "extensions": {
    "mcp": {
      "instructions": "Describe what this MCP server does",
      "serverName": "MyMcpServer",
      "serverVersion": "1.0.0",
      "system": {
        "webhookAuthorizationLevel": "Anonymous"
      }
    }
  },
  "logging": {
    "applicationInsights": {
      "samplingSettings": { "isEnabled": true, "excludedTypes": "Request" }
    }
  }
}
```

`webhookAuthorizationLevel: "Anonymous"` lets MCP clients connect without a function key. For production with auth, remove it and use Microsoft Entra via App Service authentication.

## local.settings.json

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

## Program.cs

```csharp
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = FunctionsApplication.CreateBuilder(args);
builder.ConfigureFunctionsWebApplication();

// Register your services here
// builder.Services.AddSingleton<MyService>();

builder.Build().Run();
```

## MCP tool trigger pattern

```csharp
using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Extensions.Mcp;

public class MyTool
{
    [Function("MyToolName")]
    public async Task<string> MyToolHandler(
        [McpToolTrigger("my_tool", "Description shown to MCP clients")]
        ToolInvocationContext context,
        [McpToolProperty("param1", "Description of param1", isRequired: true)]
        string param1,
        [McpToolProperty("param2", "Optional param", isRequired: false)]
        string? param2)
    {
        // Return JSON string (becomes TextContentBlock in MCP response)
        return JsonSerializer.Serialize(new { result = "..." });
    }
}
```

## Critical gotchas (LEARN FROM PAIN)

### 1. `McpToolPropertyAttribute` signature

**DO NOT USE** this signature (it fails with CS1739 "does not have a parameter named 'required'"):
```csharp
[McpToolProperty("name", "string", "description", required: true)]  // WRONG
```

**Actual constructor**: `(string propertyName, string description, bool isRequired)`

```csharp
[McpToolProperty("name", "description", isRequired: true)]  // CORRECT
```

There is NO `propertyType` parameter. The type is inferred from the C# parameter type.

### 2. Function names must be globally unique

If you have both HTTP triggers AND MCP tool triggers with overlapping function names (e.g., REST `GetRecord` and MCP `GetRecord`), deployment succeeds but the host fails with:

```
System.Linq: Sequence contains more than one matching element.
```

**Fix**: Prefix all MCP tool function names with `Mcp*`:

```csharp
[Function("McpGetRecord")]  // not nameof(GetRecord)
public async Task<string> GetRecord(...) { }
```

The MCP tool *name* exposed to clients (the `McpToolTrigger` string) can stay as `"get_record"` — only the C# `[Function(...)]` name needs to be unique.

### 3. Flex Consumption runtime config

On Flex Consumption, setting `FUNCTIONS_WORKER_RUNTIME` as an app setting FAILS:

```
ERROR: The following app setting (Site.SiteConfig.AppSettings.FUNCTIONS_WORKER_RUNTIME)
for Flex Consumption sites is invalid. Please remove or rename it before retrying.
```

The runtime is instead part of `functionAppConfig.runtime` in the site config. Check with:

```bash
az functionapp show --name <app> --resource-group <rg> \
  --query "properties.functionAppConfig.runtime" -o json
```

If the function app was created correctly (Flex Consumption + dotnet-isolated + .NET 10), this is already set. You don't need to touch it.

### 4. Do not confuse MCP tool triggers with table/blob bindings

MCP tool triggers CANNOT use input/output bindings (e.g., `[TableInput]`, `[BlobInput]`). Inject `TableServiceClient` / `BlobServiceClient` via DI using `AddAzureClients` from `Microsoft.Extensions.Azure` and call the SDKs directly.

## Local dev workflow

```bash
# Terminal 1: storage emulator
azurite --silent --location .azurite

# Terminal 2: functions
cd functions && func start
# MCP endpoint: http://localhost:7071/runtime/webhooks/mcp
```

## Deployment

```bash
# From the functions/ directory
func azure functionapp publish <function-app-name> --dotnet-isolated
```

Expected output ends with a list of deployed functions. **Verify the host started**:

```bash
az functionapp function list --name <app> --resource-group <rg> --query "[].name" -o tsv
```

If empty, check the host status endpoint:

```bash
curl https://<app>.azurewebsites.net/admin/host/status
```

If `state: "Error"` with the sequence error — you have duplicate function names. Fix and redeploy.

## MCP client connection

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` or equivalent):

```json
{
  "mcpServers": {
    "my-mcp": {
      "url": "https://<app>.azurewebsites.net/runtime/webhooks/mcp"
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "my-mcp": {
      "type": "http",
      "url": "https://<app>.azurewebsites.net/runtime/webhooks/mcp"
    }
  }
}
```

## Endpoint paths

- `/runtime/webhooks/mcp` — Streamable HTTP (preferred, modern)
- `/runtime/webhooks/mcp/sse` — Server-Sent Events (legacy, backward compat)

## When to pair with other skills

If the user also wants a frontend to manage the data behind their MCP tools, pair this skill with `azure-swa-functions-stack` — you can deploy the React admin UI to Static Web Apps while keeping the Functions app serving both MCP and REST API endpoints.
