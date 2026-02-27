# Default Sound Theme

Place your sound files here. Supported formats: `.mp3`, `.wav`, `.ogg`, `.aiff`, `.m4a`.

## Getting Started

If you don't add any sounds, the server will automatically fall back to your system's built-in sounds:

- **macOS**: `/System/Library/Sounds/` (Glass, Pop, Ping, Basso, Funk, Hero, Frog)
- **Linux**: `/usr/share/sounds/freedesktop/stereo/` (bell, complete, dialog-warning, etc.)

## Adding Custom Sounds

1. Place sound files in this directory
2. Reference them by filename (without extension) in `config/sound-config.yaml`
3. Restart the MCP server

## Naming Convention

Use descriptive names with category prefixes for organization:

```
completion-chime.mp3
completion-success.mp3
ack-click.mp3
ack-blip.mp3
attention-bell.mp3
warning-alert.mp3
```

See `docs/SOUND-SOURCES.md` for where to find open-source sound packs.
