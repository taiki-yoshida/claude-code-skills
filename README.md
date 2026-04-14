# Claude Code Skills

A personal collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) distilled from real projects. Each skill captures battle-tested patterns and gotchas so that Claude (and you) don't hit the same walls twice.

Skills live in their own subdirectories. Browse each folder for its dedicated README and the `SKILL.md` file that Claude Code loads.

## Available skills

| Skill | Category | Description |
|-------|----------|-------------|
| [`azure-functions-mcp`](./azure-functions-mcp) | Azure · MCP | Scaffold and deploy remote MCP servers on Azure Functions (.NET isolated worker + `azure-functions-mcp-extension`). |
| [`azure-openai`](./azure-openai) | Azure · AI | Integrate Azure OpenAI services including GPT Realtime API (gpt-realtime-1.5) for real-time audio conversations via WebRTC. |
| [`azure-swa-functions-stack`](./azure-swa-functions-stack) | Azure · Full-stack | Scaffold and deploy React + Vite on Azure Static Web Apps paired with a standalone Azure Functions backend. |

More skills will be added over time as I extract patterns from new projects.

## What's a Claude Code skill?

A skill is a directory containing a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-name
description: When to trigger this skill and what it does
---

# Skill contents...
```

Claude Code loads skill metadata on startup. When your prompt matches a skill's trigger description, Claude invokes the skill and reads its full content. Skills can also include reference files, templates, and scripts alongside `SKILL.md`.

See the [official skills documentation](https://docs.claude.com/en/docs/claude-code/skills) for the full spec.

## Installation

### Option 1: Clone and symlink (recommended for active use)

```bash
git clone https://github.com/<your-username>/claude-code-skills.git
cd claude-code-skills

# Symlink individual skills into your Claude Code skills directory
ln -s "$(pwd)/azure-functions-mcp" ~/.claude/skills/azure-functions-mcp
ln -s "$(pwd)/azure-swa-functions-stack" ~/.claude/skills/azure-swa-functions-stack
```

Symlinks mean you can `git pull` in this repo and your installed skills update automatically.

### Option 2: Copy individual skills

```bash
git clone https://github.com/<your-username>/claude-code-skills.git /tmp/ccs
cp -r /tmp/ccs/azure-functions-mcp ~/.claude/skills/
cp -r /tmp/ccs/azure-swa-functions-stack ~/.claude/skills/
```

### Option 3: Clone the whole repo into your skills directory

```bash
cd ~/.claude/skills
git clone https://github.com/<your-username>/claude-code-skills.git
```

Claude Code discovers `SKILL.md` files anywhere under `~/.claude/skills/`, so nesting works fine.

## Verifying installation

Start a new Claude Code session and run `/skills` (or check the system prompt). Installed skills should appear in the list:

```
- azure-functions-mcp: Scaffold and deploy remote MCP servers on Azure Functions...
- azure-swa-functions-stack: Scaffold and deploy a React+Vite frontend on Azure Static Web Apps...
```

## How I write these skills

Every skill in this repo follows the same philosophy:

1. **Capture the gotchas.** Anyone can read official docs. Skills are most valuable when they document the errors you hit, the misleading examples, and the undocumented constraints.
2. **Show, don't summarize.** Include real code templates and commands that Claude can copy-paste, not vague prose.
3. **Describe the trigger precisely.** The `description` frontmatter is how Claude decides when to load the skill — be specific about the keywords and intents that should invoke it.
4. **Cross-link related skills.** Skills that work well together should mention each other so Claude can pair them when appropriate.

## Contributing

This is a personal collection, but PRs that fix bugs or add gotchas to existing skills are welcome. For new skills, feel free to fork.

## License

MIT — see [LICENSE](./LICENSE).
