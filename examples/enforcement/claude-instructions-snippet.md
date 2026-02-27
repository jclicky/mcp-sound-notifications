# Sound Notifications Snippet for Claude Code
#
# Add the content below to your `.claude/CLAUDE.md` context file.
# -----------------------------------------------------------------------

## 🔊 Audio Notifications

This project uses the `sound-notifications` MCP server for audio workflow cues.

**When to play sounds**:
- `play_sound(event="task_acknowledged")` - Starting user-requested work
- `play_sound(event="task_completed")` - Completed significant work (3+ files)
- `play_sound(event="waiting_for_input")` - Need user decision
- `play_sound(event="task_failed")` - Error occurred
- `play_sound(event="git_push_success")` - Pushed to remote

**When NOT to play sounds**: Trivial actions (single file read, context checks).

**Rate limit**: Max 1 sound per 5 seconds to avoid noise.
