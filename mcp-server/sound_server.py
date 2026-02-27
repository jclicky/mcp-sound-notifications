#!/usr/bin/env python3
"""
MCP Sound Server - Universal Audio Notifications for AI Agent Workflows
========================================================================
ADR: [T-ADR-017] - Universal Sound Notification Architecture
ADR: [T-ADR-011a] - Multi-Agent Audio Persona System

This MCP server exposes a `play_sound` tool that agents can call to play
audio notifications without requiring shell command authorization.

Features:
- Plays sounds via native OS commands (afplay on macOS)
- Shows OS notifications with context
- Implements anti-fatigue mechanisms (cooldowns, rotation)
- Supports agent-specific personas (Peasant, Rifleman, Peon)
- Reads configuration from sound-config.yaml

Supported IDEs:
- Cursor IDE (~/.cursor/mcp.json)
- Claude Code (~/.claude/mcp.json)
- Windsurf (~/.codeium/windsurf/mcp_config.json)

Agent Personas (T-ADR-011a):
- cursor-agent  → Human Peasant (WC3) → peasant-* sounds
- claude-code   → Scottish Rifleman (WC3) → rifleman-* sounds
- gemini-cli    → Orc Peon (WC3) → peon-* sounds

Usage:
    python sound_server.py --agent cursor-agent   # Cursor IDE (peasant)
    python sound_server.py --agent claude-code    # Claude Code (rifleman)
    python sound_server.py --agent gemini-cli     # Gemini CLI (peon)

MCP Configuration (T-ADR-017a: auto-populate agent):

Cursor IDE (~/.cursor/mcp.json):
    {
        "mcpServers": {
            "sound-notifications": {
                "command": "python3",
                "args": ["/path/to/sound_server.py", "--agent", "cursor-agent"]
            }
        }
    }

Claude Code (~/.claude/mcp.json):
    {
        "mcpServers": {
            "sound-notifications": {
                "command": "python3",
                "args": ["/path/to/sound_server.py", "--agent", "claude-code"]
            }
        }
    }
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# =============================================================================
# Command-Line Arguments (T-ADR-017a: Auto-populate agent from IDE config)
# =============================================================================
# This allows each IDE to configure its agent identity in mcp.json:
#   Cursor:  --agent cursor-agent  (peasant sounds)
#   Claude:  --agent claude-code   (rifleman sounds)
#   Gemini:  --agent gemini-cli    (peon sounds)

_parser = argparse.ArgumentParser(
    description="MCP Sound Server with Agent Persona Support (T-ADR-017a)"
)
_parser.add_argument(
    "--agent",
    default="cursor-agent",
    choices=["cursor-agent", "claude-code", "gemini-cli"],
    help="Agent identity for persona sound selection (default: cursor-agent)"
)
_args, _ = _parser.parse_known_args()  # parse_known_args to ignore MCP-specific args
DEFAULT_AGENT = _args.agent  # Set from command-line, used as fallback in play_sound()

# Try to import YAML parser
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not installed. Using default configuration.", file=sys.stderr)

# =============================================================================
# Configuration
# =============================================================================

# Resolve paths relative to this script
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = SCRIPT_DIR.parent
SOUNDS_DIR = CONFIG_DIR / "sounds"
CONFIG_FILE = CONFIG_DIR / "sound-config.yaml"

# State tracking for anti-fatigue
_last_played: dict[str, float] = {}  # sound_name -> timestamp
_last_category_sound: dict[str, str] = {}  # category -> last sound played
_sounds_this_minute: list[float] = []  # timestamps of recent sounds
_hook_sounds_this_minute: list[float] = []  # timestamps for hook event throttle tier

# Default configuration (used if YAML not available or file not found)
# Sound files use agent prefixes: peasant-, peon-, rifleman-
DEFAULT_CONFIG = {
    "settings": {
        "enabled": True,
        "volume": 0.7,
        "sound_cooldown_ms": 2000,
        "max_sounds_per_minute": 6,
        "fallback_to_notifications": True,
        "easter_egg_probability": 0.05,
        "os_notifications": {
            "enabled": True,
            "style": "banner"
        }
    },
    "categories": {
        "completion": {
            # Large pool with STFC fallbacks for variety - sequential rotation cycles through all
            "pool": [
                "peasant-job-done", "peasant-jobs-done-exact", "peasant-off-i-go",
                "STNG-picard-make-it-so", "STFC-acknowledged", 
                "STFC-cochrane-thanks", "STFC-crew-aye-sir"
            ],
            "rotation": "sequential",
            "os_notification": True,
            "intensity": "low",
            "enabled": True
        },
        "acknowledgment": {
            # Expanded pool for variety
            "pool": [
                "peasant-yes-me-lord", "peasant-ready-to-work", "peasant-ready-to-serve",
                "STFC-acknowledged", "STFC-crew-aye-sir",
                "STFC-chochrane-engage-intense"
            ],
            "rotation": "sequential",
            "os_notification": False,
            "intensity": "low",
            "enabled": True
        },
        "attention": {
            # Attention-getting sounds
            "pool": [
                "peasant-what-is-it", "peasant-more-work",
                "STFC-crusher-crusher-to-bridge",
                "STFC-data-captain-l-believe-l-am-feeling-anxiety"
            ],
            "rotation": "sequential",
            "os_notification": True,
            "intensity": "medium",
            "enabled": True
        },
        "warning": {
            # Warning/error sounds
            "pool": [
                "peon-we-need-more-gold", "you_must_construct_additional_pylons",
                "STFC-borg-collective-resistance-is-futile"
            ],
            "rotation": "random",
            "os_notification": True,
            "intensity": "medium",
            "enabled": True
        },
        "refusal": {
            # Refusal/blocking sounds
            "pool": ["peon-me-not-that-kind", "rifleman-no", "peasant-dont-want-to-do-this"],
            "rotation": "random",
            "os_notification": True,
            "intensity": "high",
            "enabled": True
        },
        "easter_egg": {
            # Easter egg sounds (low probability)
            "pool": ["peon-leave-me-alone", "peasant-im-not-listening", "you_must_construct_additional_pylons"],
            "rotation": "random",
            "os_notification": False,
            "intensity": "high",
            "enabled": True,
            "probability": 0.05
        },
        "greeting": {
            # Session start/greeting sounds
            "pool": [
                "peasant-ready-to-work", "peasant-ready-to-serve",
                "STNG-picard-make-it-so", "STFC-acknowledged"
            ],
            "rotation": "sequential",
            "os_notification": False,
            "intensity": "low",
            "enabled": True
        }
    }
}

# Event to category mapping
EVENT_CATEGORY_MAP = {
    # Completion events
    "task_completed": "completion",
    "git_push_success": "completion",
    "git_mr_created": "completion",
    "build_success": "completion",
    "tests_passed": "completion",
    "deployment_complete": "completion",
    "diagnostic_complete": "completion",
    "security_audit_complete": "completion",
    "task_completed_analytical": "completion",
    
    # Acknowledgment events
    "task_acknowledged": "acknowledgment",
    "git_commit_success": "acknowledgment",
    "subagent_spawned": "acknowledgment",
    "handoff_created": "acknowledgment",
    "handoff_received": "acknowledgment",
    "message_sent": "acknowledgment",
    "message_received": "acknowledgment",
    "adr_approved": "acknowledgment",
    "plan_approved": "acknowledgment",
    "permission_granted": "acknowledgment",
    "task_started": "acknowledgment",
    "task_started_analytical": "acknowledgment",
    "diagnostic_started": "acknowledgment",
    "deployment_started": "acknowledgment",
    
    # Attention events
    "waiting_for_input": "attention",
    "permission_requested": "attention",
    "git_conflicts": "attention",
    "ready_for_next": "attention",
    "insight_discovered": "attention",
    "file_scan": "attention",
    "git_push_production": "attention",
    
    # Warning events
    "task_failed": "warning",
    "build_failed": "warning",
    "tests_failed": "warning",
    "quota_exceeded": "warning",
    "secrets_detected": "warning",
    
    # Refusal events
    "unsafe_action_blocked": "refusal",
    "security_warning": "refusal",
    
    # Greeting events
    "session_start": "greeting",
    
    # Easter eggs
    "repeated_invalid_request": "easter_egg",
    "excessive_rapid_requests": "easter_egg",

    # Hook lifecycle events (Phase 2I - T-ADR-057 v2)
    "hook_blocked_action": "warning",
    "hook_injection_detected": "warning",
    "hook_secret_blocked": "warning",
    "hook_tool_approved": "acknowledgment",
    "hook_tool_denied": "warning",
    "hook_session_started": "greeting",
    "hook_session_ended": "completion",
    "hook_session_governance_passed": "completion",
    "hook_subagent_spawned": "acknowledgment",
    "hook_subagent_completed": "acknowledgment",
    "hook_precompact_injected": "acknowledgment",
    "hook_prompt_clean": "acknowledgment",
    "hook_prompt_suspicious": "attention",
    "hook_changelog_verified": "completion",
    "hook_changelog_missing": "attention",
    "hook_tool_failure_logged": "attention",
    "hook_teammate_idle": "attention",
    "hook_op_read_blocked": "warning",
}

# Events that trigger OS notification in addition to sound (Phase 2I - T-ADR-057 v2)
CRITICAL_NOTIFICATION_EVENTS = {
    "hook_blocked_action",
    "hook_injection_detected",
    "hook_secret_blocked",
    "hook_tool_denied",
    "hook_op_read_blocked",
    "hook_changelog_missing",
    "hook_tool_failure_logged",
    "hook_prompt_suspicious",
}

# Throttle tiers (Phase 2I - T-ADR-057 v2)
THROTTLE_TIERS = {
    "default": {"max_per_minute": 5, "cooldown_seconds": 2},
    "hook_events": {"max_per_minute": 3, "cooldown_seconds": 5},
    "security_critical": {"max_per_minute": 999, "cooldown_seconds": 0},  # never throttle
}

# Events that bypass throttling (always play)
SECURITY_CRITICAL_EVENTS = {
    "hook_blocked_action",
    "hook_injection_detected",
    "hook_secret_blocked",
    "hook_op_read_blocked",
}

# Hook events use stricter throttle tier
HOOK_EVENTS = {k for k in EVENT_CATEGORY_MAP if k.startswith("hook_")}

# =============================================================================
# Agent Persona System (T-ADR-011a)
# =============================================================================

# Agent to persona mapping
AGENT_PERSONAS = {
    "cursor-agent": "peasant",      # Human Peasant (WC3) - Eager to serve
    "claude-code": "rifleman",      # Scottish Rifleman (WC3) - Professional, precise
    "gemini-cli": "peon",           # Orc Peon (WC3) - Simple, hardworking
    "default": "peasant"            # Default to Peasant
}

# Persona-specific sound pools per category
# STRICT: Each persona uses ONLY their own sounds - no cross-persona sounds!
PERSONA_SOUNDS = {
    "peasant": {
        # Cursor Agent = Human Peasant (WC3) - ONLY peasant-* sounds
        "completion": ["peasant-job-done", "peasant-jobs-done-exact", "peasant-off-i-go"],
        "acknowledgment": ["peasant-yes-me-lord", "peasant-ready-to-work", "peasant-ready-to-serve"],
        "attention": ["peasant-what-is-it", "peasant-more-work"],
        "warning": ["peasant-more-work", "you_must_construct_additional_pylons"],
        "refusal": ["peasant-dont-want-to-do-this"],
        "greeting": ["peasant-ready-to-work", "peasant-ready-to-serve"],
        "easter_egg": ["peasant-im-not-listening"]
    },
    "rifleman": {
        # Claude Code = Scottish Rifleman (WC3 Dwarf) - ONLY rifleman-* sounds
        "completion": ["rifleman-brilliant", "rifleman-thank-you", "rifleman-my-pleasure"],
        "acknowledgment": ["rifleman-aye-sir", "rifleman-aye", "rifleman-yes", "rifleman-ill-take-care-of-it"],
        "attention": ["rifleman-hello", "rifleman-how-are-ya", "rifleman-howre-ya"],
        "warning": ["rifleman-help-me"],
        "refusal": ["rifleman-no"],
        "greeting": ["rifleman-greetings", "rifleman-hello"],
        "easter_egg": []  # Rifleman (Claude Code) is the serious professional - NO easter eggs
    },
    "peon": {
        # Gemini CLI = Orc Peon (WC3) - ONLY peon-* sounds
        "completion": ["peon-zug-zug", "peon-double"],  # NO peasant-job-done!
        "acknowledgment": ["peon-zug-zug", "peon-work-work"],
        "attention": ["peon-something-need-doing"],
        "warning": ["peon-we-need-more-gold"],
        "refusal": ["peon-me-not-that-kind"],
        "greeting": ["peon-work-work", "peon-zug-zug"],
        "easter_egg": ["peon-leave-me-alone", "peon-what-exhasperated"]
    }
}


def load_config() -> dict:
    """Load configuration from YAML file or use defaults."""
    if not HAS_YAML or not CONFIG_FILE.exists():
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load config: {e}", file=sys.stderr)
        return DEFAULT_CONFIG


# =============================================================================
# T-ADR-027: Multi-Universe Sound Architecture (STNG Integration)
# =============================================================================
# Dual universe system: Warcraft (default) + STNG (contextual override)
# - Cursor = Peasant (Warcraft) / Picard (STNG)
# - Claude Code = Rifleman (Warcraft) / Data (STNG)
# - Gemini CLI = Peon (Warcraft) / Geordi (STNG)
# - Worf for security events across all agents

STNG_CONFIG_FILE = CONFIG_DIR / "stng-mcp-config.yaml"
_stng_config: dict = {}

def load_stng_config() -> dict:
    """Load T-ADR-027 multi-universe configuration."""
    global _stng_config
    if _stng_config:
        return _stng_config
    
    if not HAS_YAML or not STNG_CONFIG_FILE.exists():
        return {}
    
    try:
        with open(STNG_CONFIG_FILE) as f:
            _stng_config = yaml.safe_load(f)
            return _stng_config
    except Exception as e:
        print(f"Warning: Failed to load STNG config: {e}", file=sys.stderr)
        return {}


def resolve_stng_sound(sound_ref: str, stng_config: dict) -> Optional[str]:
    """Resolve a sound reference like 'picard.make_it_so' to actual filename."""
    if "." not in sound_ref:
        return sound_ref  # Already a direct filename
    
    character, event = sound_ref.split(".", 1)
    curated = stng_config.get("universes", {}).get("stng", {}).get("curated_sounds", {})
    char_sounds = curated.get(character, {})
    
    sound_file = char_sounds.get(event)
    if sound_file:
        # Remove .mp3 extension if present (we add it later)
        return sound_file.replace(".mp3", "")
    return None


def select_universe_and_sound(event: str, agent: str, config: dict) -> tuple[str, Optional[str]]:
    """
    T-ADR-027: Select universe (warcraft/stng) and sound based on event type.
    
    Returns: (universe, sound_filename_or_none)
    """
    stng_config = load_stng_config()
    if not stng_config:
        return ("warcraft", None)  # Fall back to warcraft if no STNG config
    
    event_mapping = stng_config.get("event_mapping", {})
    default_universe = stng_config.get("default_universe", "warcraft")
    
    # Check if this event has a specific mapping
    if event in event_mapping:
        mapping = event_mapping[event]
        universe = mapping.get("universe", default_universe)
        
        # If universe is "auto", check both warcraft and stng options
        if universe == "auto":
            # For auto events, randomly choose or use warcraft as default
            universe = default_universe
        
        # Get the sounds list for this event
        sounds = mapping.get("sounds", [])
        if sounds:
            # Pick a random sound from the list for variety
            sound_ref = random.choice(sounds)
            sound_file = resolve_stng_sound(sound_ref, stng_config)
            if sound_file:
                return (universe, sound_file)
    
    # No specific mapping - use default universe
    return (default_universe, None)


def get_stng_persona_sound(agent: str, category: str) -> Optional[str]:
    """Get STNG persona sound for agent and category (T-ADR-027 fallback)."""
    stng_config = load_stng_config()
    if not stng_config:
        return None
    
    # Map agent to STNG persona
    stng_personas = stng_config.get("universes", {}).get("stng", {}).get("agent_personas", {})
    persona = stng_personas.get(agent)
    
    if not persona:
        return None
    
    # Get curated sounds for this persona
    curated = stng_config.get("universes", {}).get("stng", {}).get("curated_sounds", {})
    persona_sounds = curated.get(persona, {})
    
    # Map category to persona sound event
    category_to_event = {
        "completion": "task_completed",
        "acknowledgment": "task_acknowledged",
        "greeting": "greeting",
        "attention": "question"
    }
    
    event = category_to_event.get(category)
    if event and event in persona_sounds:
        return persona_sounds[event].replace(".mp3", "")
    
    return None


def get_platform() -> str:
    """Detect the current platform."""
    import platform
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Windows":
        return "windows"
    else:
        return "linux"


def play_audio_file(sound_path: Path, volume: float = 0.7) -> bool:
    """Play an audio file using platform-specific command."""
    if not sound_path.exists():
        print(f"Sound file not found: {sound_path}", file=sys.stderr)
        return False
    
    platform = get_platform()
    
    try:
        if platform == "macos":
            # macOS: use afplay with volume control
            # Use Popen with start_new_session to detach from MCP process group
            # This prevents Cursor from killing the audio process prematurely
            subprocess.Popen(
                ["afplay", "-v", str(volume), str(sound_path)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True  # Return immediately, don't wait for sound to finish
        elif platform == "windows":
            # Windows: use PowerShell
            ps_cmd = f"(New-Object Media.SoundPlayer '{sound_path}').PlaySync()"
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                check=True,
                capture_output=True
            )
        else:
            # Linux: try paplay first, then aplay, then mpg123
            for cmd in [["paplay", str(sound_path)], 
                       ["aplay", str(sound_path)],
                       ["mpg123", "-q", str(sound_path)]]:
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        return True
    except Exception as e:
        print(f"Failed to play audio: {e}", file=sys.stderr)
        return False


def show_notification(title: str, message: str, sound: bool = False) -> bool:
    """Show an OS notification."""
    platform = get_platform()
    
    try:
        if platform == "macos":
            # macOS: use osascript
            script = f'display notification "{message}" with title "{title}"'
            if sound:
                script += ' sound name "Glass"'
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True
            )
        elif platform == "windows":
            # Windows: use PowerShell toast notification
            ps_cmd = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $template.SelectSingleNode('//text[@id=1]').AppendChild($template.CreateTextNode('{title}'))
            $template.SelectSingleNode('//text[@id=2]').AppendChild($template.CreateTextNode('{message}'))
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Cursor').Show([Windows.UI.Notifications.ToastNotification]::new($template))
            """
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                capture_output=True
            )
        else:
            # Linux: use notify-send
            subprocess.run(
                ["notify-send", title, message],
                capture_output=True
            )
        return True
    except Exception as e:
        print(f"Failed to show notification: {e}", file=sys.stderr)
        return False


