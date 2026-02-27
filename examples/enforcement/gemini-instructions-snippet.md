# Sound Notifications Snippet for Gemini CLI
#
# Add the content below to your `.gemini/GEMINI.md` context file.
# -----------------------------------------------------------------------

## 🔊 Audio Notifications

This project uses the `sound-notifications` MCP server for audio workflow cues.

**When to play sounds**:
- `play_sound(event="task_acknowledged")` - Starting user-requested work
- `play_sound(event="task_completed")` - Completed significant work (3+ files)
- `play_sound(event="waiting_for_input")` - Need user decision
- `play_sound(event="task_failed")` - Error occurred

**When NOT to play sounds**: Trivial actions (single file read, context checks).

**Fallback**: If MCP is unavailable, use CLI: `sound-notify --event task_completed`
