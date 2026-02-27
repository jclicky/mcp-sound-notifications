# Sound Notifications Snippet for GitHub Copilot
#
# Add the content below to your `.github/copilot-instructions.md` file.
# -----------------------------------------------------------------------

## Audio Notifications

This project uses the `sound-notifications` MCP server to play audio cues
at workflow boundaries. When completing significant work (3+ file changes),
call `play_sound(event="task_completed")`. When starting user-requested
work, call `play_sound(event="task_acknowledged")`. When blocked or needing
user input, call `play_sound(event="waiting_for_input")`. Do not play sounds
for trivial actions like reading a single file.
