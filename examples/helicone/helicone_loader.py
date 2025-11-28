"""
Helicone Data Loader for ACE Training

Loads and processes Helicone API observability logs for ACE training.
Extracts conversation traces, tool usage patterns, and performance metrics.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ToolCall:
    """Represents a single tool invocation"""

    turn_index: int
    tool_name: str
    tool_input: Dict[str, Any]
    tool_result: Optional[Dict[str, Any]] = None


@dataclass
class ConversationTurn:
    """Represents one turn in the conversation"""

    turn_index: int
    role: str  # 'user' or 'assistant'
    text_content: List[str]
    tool_calls: List[ToolCall]
    has_images: bool = False


@dataclass
class HeliconeTrace:
    """Complete trace from a Helicone log"""

    trace_id: str
    model: str
    provider: str
    created_at: str

    # Conversation data
    system_prompt: str
    conversation: List[ConversationTurn]

    # Performance metrics
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost: float
    delay_ms: int
    time_to_first_token: int

    # Metadata
    user_id: str
    cache_enabled: bool

    def get_tool_sequence(self) -> List[str]:
        """Get ordered list of all tool names used"""
        tools = []
        for turn in self.conversation:
            for tool_call in turn.tool_calls:
                tools.append(tool_call.tool_name)
        return tools

    def get_tool_stats(self) -> Dict[str, int]:
        """Get count of each tool used"""
        from collections import Counter

        return dict(Counter(self.get_tool_sequence()))

    def get_cache_effectiveness(self) -> float:
        """Calculate cache hit ratio"""
        if self.prompt_tokens == 0:
            return 0.0
        return (self.cache_read_tokens / self.prompt_tokens) * 100

    def get_cost_per_token(self) -> float:
        """Calculate cost per token"""
        if self.total_tokens == 0:
            return 0.0
        return self.cost / self.total_tokens


class HeliconeLoader:
    """Loads and processes Helicone API logs"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self) -> HeliconeTrace:
        """Load a single Helicone trace from JSON file"""
        with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.loads(f.read(), strict=False)

        return self._parse_trace(data)

    def _parse_trace(self, data: Dict[str, Any]) -> HeliconeTrace:
        """Parse raw JSON data into HeliconeTrace object"""

        # Extract basic info
        trace_id = data.get("response_id", "")
        model = data.get("model", "")
        provider = data.get("provider", "")
        created_at = data.get("request_created_at", "")

        # Extract request body
        request_body = data.get("request_body", {})

        # Extract system prompt
        system = request_body.get("system", [])
        system_prompt = ""
        if isinstance(system, list) and len(system) > 0:
            if isinstance(system[0], dict):
                system_prompt = system[0].get("text", "")

        # Parse conversation messages
        messages = request_body.get("messages", [])
        conversation = self._parse_messages(messages)

        # Extract performance metrics
        response_body = data.get("response_body", {})
        usage = response_body.get("usage", {})

        total_tokens = int(data.get("total_tokens", 0))
        prompt_tokens = int(data.get("prompt_tokens", 0))
        completion_tokens = int(data.get("completion_tokens", 0))
        cache_read_tokens = int(data.get("prompt_cache_read_tokens", 0))
        cache_write_tokens = int(data.get("prompt_cache_write_tokens", 0))
        cost = float(data.get("cost", 0.0))
        delay_ms = int(data.get("delay_ms", 0))
        time_to_first_token = int(data.get("time_to_first_token", 0))

        # Extract metadata
        user_id = data.get("request_user_id", "")
        cache_enabled = bool(data.get("cache_enabled", False))

        return HeliconeTrace(
            trace_id=trace_id,
            model=model,
            provider=provider,
            created_at=created_at,
            system_prompt=system_prompt,
            conversation=conversation,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            cost=cost,
            delay_ms=delay_ms,
            time_to_first_token=time_to_first_token,
            user_id=user_id,
            cache_enabled=cache_enabled,
        )

    def _parse_messages(self, messages: List[Dict[str, Any]]) -> List[ConversationTurn]:
        """Parse messages into ConversationTurn objects"""
        turns = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", [])

            text_blocks = []
            tool_calls = []
            has_images = False

            # Handle string content
            if isinstance(content, str):
                text_blocks.append(content)
            # Handle list content
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue

                    block_type = block.get("type", "")

                    if block_type == "text":
                        text_blocks.append(block.get("text", ""))

                    elif block_type == "image":
                        has_images = True

                    elif block_type == "tool_use":
                        tool_call = ToolCall(
                            turn_index=i,
                            tool_name=block.get("name", "unknown"),
                            tool_input=block.get("input", {}),
                        )
                        tool_calls.append(tool_call)

                    elif block_type == "tool_result":
                        # Tool results come in the next user message
                        # We'll link them later if needed
                        pass

            turn = ConversationTurn(
                turn_index=i,
                role=role,
                text_content=text_blocks,
                tool_calls=tool_calls,
                has_images=has_images,
            )
            turns.append(turn)

        return turns

    def extract_training_samples(self, trace: HeliconeTrace) -> List[Dict[str, Any]]:
        """
        Extract training samples for ACE from the trace.
        Each sample represents a decision point where the agent chose an action.
        """
        samples = []

        for turn in trace.conversation:
            if turn.role == "assistant" and turn.tool_calls:
                # This is a decision point - the agent chose to use tools

                # Get context: what came before this decision
                context_turns = [
                    t for t in trace.conversation if t.turn_index < turn.turn_index
                ]

                for tool_call in turn.tool_calls:
                    sample = {
                        "turn_index": turn.turn_index,
                        "system_prompt": trace.system_prompt,
                        "conversation_history": context_turns,
                        "decision": {
                            "tool_name": tool_call.tool_name,
                            "tool_input": tool_call.tool_input,
                        },
                        "context": {
                            "previous_tools": [
                                tc.tool_name
                                for t in context_turns
                                for tc in t.tool_calls
                            ],
                            "turn_count": len(context_turns),
                        },
                    }
                    samples.append(sample)

        return samples


