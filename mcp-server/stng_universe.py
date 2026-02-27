#!/usr/bin/env python3
"""
STNG Universe Module for MCP Sound Server
==========================================
ADR: T-ADR-027 - Multi-Universe Sound Architecture

Adds Star Trek: TNG sound support to existing Warcraft III sound system.
This module can be imported by sound_server.py without modifying core logic.

Usage:
    from stng_universe import STNGUniverse

    stng = STNGUniverse()
    sounds = stng.select_sounds(agent="claude-code", event="task_completed",
                                  context={"analytical": True})
    # Returns sound filenames from your stng-mcp-config.yaml curated_sounds section
"""

from pathlib import Path
from typing import List, Dict, Optional
import yaml


class STNGUniverse:
    """STNG Sound Universe selector and manager."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize STNG universe.

        Args:
            config_path: Path to stng-mcp-config.yaml (auto-detects if None)
        """
        if config_path is None:
            # Auto-detect config file
            script_dir = Path(__file__).parent.resolve()
            config_path = script_dir.parent / "stng-mcp-config.yaml"

        self.config = {}
        self.enabled = False

        if config_path.exists():
            try:
                with open(config_path) as f:
                    self.config = yaml.safe_load(f) or {}
                self.enabled = self.config.get("universes", {}).get("stng", {}).get("enabled", False)
            except Exception as e:
                print(f"Warning: Could not load STNG config: {e}")

    def should_use_stng(self, agent: str, event: str, context: Dict) -> bool:
        """
        Determine if STNG universe should be used for this event.

        T-ADR-027 Context Triggers:
        - Security events → STNG
        - Analytical work → STNG
        - Inter-agent comm → STNG
        - Architecture decisions → STNG
        - Production deploys → STNG
        - Diagnostics → STNG

        Args:
            agent: Agent identifier
            event: Event type
            context: Event context dict

        Returns:
            True if STNG should be used, False for Warcraft default
        """
        if not self.enabled:
            return False

        # Security events
        if event in ["security_warning", "unsafe_action_blocked", "secrets_detected"]:
            return True

        # Analytical work
        if context.get("analytical", False):
            return True
        if event in ["security_audit_complete", "code_analysis_complete", "rca_generated"]:
            return True

        # Inter-agent communication
        if event in ["handoff_created", "handoff_received", "message_sent", "message_received"]:
            return True

        # Architecture decisions
        if event in ["adr_approved", "plan_approved", "permission_granted"]:
            return True

        # Production deployments
        if context.get("production", False):
            return True
        if event in ["deployment_started", "deployment_complete", "git_push_production"]:
            return True

        # Diagnostic operations
        if event in ["diagnostic_started", "diagnostic_complete", "file_scan"]:
            return True

        return False

    def get_agent_persona(self, agent: str) -> str:
        """
        Get STNG persona for agent.

        Args:
            agent: Agent identifier (cursor-agent, claude-code, gemini-cli)

        Returns:
            STNG persona (picard, data, geordi)
        """
        personas = self.config.get("universes", {}).get("stng", {}).get("agent_personas", {})
        return personas.get(agent, "data")  # Default to Data

    def select_sounds(self, agent: str, event: str, context: Optional[Dict] = None) -> List[str]:
        """
        Select STNG sounds to play for an event.

        Args:
            agent: Agent identifier
            event: Event type
            context: Event context

        Returns:
            List of sound filenames to play in sequence
        """
        if context is None:
            context = {}

        if not self.should_use_stng(agent, event, context):
            return []

        # Get event mapping
        event_mapping = self.config.get("event_mapping", {}).get(event, {})
        if not event_mapping:
            # No mapping, return empty (fall back to Warcraft)
            return []

        sound_refs = event_mapping.get("sounds", [])
        curated_sounds = self.config.get("universes", {}).get("stng", {}).get("curated_sounds", {})

        sounds = []
        for ref in sound_refs:
            if "." in ref:
                # Parse persona.use_case reference
                persona, use_case = ref.split(".", 1)
                persona_sounds = curated_sounds.get(persona, {})
                filename = persona_sounds.get(use_case)
                if filename:
                    sounds.append(filename)
            else:
                # Direct filename
                sounds.append(ref)

        return sounds

    def get_sound_info(self, agent: str, event: str, context: Optional[Dict] = None) -> Dict:
        """
        Get comprehensive sound selection info for debugging.

        Args:
            agent: Agent identifier
            event: Event type
            context: Event context

        Returns:
            Dict with universe, persona, sounds, and trigger reason
        """
        if context is None:
            context = {}

        should_use_stng = self.should_use_stng(agent, event, context)
        sounds = self.select_sounds(agent, event, context) if should_use_stng else []

        # Determine trigger reason
        trigger = "none"
        if should_use_stng:
            if event in ["security_warning", "unsafe_action_blocked"]:
                trigger = "security_event"
            elif context.get("analytical"):
                trigger = "analytical_context"
            elif event in ["handoff_created", "handoff_received"]:
                trigger = "inter_agent_communication"
            elif event in ["adr_approved", "plan_approved"]:
                trigger = "architecture_decision"
            elif context.get("production"):
                trigger = "production_deployment"
            elif event in ["diagnostic_started", "diagnostic_complete"]:
                trigger = "diagnostic_operation"

        return {
            "universe": "stng" if should_use_stng else "warcraft",
            "persona": self.get_agent_persona(agent) if should_use_stng else None,
            "sounds": sounds,
            "trigger": trigger,
            "event": event,
            "context": context
        }


# =============================================================================
# Standalone Testing
# =============================================================================

if __name__ == "__main__":
    """Test STNG universe selection."""
    import sys

    stng = STNGUniverse()

    print("🌌 STNG Universe Module Test")
    print(f"✅ STNG Enabled: {stng.enabled}")
    print()

    # Test scenarios
    scenarios = [
        ("claude-code", "task_completed", {"analytical": True}, "Should use Data voice"),
        ("claude-code", "task_completed", {}, "Should use Warcraft default"),
        ("cursor-agent", "adr_approved", {}, "Should use Picard 'make it so'"),
        ("gemini-cli", "security_warning", {}, "Should use red alert"),
        ("claude-code", "handoff_received", {}, "Should use commbadge chirp"),
        ("claude-code", "git_push_production", {"production": True}, "Should use warp engage"),
    ]

    for agent, event, context, expected in scenarios:
        info = stng.get_sound_info(agent, event, context)
        print(f"📝 Scenario: {expected}")
        print(f"   Agent: {agent}, Event: {event}, Context: {context}")
        print(f"   Universe: {info['universe']}")
        print(f"   Trigger: {info['trigger']}")
        if info['sounds']:
            print(f"   Sounds: {info['sounds']}")
        print()

    sys.exit(0)