def should_throttle(config: dict, event: Optional[str] = None) -> bool:
    """Check if we should throttle sounds due to rate limiting.
    Phase 2I: Uses throttle tiers - security critical events never throttle.
    """
    global _sounds_this_minute, _hook_sounds_this_minute

    now = time.time()

    # Security critical events never throttle
    if event and event in SECURITY_CRITICAL_EVENTS:
        return False

    # Hook events use stricter tier
    if event and event in HOOK_EVENTS:
        tier = THROTTLE_TIERS["hook_events"]
        _hook_sounds_this_minute[:] = [t for t in _hook_sounds_this_minute if now - t < 60]
        return len(_hook_sounds_this_minute) >= tier["max_per_minute"]

    # Default tier
    tier = THROTTLE_TIERS["default"]
    settings = config.get("settings", {})
    max_per_minute = settings.get("max_sounds_per_minute", tier["max_per_minute"])

    _sounds_this_minute = [t for t in _sounds_this_minute if now - t < 60]
    return len(_sounds_this_minute) >= max_per_minute


def check_cooldown(sound_name: str, config: dict) -> bool:
    """Check if sound is still in cooldown period.
    
    Per user feedback: Rely on ROTATION for variety, not blocking.
    Cooldown only prevents the EXACT SAME sound within 500ms (accidental double-tap).
    """
    settings = config.get("settings", {})
    # Minimal cooldown - just prevent accidental double-triggers
    cooldown_ms = settings.get("sound_cooldown_ms", 500)  # Reduced from 2000ms
    cooldown_sec = cooldown_ms / 1000
    
    last_time = _last_played.get(sound_name, 0)
    return (time.time() - last_time) < cooldown_sec