def main():
    """Demo: Load and analyze a Helicone trace"""
    import os

    # Data files are stored in .private/helicone/ to keep them out of the repo
    # Place your Helicone JSON export in: ../../.private/helicone/oneline.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "../../.private/helicone/oneline.json")

    loader = HeliconeLoader(json_path)
    trace = loader.load()

    print("=" * 80)
    print("HELICONE TRACE LOADED")
    print("=" * 80)
    print(f"\nTrace ID: {trace.trace_id}")
    print(f"Model: {trace.model}")
    print(f"Provider: {trace.provider}")
    print(f"Created: {trace.created_at}")

    print(f"\n📊 CONVERSATION STATS")
    print(f"   Total turns: {len(trace.conversation)}")
    print(f"   System prompt: {len(trace.system_prompt)} chars")

    print(f"\n🔧 TOOL USAGE")
    tool_stats = trace.get_tool_stats()
    for tool, count in sorted(tool_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {tool}: {count} calls")

    print(f"\n💰 PERFORMANCE")
    print(f"   Total tokens: {trace.total_tokens:,}")
    print(f"   Cost: ${trace.cost:.4f}")
    print(f"   Cost per token: ${trace.get_cost_per_token():.6f}")
    print(f"   Cache effectiveness: {trace.get_cache_effectiveness():.1f}%")
    print(f"   Latency: {trace.delay_ms}ms")

    print(f"\n🎯 TRAINING SAMPLES")
    samples = loader.extract_training_samples(trace)
    print(f"   Extracted {len(samples)} training samples")

    if samples:
        print(f"\n   First sample:")
        first = samples[0]
        print(f"      Turn: {first['turn_index']}")
        print(f"      Tool: {first['decision']['tool_name']}")
        print(f"      Previous tools: {first['context']['previous_tools']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
