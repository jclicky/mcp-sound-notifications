---
name: audio-notifications
description: Play audio notification sounds at workflow boundaries
activation: always_on
---

# Audio Notification Protocol

Play audio cues at workflow boundaries to notify the developer.

## When to Play Sounds

| Condition | Sound Call |
|-----------|-----------|
| Starting user-requested work | `play_sound(event="task_acknowledged")` |
| Completed significant work (3+ files) | `play_sound(event="task_completed")` |
| Git push success | `play_sound(event="git_push_success")` |
| Need user input / blocked | `play_sound(event="waiting_for_input")` |
| Error or failure | `play_sound(event="task_failed")` |
| Trivial action (single file read) | **No sound** |

## MCP Tool Usage

Use the `play_sound` tool from the sound-notifications MCP server:

```python
play_sound(event="task_completed")
play_sound(event="task_acknowledged")
play_sound(category="completion")
```

## Do NOT

- Play sounds for every tiny action
- Play sounds in rapid succession (rate limit: 1 sound per 5 seconds)
- Skip sounds for user-requested deliverables
