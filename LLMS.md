# Brain CLI — Installation

Install and wire the Brain CLI reasoning engine into Hermes Agent.

## 1. Install brain

```bash
cd /path/to/brain-cli
uv tool install --editable .
```

Verify:
```bash
brain --version    # → brain 0.3.0
brain think "2+2" --depth quick
```

## 2. API keys

Brain reads keys from `~/.hermes/profiles/goose/.env`:

```env
OPENROUTER_API_KEY=sk-or-...
OPENCODE_GO_API_KEY=sk-pw...
```

Or set provider-specific env vars. `brain key` shows the active key.

Pick a provider:
```bash
brain config-set provider opencode_go
brain config-set provider openrouter
```

## 3. Install Hermes plugin

```bash
cp -r plugin/brain-tool ~/.hermes/plugins/brain-tool/
```

Enable in `~/.hermes/config.yaml`:
```yaml
plugins:
  enabled:
    - brain-tool
```

## 4. Restart Hermes

```bash
hermes restart
hermes plugins list    # should show brain-tool
```

## 5. Verify

Send to Hermes:
```
brain_think "fix the bug in foo.py"
```

Agent should:
1. Call `brain_think` → reasoning engine creates a plan
2. `pre_tool_call` gate allows action tools (edit/bash) now that plan exists
3. Agent calls `brain_plan_done` after each completed step

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `brain: command not found` | `uv tool install --editable .` |
| `No key found` | Set API key in `~/.hermes/profiles/goose/.env` |
| Plugin not in `hermes plugins list` | Check `plugin.yaml` syntax, restart Hermes |
| Gate blocks all tools | No plan → agent must call `brain_think` first |
| Plan expired mid-session | TTL reset on `brain_plan_done`/`brain_plan_block` |
