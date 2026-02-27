# S-ADR-021: Actor-Centric Sound Design Philosophy

**Status**: Accepted
**Date**: 2026-02-05

## Overview

This strategic ADR establishes the **overarching philosophy** for multi-agent audio design: sounds should be **actor-centric, not event-centric**.

## The Core Insight

Traditional notification systems are event-centric:

```
Event: "task_completed" → Play: completion-sound.mp3
```

This tells the user "something happened" but not "who did what." In a multi-agent system, this is insufficient.

**Our approach is actor-centric:**

```
Actor: "cursor" (Peasant persona)
  Action: "completing_work"
    → Play: peasant-job-done.mp3
```

Sound selection starts with **WHO** (persona), then **WHAT** (action type).

## Decision

### Auditory Anthropomorphization for Developer Observability

We assign distinct audio personas to each agent, creating **semantic layering** where:
- You learn: Peasant voice = Cursor = general assistance
- You learn: Rifleman voice = Claude Code = precise analysis
- You learn: Peon voice = Gemini CLI = heavy lifting

This is UX design, not philosophy. Personas are handles for human cognition.

### Dual-Universe Persona System

Each agent has personas in **two complementary sound universes**:

| Agent | Universe A Persona | Universe B Persona | Archetype |
|-------|-------------------|-------------------|-----------|
| **Cursor** | Human Peasant (Warcraft) | Captain Picard (STNG) | Command |
| **Claude Code** | Dwarven Rifleman (Warcraft) | Commander Data (STNG) | Analytical |
| **Gemini CLI** | Orc Peon (Warcraft) | Lt. Geordi LaForge (STNG) | Engineering |

**Why two universes?**
- **Warcraft**: Quick, distinctive work sounds (acknowledgments, completions)
- **Star Trek TNG**: Richer vocabulary for complex actions (handoffs, security, collaboration)
- **Variation**: Larger pool prevents repetition
- **Context**: Different universes suit different contexts

### Action Type Categories

Sounds map to semantic action categories, not raw events:

| Category | Description | Example Sounds |
|----------|-------------|----------------|
| **Initiating Work** | Agent starting a task | "More work?", "Report!" |
| **Completing Work** | Agent finishing a task | "Job's done!", "Engage" |
| **Acknowledging** | Quick confirmation | "Aye sir", "Ready to work" |
| **Delegating** | Handing off to another agent | "Off I go", "Number One" |
| **Combat/Debug** | Error handling, intense work | "Charge!", "Red alert" |

### Anti-Fatigue Mechanisms

1. **Recency Tracking**: Don't repeat a sound within the last 3-5 plays
2. **Weighted Selection**: Sounds weighted by recency, context match, and random jitter
3. **Cross-Agent Coordination**: Completion sounds rotate globally across agents
4. **Easter Eggs**: Rare, context-specific sounds at low probability (3-8%)

### Ambient System Sounds

Some events are system-level, not actor-specific:

| System Event | Sound Type | Examples |
|--------------|-----------|----------|
| MCP Operations | Ambient | Combadge chirp, tricorder scan |
| Security Events | Alert | Red alert, shields up |
| Background Processing | Work sounds | Building, assembling |

## Consequences

### Positive
- **Instant Recognition**: Developers identify agents by sound alone
- **Reduced Fatigue**: Variation and rotation prevent repetitive notifications
- **Semantic Richness**: Sounds convey "who did what", not just "something happened"
- **Scalability**: New agents get new personas (Goblin Tinker, Worf, etc.)
- **Delight**: Nostalgic sounds create engagement without unprofessionalism

### Negative
- Initial learning curve for persona associations
- Larger sound library to maintain
- Some sound files may be extraction artifacts vs. intentional variations

## Related ADRs

- [T-ADR-011a: Multi-Agent Audio Persona System](T-ADR-011a-Multi-Agent-Audio-Persona-System.md) -- Persona assignments and configuration
- [T-ADR-017: Universal Sound Notification Architecture](T-ADR-017-Universal-Sound-Notification-Architecture.md) -- MCP server and multi-IDE integration

## The Meta-Principle

> **Auditory Anthropomorphization for Developer Observability**
>
> We're not claiming agents are sentient. We're using distinct audio personas to
> make a multi-agent system **observable** to humans. When you hear "Yes me lord",
> you know Cursor acknowledged. When you hear "Aye sir", you know Claude confirmed.
>
> This is UX design, not philosophy. Personas are handles for human cognition.