def get_existing_sounds(pool: list[str]) -> list[str]:
    """Filter pool to only sounds that actually exist on disk."""
    existing = []
    for sound in pool:
        sound_file = sound if sound.endswith(".mp3") else f"{sound}.mp3"
        if (SOUNDS_DIR / sound_file).exists():
            existing.append(sound)
    return existing


def select_sound_from_pool(category: str, category_config: dict) -> Optional[str]:
    """Select a sound from the category pool using rotation strategy.
    
    Only considers sounds that actually exist on disk.
    """
    pool = category_config.get("pool", [])
    if not pool:
        return None
    
    # Filter to existing sounds only
    pool = get_existing_sounds(pool)
    if not pool:
        return None
    
    rotation = category_config.get("rotation", "random")
    last_sound = _last_category_sound.get(category)
    
    if rotation == "sequential":
        # Get next sound in sequence
        if last_sound and last_sound in pool:
            idx = (pool.index(last_sound) + 1) % len(pool)
        else:
            idx = 0
        return pool[idx]
    else:
        # Random selection, avoiding last played if possible
        available = [s for s in pool if s != last_sound] if last_sound else pool
        if not available:
            available = pool
        return random.choice(available)


def get_persona_sound(agent: str, category: str) -> Optional[str]:
    """Get a sound for an agent's persona and category."""
    persona = AGENT_PERSONAS.get(agent, AGENT_PERSONAS["default"])
    persona_sounds = PERSONA_SOUNDS.get(persona, {})
    category_sounds = persona_sounds.get(category, [])
    
    if not category_sounds:
        # Fallback to default peasant sounds
        category_sounds = PERSONA_SOUNDS["peasant"].get(category, [])
    
    if not category_sounds:
        return None
    
    # Select sound, avoiding last played for this category
    last_sound = _last_category_sound.get(f"{agent}_{category}")
    available = [s for s in category_sounds if s != last_sound] if last_sound else category_sounds
    if not available:
        available = category_sounds
    
    return random.choice(available)


