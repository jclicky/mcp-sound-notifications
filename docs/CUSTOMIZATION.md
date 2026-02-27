# Customization Guide

How to make the sound system your own.

## Persona Differentiation

The core value proposition: **each AI agent gets distinct sounds so you can tell them apart by ear.** When Cursor completes a task it sounds different from Claude Code or Gemini CLI.

### Setting Up Personas

Edit `~/.config/sound-notifications/config/sound-config.yaml` (source: [config/sound-config.yaml](../config/sound-config.yaml)):

```yaml
personas:
  cursor-agent:
    name: "Cursor"
    categories:
      completion:
        pool: ["cursor-done-1", "cursor-done-2"]
        rotation: sequential
      acknowledgment:
        pool: ["cursor-ack"]

  claude-code:
    name: "Claude"
    categories:
      completion:
        pool: ["claude-done-1", "claude-done-2"]
        rotation: sequential
```

Place `cursor-done-1.mp3`, `cursor-done-2.mp3`, `claude-done-1.mp3`, etc. in [config/themes/default/](../config/themes/default/).

### Rotation Strategies

- **sequential**: Cycles through sounds in order (A → B → C → A → ...)
- **random**: Random selection, avoiding the last-played sound

## Creating a Theme

Themes organize sound packs. Copy an example and customize:

```bash
cp -r config/themes/example-warcraft config/themes/my-theme
```

Edit [theme.yaml](../config/themes/example-warcraft/theme.yaml) in your theme directory:

```yaml
theme:
  name: "My Custom Theme"
  description: "Sounds I like"

personas:
  agent-a:
    categories:
      completion:
        pool: ["my-chime", "my-ding"]
      warning:
        pool: ["my-alert"]
```

## Anti-Fatigue Tuning

Prevent notification overload:

```yaml
settings:
  sound_cooldown_ms: 500       # Min ms between same sound (double-tap prevention)
  max_sounds_per_minute: 6     # Hard rate limit
  fallback_to_notifications: true  # Show OS notification when rate-limited
  easter_egg_probability: 0.05 # 5% chance of fun sounds
```

## Volume Control

```yaml
settings:
  volume: 0.7  # 0.0 (silent) to 1.0 (full volume)
```

## Disabling Categories

```yaml
categories:
  easter_egg:
    enabled: false  # No fun allowed
  greeting:
    enabled: false  # Skip session-start sounds
```

## User-Level Config Override

The server checks these locations in order:

1. `$XDG_CONFIG_HOME/sound-notifications/sound-config.yaml` (user override)
2. `<install-dir>/config/sound-config.yaml` (package default: [config/sound-config.yaml](../config/sound-config.yaml))
3. Built-in defaults (system sound fallbacks)

To override without modifying the package:

```bash
mkdir -p ~/.config/sound-notifications
cp config/sound-config.yaml ~/.config/sound-notifications/
# Edit ~/.config/sound-notifications/sound-config.yaml
```

See [config/sound-config.yaml](../config/sound-config.yaml) for the source file.
