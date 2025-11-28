#!/usr/bin/env python3
"""
LangChain agent with tools + ACE learning example.

This example demonstrates how to wrap a LangChain agent with tools using ACELangChain.
The agent learns from tool usage patterns and multi-step reasoning.

Requirements:
    pip install ace-framework[langchain]
    # or: pip install langchain-core langchain-openai langchain-community

Environment:
    export OPENAI_API_KEY="your-api-key"
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check availability
try:
    from ace.integrations import ACELangChain, LANGCHAIN_AVAILABLE

    if not LANGCHAIN_AVAILABLE:
        print("LangChain is not installed.")
        print("Install with: pip install ace-framework[langchain]")
        exit(1)
except ImportError:
    print("ACE framework not installed.")
    print("Install with: pip install ace-framework")
    exit(1)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# Define custom tools
@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


@tool
def get_word_length(word: str) -> int:
    """Get the length of a word."""
    return len(word)


def example_agent_with_tools():
    """Example 1: Agent with math tools and ACE learning."""
    print("\n" + "=" * 60)
    print("Example 1: Agent with Tools")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Note: This example shows the pattern, but requires additional LangChain packages
    # For a fully functional agent, you'd need to use LangChain's agent framework
    # Here we show a simplified chain that demonstrates the ACE integration

    # Create a simple prompt chain (in practice, use create_tool_calling_agent)
    prompt = ChatPromptTemplate.from_template(
        """You are a helpful assistant. Answer the question: {input}

Available tools:
- add(a, b): Add two numbers
- multiply(a, b): Multiply two numbers
- get_word_length(word): Get length of a word

Think step by step and use tools as needed."""
    )

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    chain = prompt | llm

    # Wrap with ACE
    ace_agent = ACELangChain(runnable=chain, ace_model="gpt-4o-mini", is_learning=True)

    # Test questions
    questions = [
        "What is 23 + 45?",
        "Calculate 12 * 7",
        "How long is the word 'anthropic'?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        result = ace_agent.invoke({"input": question})
        print(f"Response: {result.content[:150]}...")

    print(f"\nLearned {len(ace_agent.playbook.bullets())} strategies")
    ace_agent.save_playbook("agent_with_tools_learned.json")


def example_multi_step_reasoning():
    """Example 2: Agent learning multi-step reasoning patterns."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Step Reasoning")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create a chain that encourages step-by-step thinking
    prompt = ChatPromptTemplate.from_template(
        """Break down the problem and solve step by step:

Problem: {input}

Think through each step carefully."""
    )

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    chain = prompt | llm

    # Wrap with ACE
    ace_agent = ACELangChain(runnable=chain, ace_model="gpt-4o-mini")

    # Complex questions requiring multiple steps
    questions = [
        "If a store sells 15 apples per hour and is open for 8 hours, how many apples does it sell?",
        "A train travels at 60 mph for 2.5 hours. How far does it go?",
        "If you have 3 boxes with 12 items each, and you remove 5 items total, how many remain?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        result = ace_agent.invoke({"input": question})
        print(f"Response: {result.content[:200]}...")

    print(f"\nLearned {len(ace_agent.playbook.bullets())} reasoning strategies")


def example_string_input():
    """Example 3: Using string input instead of dict."""
    print("\n" + "=" * 60)
    print("Example 3: String Input Format")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create a simple LLM (without prompt template)
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

    # Wrap with ACE
    ace_agent = ACELangChain(runnable=llm, ace_model="gpt-4o-mini")

    # Use string input directly
    questions = [
        "What is the capital of Japan?",
        "Explain photosynthesis in one sentence.",
        "What is the speed of light?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        result = ace_agent.invoke(question)  # String input
        print(f"Answer: {result.content}")

    print(f"\nLearned {len(ace_agent.playbook.bullets())} strategies")


def example_learning_from_failures():
    """Example 4: Learning from execution failures."""
    print("\n" + "=" * 60)
    print("Example 4: Learning from Failures")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create a chain
    prompt = ChatPromptTemplate.from_template("Answer concisely: {input}")
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    chain = prompt | llm

    # Wrap with ACE
    ace_agent = ACELangChain(runnable=chain, ace_model="gpt-4o-mini")

    print("Initial strategies:", len(ace_agent.playbook.bullets()))

    # First question - normal execution
    print("\nNormal execution:")
    result = ace_agent.invoke({"input": "What is 2+2?"})
    print(f"Answer: {result.content}")
    print("Strategies after success:", len(ace_agent.playbook.bullets()))

    # Note: ACE learns from both successes and failures
    # In a real scenario with tool-using agents, failures might include:
    # - Tool not found errors
    # - Invalid tool parameters
    # - Execution timeouts
    # ACE captures these patterns and learns to avoid them


async def example_async_agent():
    """Example 5: Async agent execution with ACE."""
    print("\n" + "=" * 60)
    print("Example 5: Async Agent Execution")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create chain
    prompt = ChatPromptTemplate.from_template("Provide a detailed answer: {input}")
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    chain = prompt | llm

    # Wrap with ACE
    ace_agent = ACELangChain(runnable=chain, ace_model="gpt-4o-mini")

    # Async execution
    questions = [
        "What are the benefits of async programming?",
        "Explain how neural networks learn.",
        "What is the difference between REST and GraphQL?",
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        result = await ace_agent.ainvoke({"input": question})
        print(f"Answer: {result.content[:150]}...")


def main():
    """Run all examples."""
    print("=" * 60)
    print("LangChain Agent + Tools + ACE Examples")
    print("=" * 60)

    # Run sync examples
    example_agent_with_tools()
    example_multi_step_reasoning()
    example_string_input()
    example_learning_from_failures()

    # Run async example
    import asyncio

    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(example_async_agent())

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check learned strategies in playbook JSON files")
    print("2. Experiment with your own chains and agents")
    print("3. See docs/INTEGRATION_GUIDE.md for more patterns")


if __name__ == "__main__":
    main()
