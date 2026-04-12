# azure-functions-mcp

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) for scaffolding and deploying remote MCP (Model Context Protocol) servers on Azure Functions using the `Microsoft.Azure.Functions.Worker.Extensions.Mcp` package.

## What it does

When your prompt mentions building an MCP server on Azure Functions (or similar phrases), Claude automatically loads this skill and applies the patterns inside. The skill covers:

- Project scaffolding (.NET 10 isolated worker)
- Correct NuGet package versions
- `host.json` configuration for the MCP extension
- MCP tool trigger + property attribute patterns
- Local development with Azurite
- Deployment to Flex Consumption plan

## Installation

```bash
# Install to your Claude Code skills directory
cp -r azure-functions-mcp ~/.claude/skills/
```

Or see the [parent README](../README.md) for other installation options.

## Triggers

Claude will load this skill when you say things like:

- "Build an MCP server on Azure Functions"
- "How do I use the azure-functions-mcp-extension?"
- "Create an MCP tool that reads from Azure Storage"
- "Deploy an MCP server to Flex Consumption"

## Key gotchas (why this skill exists)

The skill captures several painful lessons from real builds:

### `McpToolPropertyAttribute` signature

Many examples online show `[McpToolProperty("name", "type", "description", required: true)]`. **This fails to compile** with CS1739. The actual constructor is `(string propertyName, string description, bool isRequired)` — no `propertyType` parameter. Type is inferred from the C# parameter.

### Unique function names

Azure Functions requires function names to be globally unique. If you have a REST API function `GetRecord` AND an MCP tool function `GetRecord`, deployment succeeds but the host fails with:

```
System.Linq: Sequence contains more than one matching element.
```

Prefix MCP tool `[Function(...)]` names with `Mcp*` to avoid collisions. The MCP tool name exposed to clients can stay the same.

### Flex Consumption runtime config

Setting `FUNCTIONS_WORKER_RUNTIME` as an app setting fails on Flex Consumption:

```
ERROR: The following app setting (Site.SiteConfig.AppSettings.FUNCTIONS_WORKER_RUNTIME)
for Flex Consumption sites is invalid.
```

The runtime lives in `functionAppConfig.runtime` in the site config instead.

### Worker template conversion

`dotnet new worker` creates a project using `Microsoft.NET.Sdk.Worker` which is NOT compatible with Azure Functions. The skill shows exactly how to rewrite the `.csproj` to use `Microsoft.NET.Sdk` with `OutputType=Exe`.

## See also

- [Azure Functions MCP extension repo](https://github.com/Azure/azure-functions-mcp-extension)
- Companion skill: [`azure-swa-functions-stack`](../azure-swa-functions-stack) — pairs this backend with a React frontend on Static Web Apps
