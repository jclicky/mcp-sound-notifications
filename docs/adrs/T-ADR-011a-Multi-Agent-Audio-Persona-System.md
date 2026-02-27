# T-ADR-011a: Multi-Agent Audio Persona System

**Status**: Accepted
**Date**: 2026-01-31

## Overview

This ADR defines how **multiple concurrent AI agents** receive distinct audio personas, enabling developers to identify which agent completed work by sound alone.

## Problem Statement

When 3+ AI agents work simultaneously (IDE agent, terminal agents, sub-agents):
- Can't tell which agent completed work
- Audio fatigue from identical sounds
- Confusion about which terminal needs attention
- Lost context during multitasking

## Decision

**Each agent gets a unique character persona** with dedicated sound pools.

### Default Persona Assignments

| Agent | Persona | Character | Sound Prefix |
|-------|---------|-----------|--------------|
| **Cursor** | Human Peasant | Warcraft III Peasant | `peasant-*` |
| **Claude Code** | Dwarven Rifleman | Warcraft III Rifleman | `rifleman-*` |
| **Gemini CLI** | Orc Peon | Warcraft III Peon | `peon-*` |

### Why Personas Work

**Without distinct audio personas:**
- Audio becomes noise -- "something happened, somewhere"
- Users mute notifications (defeating the purpose)

**With audio personas:**
- Instant recognition: "That's the Rifleman -- Claude Code finished!"
- Thematic coherence (managing workers like an RTS base)
- Scalable to N agents without chaos

### Sound Pool Design

Each persona maps to action categories:

| Action Type | Cursor (Peasant) | Claude (Rifleman) | Gemini (Peon) |
|-------------|-------------------|--------------------|---------------|
| **Start Work** | `yes-me-lord` | `aye-sir` | `work-work` |
| **Complete Task** | `job-done` | `job-done` | `zug-zug` |
| **Need Input** | `what-is-it` | `speak` | `something-need-doing` |
| **Error/Warning** | `help` | `help` | `help-me` |

### Anti-Fatigue Design

Multi-agent scenarios risk audio collision (3 agents completing within seconds):

1. **Per-Agent Cooldowns**: Each agent has independent cooldown tracking
2. **Global Rate Limiting**: Max sounds/minute across all agents with priority enforcement
3. **Cross-Agent Rotation**: Completion sounds rotate globally to prevent repetition
4. **Notification Fallback**: When throttled, silent OS notification with agent name

### Professional Boundaries

```yaml
# Per-agent intensity controls
agents:
  claude-code:
    intensity_max: low         # Always professional
    easter_eggs_enabled: false
  gemini-cli:
    intensity_max: medium
    easter_eggs_enabled: true
    easter_egg_probability: 0.05
  cursor-agent:
    intensity_max: medium
    easter_eggs_enabled: true
    easter_egg_probability: 0.03
```

Work-safe mode (`CURSOR_AUDIO_WORK_MODE=true`) restricts to low-intensity sounds only.

## Consequences

### Positive
- Developers identify agents by sound alone (>90% accuracy after learning period)
- Reduced audio fatigue through variation and rotation
- Scalable: add agents by assigning new personas
- Professional yet engaging

### Negative
- Initial learning curve for persona associations
- More sound files to manage per persona

## Related ADRs

- [T-ADR-017: Universal Sound Notification Architecture](T-ADR-017-Universal-Sound-Notification-Architecture.md) -- MCP integration
- [S-ADR-021: Actor-Centric Sound Design Philosophy](S-ADR-021-Actor-Centric-Sound-Design-Philosophy.md) -- Design philosophy

## Configuration

See [Customization Guide](../CUSTOMIZATION.md) for persona setup and the project's [sound-config.yaml](../../config/sound-config.yaml) for the default configuration.
