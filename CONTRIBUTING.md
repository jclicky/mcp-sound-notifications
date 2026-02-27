# Contributing

Contributions welcome! Here's how to help.

## Sound Contributions

The most valuable contributions are **CC0-licensed sound packs**:

1. Record or find sounds under CC0 / public domain license
2. Organize by category (completion, acknowledgment, attention, warning, etc.)
3. Keep files short (< 3 seconds) and normalized
4. Submit as a new theme in `config/themes/your-theme/`

## Code Contributions

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Make changes
4. Test: Run the server manually and verify sounds play
5. Submit a pull request

## Guidelines

- **No copyrighted sounds**: All submitted sounds must be CC0, MIT, or public domain
- **Cross-platform**: Changes should work on macOS and Linux (Windows is best-effort)
- **No new dependencies**: The server runs on Python 3.9+ with zero required dependencies
- **Backward compatible**: Don't break existing configurations

## Reporting Issues

Include:
- OS and version
- IDE and version
- Python version (`python3 --version`)
- The MCP config you're using
- Any error output from the IDE's MCP log
