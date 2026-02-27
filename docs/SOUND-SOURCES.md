# Sound Sources

Where to find sounds for your MCP Sound Notifications setup.

## System Sounds (Zero Effort)

The server automatically falls back to system sounds when no custom sounds are configured.

### macOS

Built-in sounds at `/System/Library/Sounds/`:

| Sound | Good For |
|-------|----------|
| Glass | Completion |
| Pop | Acknowledgment |
| Ping | Attention |
| Basso | Warning |
| Funk | Refusal |
| Hero | Greeting |
| Frog | Easter egg |
| Tink, Blow, Bottle, Morse, Purr, Sosumi, Submarine | Variety |

Run [`find-system-sounds.sh`](../scripts/find-system-sounds.sh) to discover all available sounds.

### Linux

FreeDesktop sounds at `/usr/share/sounds/freedesktop/stereo/`:

```bash
sudo apt install sound-theme-freedesktop  # Debian/Ubuntu
sudo dnf install sound-theme-freedesktop  # Fedora
```

| Sound | Good For |
|-------|----------|
| complete | Completion |
| message | Acknowledgment |
| bell | Attention |
| dialog-warning | Warning |
| dialog-error | Refusal |
| service-login | Greeting |

## Free Sound Libraries

### freesound.org (CC0 / Public Domain)

The best source for free, high-quality notification sounds.

1. Create account at https://freesound.org
2. Get API key at https://freesound.org/apiv2/apply/
3. Use the included helper script:

```bash
export FREESOUND_API_KEY="your-key"
python scripts/fetch-freesounds.py                    # Download default set
python scripts/fetch-freesounds.py --query "chime"    # Custom search
python scripts/fetch-freesounds.py --list-only        # Preview first
```

### Recommended Search Queries

| Category | Search Terms |
|----------|-------------|
| Completion | "notification chime", "success ding", "task complete" |
| Acknowledgment | "UI click", "confirm beep", "accept" |
| Attention | "alert bell", "notification ping" |
| Warning | "warning beep", "error alert" |
| Greeting | "startup chime", "welcome" |

### Other Free Sources

- **Mixkit** (https://mixkit.co/free-sound-effects/) -- Free for personal and commercial use
- **Pixabay Audio** (https://pixabay.com/sound-effects/) -- Royalty-free
- **Zapsplat** (https://www.zapsplat.com/) -- Free with attribution (or paid for no-attribution)
- **Soundsnap** (https://www.soundsnap.com/) -- Subscription-based, high quality

## Recording Your Own

### macOS (QuickTime)

1. Open QuickTime Player > File > New Audio Recording
2. Record your sound
3. Export as M4A, then convert: `afconvert input.m4a output.mp3 -d mp3`

### Command Line (sox)

```bash
brew install sox  # macOS
sudo apt install sox  # Linux

# Generate a simple chime
sox -n completion.mp3 synth 0.3 sine 880 fade 0 0.3 0.1
sox -n warning.mp3 synth 0.5 sine 440 fade 0 0.5 0.2
sox -n attention.mp3 synth 0.2 sine 1200 synth 0.2 sine 800
```

## Theme Packs

The server supports theme directories. See [example-warcraft/](../config/themes/example-warcraft/) and [example-star-trek/](../config/themes/example-star-trek/) for the schema. Create your own:

```
config/themes/my-theme/
  theme.yaml          # Persona and category mappings
  completion-1.mp3
  completion-2.mp3
  ack-1.mp3
  warning-1.mp3
```
