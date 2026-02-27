#!/bin/bash
# =============================================================================
# Find System Sounds - Discover built-in sounds on your OS
# =============================================================================
# Run this to see what sounds are available on your system without
# needing to download any external sound packs.
#
# Usage:
#   ./find-system-sounds.sh          # List all system sounds
#   ./find-system-sounds.sh --play   # List and play each sound

set -euo pipefail

PLAY_MODE="${1:-}"

echo "🔍 Searching for system sounds..."
echo ""

FOUND=0

# macOS sounds
if [[ "$(uname)" == "Darwin" ]]; then
    echo "=== macOS System Sounds ==="
    echo "Location: /System/Library/Sounds/"
    echo ""
    
    if [[ -d "/System/Library/Sounds" ]]; then
        for f in /System/Library/Sounds/*; do
            name=$(basename "$f" | sed 's/\.[^.]*$//')
            echo "  ✓ $name  ($f)"
            FOUND=$((FOUND + 1))
            if [[ "$PLAY_MODE" == "--play" ]]; then
                echo "    ▶ Playing..."
                afplay "$f" &
                sleep 1.5
                kill %1 2>/dev/null || true
            fi
        done
    fi
    
    echo ""
    echo "=== macOS Alert Tones ==="
    TONES_DIR="/System/Library/PrivateFrameworks/ToneLibrary.framework/Versions/A/Resources/AlertTones"
    if [[ -d "$TONES_DIR" ]]; then
        find "$TONES_DIR" -name "*.caf" -o -name "*.m4r" | head -20 | while read -r f; do
            name=$(basename "$f" | sed 's/\.[^.]*$//')
            echo "  ✓ $name  ($f)"
            FOUND=$((FOUND + 1))
        done
        echo "  ... (run 'find $TONES_DIR' for full list)"
    fi

# Linux sounds
elif [[ "$(uname)" == "Linux" ]]; then
    echo "=== FreeDesktop Sounds ==="
    FD_DIR="/usr/share/sounds/freedesktop/stereo"
    if [[ -d "$FD_DIR" ]]; then
        for f in "$FD_DIR"/*; do
            name=$(basename "$f" | sed 's/\.[^.]*$//')
            echo "  ✓ $name  ($f)"
            FOUND=$((FOUND + 1))
            if [[ "$PLAY_MODE" == "--play" ]]; then
                echo "    ▶ Playing..."
                paplay "$f" 2>/dev/null || aplay "$f" 2>/dev/null || true
                sleep 1
            fi
        done
    else
        echo "  FreeDesktop sounds not found. Install with:"
        echo "    sudo apt install sound-theme-freedesktop"
    fi
    
    echo ""
    echo "=== Other Sound Locations ==="
    for dir in /usr/share/sounds /usr/local/share/sounds; do
        if [[ -d "$dir" ]]; then
            count=$(find "$dir" -type f \( -name "*.wav" -o -name "*.ogg" -o -name "*.oga" \) | wc -l)
            echo "  $dir: $count sound files found"
        fi
    done
fi

echo ""
echo "Found $FOUND system sounds."
echo ""
echo "To use system sounds with MCP Sound Notifications:"
echo "  1. Note the sound name (without extension)"
echo "  2. The server will automatically check system directories as a fallback"
echo "  3. Or copy sounds to config/themes/default/ for explicit control"
