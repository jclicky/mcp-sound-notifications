#!/bin/bash
# =============================================================================
# MCP Sound Notifications - Universal Installer
# =============================================================================
# Installs the audio notification MCP server and configures it for your IDE.
#
# Usage:
#   ./install.sh                      # Install for Cursor (default)
#   ./install.sh --ide cursor         # Cursor only
#   ./install.sh --ide claude         # Claude Code only
#   ./install.sh --ide windsurf       # Windsurf only
#   ./install.sh --ide all            # All supported IDEs
#   ./install.sh --ide cursor,claude  # Multiple IDEs
#   ./install.sh --uninstall          # Remove installation

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSION="1.0.0"
INSTALL_DIR="$HOME/.config/sound-notifications"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# IDE MCP config locations
CURSOR_MCP="$HOME/.cursor/mcp.json"
CLAUDE_MCP="$HOME/.claude/mcp.json"
WINDSURF_MCP="$HOME/.codeium/windsurf/mcp_config.json"

DEFAULT_IDE="cursor"

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║   MCP Sound Notifications - Installer v$VERSION     ║"
    echo "║   Audio feedback for AI agent workflows          ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }

check_python() {
    if ! command -v python3 &>/dev/null; then
        err "Python 3 is required but not found."
        echo "  Install via: brew install python3 (macOS) or apt install python3 (Linux)"
        exit 1
    fi
    ok "Python 3 found: $(python3 --version)"
}

install_files() {
    echo ""
    echo "📦 Installing to $INSTALL_DIR ..."
    mkdir -p "$INSTALL_DIR"
    
    # Copy server
    mkdir -p "$INSTALL_DIR/mcp-server"
    cp "$REPO_DIR/mcp-server/sound_server.py" "$INSTALL_DIR/mcp-server/"
    cp "$REPO_DIR/mcp-server/__init__.py" "$INSTALL_DIR/mcp-server/" 2>/dev/null || true
    
    # Copy config (don't overwrite existing)
    mkdir -p "$INSTALL_DIR/config/themes/default"
    if [[ ! -f "$INSTALL_DIR/config/sound-config.yaml" ]]; then
        cp "$REPO_DIR/config/sound-config.yaml" "$INSTALL_DIR/config/"
        ok "Installed default configuration"
    else
        warn "Config exists, not overwriting ($INSTALL_DIR/config/sound-config.yaml)"
    fi
    
    # Copy theme templates
    cp -r "$REPO_DIR/config/themes/example-"* "$INSTALL_DIR/config/themes/" 2>/dev/null || true
    
    # Copy scripts
    mkdir -p "$INSTALL_DIR/scripts"
    cp "$REPO_DIR/scripts/find-system-sounds.sh" "$INSTALL_DIR/scripts/"
    cp "$REPO_DIR/scripts/fetch-freesounds.py" "$INSTALL_DIR/scripts/"
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    
    ok "Files installed to $INSTALL_DIR"
}

configure_ide() {
    local ide="$1"
    local config_file=""
    local agent_id=""
    local server_path="$INSTALL_DIR/mcp-server/sound_server.py"
    
    case "$ide" in
        cursor)
            config_file="$CURSOR_MCP"
            agent_id="cursor-agent"
            ;;
        claude)
            config_file="$CLAUDE_MCP"
            agent_id="claude-code"
            ;;
        windsurf)
            config_file="$WINDSURF_MCP"
            agent_id="windsurf-agent"
            ;;
        *)
            warn "Unknown IDE: $ide"
            return
            ;;
    esac
    
    # Ensure parent directory exists
    mkdir -p "$(dirname "$config_file")"
    
    # Check if config already has sound-notifications
    if [[ -f "$config_file" ]] && python3 -c "
import json, sys
with open('$config_file') as f:
    d = json.load(f)
servers = d.get('mcpServers', {})
if 'sound-notifications' in servers:
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        warn "$ide: sound-notifications already configured in $config_file"
        return
    fi
    
    # Add MCP server entry
    python3 -c "
import json, sys
config_file = '$config_file'
try:
    with open(config_file) as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['sound-notifications'] = {
    'command': 'python3',
    'args': ['$server_path', '--agent', '$agent_id']
}

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
"
    
    ok "$ide: Configured in $config_file (agent: $agent_id)"
}

