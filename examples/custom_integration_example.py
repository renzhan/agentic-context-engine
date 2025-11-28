#!/usr/bin/env python3
"""
Minimal example of integrating ACE with a custom agentic system.

This demonstrates the core pattern without any external framework dependencies.
Shows how to wrap any agent with ACE learning capabilities.

Requirements:
    pip install ace-framework
    export OPENAI_API_KEY="your-key"
"""

from dataclasses import dataclass
from ace import Playbook, Reflector, Curator, LiteLLMClient
from ace.integrations.base import wrap_playbook_context
from ace.roles import GeneratorOutput


# Simulated custom agent (replace with your actual agent)
@dataclass
class AgentResult:
    output: str
    success: bool
    steps: int = 0


class MyCustomAgent:
    """Example custom agent - replace with your actual agent."""

    def execute(self, task: str) -> AgentResult:
        # Your agent logic here
        # This is just a placeholder
        return AgentResult(output=f"Processed: {task}", success=True, steps=1)


# ACE Wrapper for your custom agent
class ACEWrappedAgent:
    """
    Wraps any agent with ACE learning capabilities.

    Pattern:
    1. Inject playbook context before execution
    2. Execute agent normally
    3. Learn from results (Reflector + Curator)
    """

    def __init__(self, agent, ace_model: str = "gpt-4o-mini", is_learning: bool = True):
        self.agent = agent
        self.playbook = Playbook()
        self.is_learning = is_learning

        # Create ACE learning components
        self.llm = LiteLLMClient(model=ace_model, max_tokens=2048)
        self.reflector = Reflector(self.llm)
        self.curator = Curator(self.llm)

    def run(self, task: str) -> AgentResult:
        """Execute task with ACE learning."""
        # 1. Inject playbook context (if available)
        enhanced_task = task
        if self.is_learning and self.playbook.bullets():
            playbook_context = wrap_playbook_context(self.playbook)
            enhanced_task = f"{task}\n\n{playbook_context}"

        # 2. Execute agent
        result = self.agent.execute(enhanced_task)

        # 3. Learn from execution
        if self.is_learning:
            self._learn(task, result)

        return result

    def _learn(self, task: str, result: AgentResult):
        """Run ACE learning pipeline."""
        # Create adapter for Reflector (required interface)
        generator_output = GeneratorOutput(
            reasoning=f"Task: {task}",
            final_answer=result.output,
            bullet_ids=[],  # External agent, not using ACE Generator
            raw={"steps": result.steps, "success": result.success},
        )

        # Build feedback
        feedback = (
            f"Task {'succeeded' if result.success else 'failed'} "
            f"in {result.steps} steps.\n"
            f"Output: {result.output}"
        )

        # Reflect: Analyze what went right/wrong
        reflection = self.reflector.reflect(
            question=task,
            generator_output=generator_output,
            playbook=self.playbook,
            ground_truth=None,
            feedback=feedback,
        )

        # Curate: Generate playbook updates
        curator_output = self.curator.curate(
            reflection=reflection,
            playbook=self.playbook,
            question_context=f"task: {task}\nfeedback: {feedback}",
            progress=f"Task: {task}",
        )

        # Apply updates
        self.playbook.apply_delta(curator_output.delta)

    def save_playbook(self, path: str):
        """Save learned knowledge."""
        self.playbook.save_to_file(path)

    def load_playbook(self, path: str):
        """Load previously learned knowledge."""
        self.playbook = Playbook.load_from_file(path)


def main():
    print("🤖 Custom ACE Integration Example")
    print("=" * 50)

    # Create your custom agent
    my_agent = MyCustomAgent()

    # Wrap with ACE learning
    ace_agent = ACEWrappedAgent(my_agent, is_learning=True)

    # Run tasks - ACE learns from each
    tasks = ["Process user data", "Validate inputs", "Generate report"]

    for i, task in enumerate(tasks, 1):
        print(f"\n📋 Task {i}: {task}")
        result = ace_agent.run(task)
        print(f"✅ Result: {result.output}")
        print(f"📚 Learned {len(ace_agent.playbook.bullets())} strategies so far")

    # Show learned strategies
    print("\n" + "=" * 50)
    print("🎯 Learned Strategies:")
    print("=" * 50)
    for i, bullet in enumerate(ace_agent.playbook.bullets()[:5], 1):
        print(f"{i}. {bullet.content}")
        print(f"   Score: +{bullet.helpful}/-{bullet.harmful}\n")

    # Save for reuse
    ace_agent.save_playbook("custom_agent_learned.json")
    print("💾 Playbook saved to custom_agent_learned.json")
    print("\n✨ Next time, load this playbook to start with learned knowledge!")


if __name__ == "__main__":
    main()
