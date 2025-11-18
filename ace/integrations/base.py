"""
Base classes and utilities for ACE integrations with external agentic frameworks.

This module provides the foundation for integrating ACE learning capabilities
with external agentic systems like browser-use, LangChain, CrewAI, etc.

Integration Pattern:
    1. External framework executes task (no ACE Generator)
    2. ACE injects playbook context beforehand (via wrap_playbook_context)
    3. ACE learns from execution afterward (Reflector + Curator)

Example:
    from ace.integrations.base import wrap_playbook_context
    from ace import Playbook

    playbook = Playbook()
    # ... playbook gets populated with bullets ...

    # Inject context into external agent's task
    task_with_context = f"{task}\\n\\n{wrap_playbook_context(playbook)}"
"""

from ..playbook import Playbook
from ..prompts_v2_1 import wrap_playbook_for_external_agent


def wrap_playbook_context(playbook: Playbook) -> str:
    """
    Wrap playbook bullets with explanation for external agents.

    This helper formats learned strategies from the playbook with instructions
    on how to apply them. Delegates to the canonical implementation in
    prompts_v2_1 to ensure consistency across all ACE components.

    The formatted output includes:
    - Header explaining these are learned strategies
    - List of bullets with success rates (helpful/harmful scores)
    - Usage instructions on how to apply strategies
    - Reminder that these are patterns, not rigid rules

    Args:
        playbook: Playbook with learned strategies

    Returns:
        Formatted text explaining playbook and listing strategies.
        Returns empty string if playbook has no bullets.

    Example:
        >>> playbook = Playbook()
        >>> playbook.add_bullet("general", "Always verify inputs")
        >>> context = wrap_playbook_context(playbook)
        >>> enhanced_task = f"{task}\\n\\n{context}"

    Note:
        This function delegates to wrap_playbook_for_external_agent() in
        prompts_v2_1 module, which is the single source of truth for
        playbook presentation. Kept here for backward compatibility.
    """
    return wrap_playbook_for_external_agent(playbook)


__all__ = ["wrap_playbook_context"]