uninstall() {
    echo "🗑️  Uninstalling..."
    
    # Remove from IDE configs
    for config_file in "$CURSOR_MCP" "$CLAUDE_MCP" "$WINDSURF_MCP"; do
        if [[ -f "$config_file" ]]; then
            python3 -c "
import json
config_file = '$config_file'
try:
    with open(config_file) as f:
        config = json.load(f)
    if 'mcpServers' in config and 'sound-notifications' in config['mcpServers']:
        del config['mcpServers']['sound-notifications']
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f'  Removed from {config_file}')
except Exception:
    pass
" 2>/dev/null || true
        fi
    done
    
    # Remove install directory
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        ok "Removed $INSTALL_DIR"
    fi
    
    ok "Uninstalled. Restart your IDE(s) to complete."
}

# =============================================================================
# Main
# =============================================================================

print_header

IDES="$DEFAULT_IDE"
UNINSTALL=false
WITH_ENFORCEMENT=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ide) IDES="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
        --with-enforcement) WITH_ENFORCEMENT=true; shift ;;
        --no-enforcement) WITH_ENFORCEMENT=false; shift ;;
        --help|-h)
            echo "Usage: $0 [--ide cursor|claude|windsurf|all] [--with-enforcement|--no-enforcement] [--uninstall]"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if $UNINSTALL; then
    uninstall
    exit 0
fi

check_python
install_files

echo ""
echo "🔧 Configuring IDEs..."

if [[ "$IDES" == "all" ]]; then
    IDES="cursor,claude,windsurf"
fi

IFS=',' read -ra IDE_LIST <<< "$IDES"
for ide in "${IDE_LIST[@]}"; do
    configure_ide "$(echo "$ide" | tr -d ' ')"
done

# Enforcement layer installation (T-ADR-055)
if $WITH_ENFORCEMENT; then
    echo ""
    echo "📋 Installing enforcement layer (rules + hooks)..."
    ENFORCEMENT_DIR="$REPO_DIR/examples/enforcement"
    
    IFS=',' read -ra ENFORCE_LIST <<< "$IDES"
    for ide in "${ENFORCE_LIST[@]}"; do
        ide="$(echo "$ide" | tr -d ' ')"
        case "$ide" in
            cursor)
                if [[ -d ".cursor/rules" ]]; then
                    cp "$ENFORCEMENT_DIR/cursor-rule.mdc" ".cursor/rules/audio-notifications.mdc" 2>/dev/null && \
                        ok "cursor: Installed enforcement rule (.cursor/rules/audio-notifications.mdc)" || \
                        warn "cursor: Could not install rule (no .cursor/rules/ in current directory)"
                else
                    warn "cursor: No .cursor/rules/ directory in current working directory. Copy manually:"
                    echo "        cp $ENFORCEMENT_DIR/cursor-rule.mdc .cursor/rules/audio-notifications.mdc"
                fi
                ;;
            windsurf)
                if [[ -d ".windsurf/rules" ]]; then
                    cp "$ENFORCEMENT_DIR/windsurf-rule.md" ".windsurf/rules/audio-notifications.md" 2>/dev/null && \
                        ok "windsurf: Installed enforcement rule (.windsurf/rules/audio-notifications.md)" || \
                        warn "windsurf: Could not install rule"
                else
                    warn "windsurf: No .windsurf/rules/ directory. Copy manually:"
                    echo "          cp $ENFORCEMENT_DIR/windsurf-rule.md .windsurf/rules/audio-notifications.md"
                fi
                ;;
            claude)
                echo "  claude: Add snippet from $ENFORCEMENT_DIR/claude-instructions-snippet.md to your .claude/CLAUDE.md"
                ;;
        esac
    done
    ok "Enforcement layer installed"
else
    warn "Enforcement layer skipped (--no-enforcement). Agents may not call the MCP server consistently."
    echo "  To install later: $0 --with-enforcement --ide $IDES"
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart your IDE(s) to activate the MCP server"
echo "  2. Add sound files to: $INSTALL_DIR/config/themes/default/"
echo "     Or run: $INSTALL_DIR/scripts/find-system-sounds.sh"
echo "  3. Configure personas in: $INSTALL_DIR/config/sound-config.yaml"
echo ""
echo "Test it: Ask your AI agent to play a completion sound!"
