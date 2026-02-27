# IDE Setup Guide

Detailed setup instructions for each supported IDE.

## Quick Install (All IDEs)

```bash
git clone <your-repo-url>/mcp-sound-notifications.git
cd mcp-sound-notifications
./scripts/install.sh --ide all
```

## Cursor IDE

### Automatic

```bash
./scripts/install.sh --ide cursor
```

### Manual

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "sound-notifications": {
      "command": "python3",
      "args": [
        "~/.config/sound-notifications/mcp-server/sound_server.py",
        "--agent", "cursor-agent"
      ]
    }
  }
}
```

Restart Cursor. The `play_sound` and `show_notification` tools will appear in the MCP tool list.

### Usage in Cursor Rules

Add to `.cursor/rules/audio-notifications.mdc`:

```markdown
# Audio Notification Protocol

Play audio cues at workflow boundaries.

## When to Play

| Condition | Action |
|-----------|--------|
| Task completed | `play_sound(event="task_completed")` |
| Git push | `play_sound(event="git_push_success")` |
| Need input | `play_sound(event="waiting_for_input")` |
| Error | `play_sound(event="task_failed")` |
```

## Claude Code

### Automatic

```bash
./scripts/install.sh --ide claude
```

### Manual

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "sound-notifications": {
      "command": "python3",
      "args": [
        "~/.config/sound-notifications/mcp-server/sound_server.py",
        "--agent", "claude-code"
      ]
    }
  }
}
```

## Windsurf IDE

### Automatic

```bash
./scripts/install.sh --ide windsurf
```

### Manual

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "sound-notifications": {
      "command": "python3",
      "args": [
        "~/.config/sound-notifications/mcp-server/sound_server.py",
        "--agent", "windsurf-agent"
      ]
    }
  }
}
```

## VS Code (Copilot Chat)

VS Code supports MCP servers via Copilot Chat. Add to your VS Code settings:

```json
{
  "github.copilot.chat.mcpServers": {
    "sound-notifications": {
      "command": "python3",
      "args": [
        "~/.config/sound-notifications/mcp-server/sound_server.py",
        "--agent", "vscode-agent"
      ]
    }
  }
}
```

## Verifying Installation

After restarting your IDE:

1. Ask the AI agent: "Play a completion sound"
2. The agent should call `play_sound(event="task_completed")`
3. You should hear a sound (or see a system notification if no sounds are configured)

## Troubleshooting

### No sound plays

1. Check that Python 3 is available: `python3 --version`
2. Check sound files exist: `ls ~/.config/sound-notifications/config/themes/default/`
3. If empty, the server falls back to system sounds -- verify they work: `afplay /System/Library/Sounds/Glass.aiff` (macOS)
4. Check MCP server logs in your IDE's output panel

### MCP server not recognized

1. Verify the config file path matches your IDE
2. Restart the IDE completely (not just reload)
3. Check that the path to `sound_server.py` is absolute (use `~/.config/...` not relative paths)
