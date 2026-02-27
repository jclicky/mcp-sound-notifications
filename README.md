# MCP Sound Notifications

**Audio feedback for AI agent workflows.** An MCP server that lets AI agents play distinct sounds at workflow boundaries -- task completion, errors, waiting for input, git operations, and more.

## Why?

When you have multiple AI agents working (Cursor, Claude Code, Gemini CLI, Windsurf), you lose track of which agent did what. Sound solves this:

- **Persona differentiation**: Each agent gets its own sound palette. You learn to recognize "that was Cursor" vs. "that was Claude" by ear alone.
- **Workflow awareness**: A completion chime means you can look away from the screen. A warning buzz means something needs attention.
- **Anti-fatigue**: Built-in rate limiting, cooldowns, and rotation prevent notification overload.

## Quick Start

```bash
# Clone
git clone <your-repo-url>/mcp-sound-notifications.git
cd mcp-sound-notifications

# Install for your IDE(s)
./scripts/install.sh --ide cursor          # Cursor only
./scripts/install.sh --ide claude          # Claude Code only
./scripts/install.sh --ide all             # All IDEs

# Restart your IDE -- the play_sound tool is now available
```

**No sound files needed.** The server falls back to your OS's built-in sounds (macOS: Glass, Pop, Ping, Basso; Linux: freedesktop sound theme).

Want custom sounds? See [SOUND-SOURCES.md](docs/SOUND-SOURCES.md).

## How It Works

```
AI Agent  →  play_sound(event="task_completed")  →  MCP Server  →  afplay/paplay  →  🔊
                                                         ↓
                                                  Anti-fatigue check
                                                  Persona routing
                                                  Sound rotation
                                                  OS notification
```

The server is a standard [MCP](https://modelcontextprotocol.io) server that exposes two tools:

| Tool | Description |
|------|-------------|
| `play_sound` | Play audio with event/category/persona routing |
| `show_notification` | OS notification without sound |

## Events

The server maps events to sound categories automatically:

| Event | Category | When |
|-------|----------|------|
| `task_completed` | completion | Agent finished work |
| `git_push_success` | completion | Pushed to remote |
| `task_acknowledged` | acknowledgment | Agent started work |
| `git_commit_success` | acknowledgment | Committed changes |
| `waiting_for_input` | attention | Agent needs user decision |
| `task_failed` | warning | Something broke |
| `unsafe_action_blocked` | refusal | Security check blocked action |
| `session_start` | greeting | New session began |

[Full event list →](mcp-server/sound_server.py)

## Persona System

Each agent gets distinct sounds so you can identify them by ear:

```yaml
# In sound-config.yaml
personas:
  cursor-agent:
    categories:
      completion:
        pool: ["chime-bright", "chime-warm"]
        rotation: sequential
  claude-code:
    categories:
      completion:
        pool: ["bell-deep", "bell-soft"]
        rotation: sequential
```

Different agents → different sounds → instant recognition.

## Configuration

Default config lives at `~/.config/sound-notifications/config/sound-config.yaml` (source: [config/sound-config.yaml](config/sound-config.yaml)):

```yaml
settings:
  enabled: true
  volume: 0.7
  sound_cooldown_ms: 500        # Prevent double-triggers
  max_sounds_per_minute: 6      # Anti-fatigue
  fallback_to_notifications: true
```

See [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for full guide.

## Theme System

Create custom sound packs organized as themes:

```
config/themes/my-theme/
  theme.yaml          # Persona mappings
  completion-1.mp3    # Your sounds
  warning-alert.wav
```

Example themes included (templates only -- bring your own sounds):
- [example-warcraft/](config/themes/example-warcraft/) -- Warcraft III unit personas
- [example-star-trek/](config/themes/example-star-trek/) -- TNG bridge crew personas

## IDE Support

| IDE | Config Location | Status |
|-----|----------------|--------|
| Cursor | `~/.cursor/mcp.json` | ✅ Full support |
| Claude Code | `~/.claude/mcp.json` | ✅ Full support |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | ✅ Full support |
| VS Code (Copilot) | VS Code settings | ✅ Via MCP extension |

See [IDE-SETUP.md](docs/IDE-SETUP.md) for detailed instructions.

## Requirements

- **Python 3.9+** (no additional packages required; PyYAML optional for config)
- **macOS**: `afplay` (built-in)
- **Linux**: `paplay`, `aplay`, or `mpg123` (one of these)
- **Windows**: PowerShell (built-in)

## Finding Sounds

No sounds included (to keep the package license-clean). Options:

1. **System sounds**: Already there, zero effort. Run [find-system-sounds.sh](scripts/find-system-sounds.sh)
2. **freesound.org**: CC0-licensed. Use the [fetch-freesounds.py](scripts/fetch-freesounds.py) script
3. **Record your own**: See [SOUND-SOURCES.md](docs/SOUND-SOURCES.md)

## Architecture

| Path | Description |
|------|-------------|
| [`mcp-server/sound_server.py`](mcp-server/sound_server.py) | MCP server (plays sounds, handles events) |
| [`config/sound-config.yaml`](config/sound-config.yaml) | Default configuration |
| [`config/themes/`](config/themes/) | Sound theme packs |
| [`scripts/install.sh`](scripts/install.sh) | Multi-IDE installer |
| [`scripts/find-system-sounds.sh`](scripts/find-system-sounds.sh) | Discover OS sounds |
| [`scripts/fetch-freesounds.py`](scripts/fetch-freesounds.py) | Download CC0 sounds |
| [`examples/`](examples/) | IDE config examples |
| [`docs/`](docs/) | Guides ([IDE Setup](docs/IDE-SETUP.md), [Customization](docs/CUSTOMIZATION.md), [Sound Sources](docs/SOUND-SOURCES.md), [Contributing](docs/CONTRIBUTING.md)) |

## License

MIT. See [LICENSE](LICENSE).