def play_sound(
    event: Optional[str] = None,
    category: Optional[str] = None,
    sound: Optional[str] = None,
    message: Optional[str] = None,
    agent: Optional[str] = None,
    force: bool = False
) -> dict:
    """
    Play an audio notification.
    
    Args:
        event: Event type (e.g., "task_completed", "git_push_success")
        category: Category name (e.g., "completion", "warning")
        sound: Specific sound name (overrides category and persona selection)
        message: Optional message for OS notification
        agent: Agent identifier for persona-specific sounds (cursor-agent, claude-code, gemini-cli)
        force: Bypass cooldown and throttle checks
    
    Returns:
        dict with status and details
    """
    global _sounds_this_minute, _hook_sounds_this_minute

    config = load_config()
    settings = config.get("settings", {})
    
    # Use DEFAULT_AGENT from --agent CLI flag if not specified (T-ADR-017a)
    if not agent:
        agent = DEFAULT_AGENT
    
    # Check if audio is enabled
    if not settings.get("enabled", True):
        return {"status": "disabled", "message": "Audio notifications are disabled"}
    
    # T-ADR-027: Multi-Universe Sound Selection (CHECK THIS FIRST)
    # Priority: 1) Explicit sound, 2) STNG event mapping, 3) Warcraft persona, 4) Category pool
    universe = "warcraft"  # Default
    
    if not sound and event:
        # Check for T-ADR-027 STNG event mapping first (before category resolution!)
        universe, stng_sound = select_universe_and_sound(event, agent, config)
        if stng_sound:
            sound = stng_sound
    
    # Resolve category from event if not provided
    if not category and event:
        category = EVENT_CATEGORY_MAP.get(event)
    
    # If we have an STNG sound from event mapping, we don't need category
    if not category and not sound:
        return {"status": "error", "message": "No category or sound specified"}
    
    # Get category configuration
    categories = config.get("categories", {})
    category_config = categories.get(category, {}) if category else {}
    
    # Check if category is enabled
    if category and not category_config.get("enabled", True):
        return {"status": "disabled", "message": f"Category '{category}' is disabled"}
    
    # Handle easter egg probability
    if category == "easter_egg" and not force:
        probability = category_config.get("probability", settings.get("easter_egg_probability", 0.05))
        if random.random() > probability:
            return {"status": "skipped", "message": "Easter egg probability check failed"}
    
    # Check throttling (Phase 2I: event-aware throttle tiers)
    if not force and should_throttle(config, event):
        if settings.get("fallback_to_notifications", True):
            # Fall back to silent notification
            agent_name = agent.replace("-", " ").title()
            if message:
                show_notification(f"{agent_name}", message, sound=False)
            return {"status": "throttled", "message": "Rate limited, showed silent notification"}
        return {"status": "throttled", "message": "Rate limited"}
    
    # If no sound yet, try persona-based selection
    if not sound:
        # Try STNG persona sound if we're in STNG universe context
        if universe == "stng":
            sound = get_stng_persona_sound(agent, category)
        
        # Fall back to Warcraft persona sounds
        if not sound:
            sound = get_persona_sound(agent, category)
        
        # Final fallback to category config pool
        if not sound:
            sound = select_sound_from_pool(category, category_config)
    
    if not sound:
        return {"status": "error", "message": "No sound available"}
    
    # Check cooldown
    if not force and check_cooldown(sound, config):
        return {"status": "cooldown", "message": f"Sound '{sound}' is in cooldown"}
    
    # Build sound path
    sound_file = sound if sound.endswith(".mp3") else f"{sound}.mp3"
    sound_path = SOUNDS_DIR / sound_file
    
    # Play the sound
    volume = settings.get("volume", 0.7)
    played = play_audio_file(sound_path, volume)
    
    if played:
        # Update state
        now = time.time()
        _last_played[sound] = now
        _sounds_this_minute.append(now)
        if event and event in HOOK_EVENTS:
            _hook_sounds_this_minute.append(now)
        if category:
            _last_category_sound[f"{agent}_{category}"] = sound

        # Phase 2I: Show OS notification for critical security events (always)
        if event and event in CRITICAL_NOTIFICATION_EVENTS:
            agent_name = agent.replace("-", " ").title()
            notif_message = message or f"{event.replace('hook_', '').replace('_', ' ').title()}"
            show_notification(f"Security: {agent_name}", notif_message, sound=False)

        # Show OS notification if configured (category-based)
        os_notif = settings.get("os_notifications", {})
        if os_notif.get("enabled", True) and category_config.get("os_notification", False):
            # Use agent persona name in notification
            persona = AGENT_PERSONAS.get(agent, "peasant").title()
            agent_name = agent.replace("-", " ").title()
            notif_message = message or f"{category.title()} event"
            show_notification(f"{agent_name} ({persona})", notif_message, sound=False)
        
        # Determine persona based on universe (T-ADR-027)
        if universe == "stng":
            stng_config = load_stng_config()
            stng_personas = stng_config.get("universes", {}).get("stng", {}).get("agent_personas", {})
            persona = stng_personas.get(agent, "picard")
        else:
            persona = AGENT_PERSONAS.get(agent, "peasant")
        
        return {
            "status": "success",
            "sound": sound,
            "category": category,
            "agent": agent,
            "universe": universe,
            "persona": persona,
            "message": f"Played '{sound}' for {agent} ({universe}/{persona})"
        }
    else:
        return {"status": "error", "message": f"Failed to play '{sound}'"}


# =============================================================================
# MCP Server Implementation
# =============================================================================

def handle_request(request: dict) -> dict:
    """Handle an MCP request."""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "cursor-sound-server",
                    "version": "2.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "play_sound",
                        "description": "Play an audio notification with agent-specific persona sounds. Use for task completion, errors, or when needing user attention. Each agent has a distinct persona (Cursor=Peasant, Claude=Rifleman, Gemini=Peon) per T-ADR-011a.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "event": {
                                    "type": "string",
                                    "description": "Event type: task_completed, git_push_success, git_commit_success, waiting_for_input, task_failed, etc.",
                                    "enum": list(EVENT_CATEGORY_MAP.keys())
                                },
                                "category": {
                                    "type": "string",
                                    "description": "Sound category: completion, acknowledgment, attention, warning, refusal, easter_egg, greeting",
                                    "enum": ["completion", "acknowledgment", "attention", "warning", "refusal", "easter_egg", "greeting"]
                                },
                                "agent": {
                                    "type": "string",
                                    "description": "Agent identifier for persona-specific sounds: cursor-agent (Peasant), claude-code (Rifleman), gemini-cli (Peon)",
                                    "enum": ["cursor-agent", "claude-code", "gemini-cli"],
                                    "default": "cursor-agent"
                                },
                                "sound": {
                                    "type": "string",
                                    "description": "Specific sound name (optional, overrides category and persona)"
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Message for OS notification (optional)"
                                }
                            }
                        }
                    },
                    {
                        "name": "show_notification",
                        "description": "Show an OS notification without sound.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Notification title",
                                    "default": "Cursor Agent"
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Notification message"
                                }
                            },
                            "required": ["message"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        if tool_name == "play_sound":
            result = play_sound(**tool_args)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result)
                        }
                    ]
                }
            }
        
        elif tool_name == "show_notification":
            title = tool_args.get("title", "Cursor Agent")
            message = tool_args.get("message", "")
            success = show_notification(title, message)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"status": "success" if success else "error"})
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    elif method == "notifications/initialized":
        # Acknowledgment, no response needed
        return None
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


def main():
    """Main entry point for the MCP server."""
    # Get persona for configured agent
    persona = AGENT_PERSONAS.get(DEFAULT_AGENT, "peasant")
    
    print("Universal Sound MCP Server v3.1.0 (T-ADR-017, T-ADR-017a)", file=sys.stderr)
    print(f"Sounds directory: {SOUNDS_DIR}", file=sys.stderr)
    print(f"Config file: {CONFIG_FILE}", file=sys.stderr)
    print(f"Configured agent: {DEFAULT_AGENT} → {persona} persona", file=sys.stderr)
    print(f"Agent Personas: cursor-agent→peasant, claude-code→rifleman, gemini-cli→peon", file=sys.stderr)
    
    # Read JSON-RPC messages from stdin, write responses to stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            response = handle_request(request)
            
            if response:
                print(json.dumps(response), flush=True)
        
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
