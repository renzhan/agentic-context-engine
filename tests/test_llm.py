"""Tests for core LLM client abstractions."""

import unittest
from collections import deque

import pytest

from ace.llm import DummyLLMClient, LLMClient, LLMResponse


@pytest.mark.unit
class TestLLMResponse(unittest.TestCase):
    """Test LLMResponse dataclass."""

    def test_basic_response(self):
        """Test creating basic response."""
        response = LLMResponse(text="Hello world")
        self.assertEqual(response.text, "Hello world")
        self.assertIsNone(response.raw)

    def test_response_with_raw_data(self):
        """Test response with raw metadata."""
        raw_data = {"model": "gpt-4", "tokens": 100}
        response = LLMResponse(text="Answer", raw=raw_data)
        self.assertEqual(response.text, "Answer")
        self.assertEqual(response.raw, raw_data)


@pytest.mark.unit
class TestLLMClient(unittest.TestCase):
    """Test abstract LLMClient interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LLMClient cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            LLMClient()  # type: ignore[abstract]

    def test_subclass_must_implement_complete(self):
        """Test that subclass must implement complete method."""

        class IncompleteLLM(LLMClient):
            pass

        with self.assertRaises(TypeError):
            IncompleteLLM()  # type: ignore[abstract]

    def test_valid_subclass(self):
        """Test that valid subclass can be created."""

        class ValidLLM(LLMClient):
            def complete(self, prompt: str, **kwargs):
                return LLMResponse(text="test")

        client = ValidLLM(model="test-model")
        self.assertEqual(client.model, "test-model")
        response = client.complete("test")
        self.assertIsInstance(response, LLMResponse)


@pytest.mark.unit
class TestDummyLLMClient(unittest.TestCase):
    """Test DummyLLMClient for testing."""

    def test_initialization_empty(self):
        """Test initializing with no responses."""
        client = DummyLLMClient()
        self.assertEqual(client.model, "dummy")

    def test_initialization_with_responses(self):
        """Test initializing with pre-queued responses."""
        responses = deque(["response1", "response2"])
        client = DummyLLMClient(responses=responses)
        self.assertEqual(client.model, "dummy")

    def test_queue_single_response(self):
        """Test queuing a single response."""
        client = DummyLLMClient()
        client.queue("Hello")

        response = client.complete("test prompt")
        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.text, "Hello")

    def test_queue_multiple_responses(self):
        """Test queuing multiple responses in order."""
        client = DummyLLMClient()
        client.queue("First")
        client.queue("Second")
        client.queue("Third")

        self.assertEqual(client.complete("prompt1").text, "First")
        self.assertEqual(client.complete("prompt2").text, "Second")
        self.assertEqual(client.complete("prompt3").text, "Third")

    def test_complete_raises_when_empty(self):
        """Test that complete raises error when no responses queued."""
        client = DummyLLMClient()

        with self.assertRaises(RuntimeError) as ctx:
            client.complete("prompt")

        self.assertIn("ran out of queued responses", str(ctx.exception))

    def test_complete_with_kwargs(self):
        """Test that complete accepts kwargs (even if ignored)."""
        client = DummyLLMClient()
        client.queue("Response")

        response = client.complete(
            "prompt", temperature=0.5, max_tokens=100, custom_param="value"
        )
        self.assertEqual(response.text, "Response")

    def test_fifo_ordering(self):
        """Test that responses are returned in FIFO order."""
        client = DummyLLMClient()
        client.queue("A")
        client.queue("B")
        client.queue("C")

        # Dequeue in order
        self.assertEqual(client.complete("p1").text, "A")
        self.assertEqual(client.complete("p2").text, "B")
        self.assertEqual(client.complete("p3").text, "C")

    def test_queue_after_completion(self):
        """Test that we can queue more responses after completing some."""
        client = DummyLLMClient()
        client.queue("First")

        self.assertEqual(client.complete("p1").text, "First")

        # Now queue more
        client.queue("Second")
        client.queue("Third")

        self.assertEqual(client.complete("p2").text, "Second")
        self.assertEqual(client.complete("p3").text, "Third")

    def test_json_response(self):
        """Test returning JSON response."""
        client = DummyLLMClient()
        json_response = '{"answer": "42", "reasoning": "calculated"}'
        client.queue(json_response)

        response = client.complete("What is the answer?")
        self.assertEqual(response.text, json_response)

    def test_multiline_response(self):
        """Test returning multiline response."""
        client = DummyLLMClient()
        multiline = "Line 1\nLine 2\nLine 3"
        client.queue(multiline)

        response = client.complete("prompt")
        self.assertEqual(response.text, multiline)

    def test_empty_string_response(self):
        """Test that empty string is a valid response."""
        client = DummyLLMClient()
        client.queue("")

        response = client.complete("prompt")
        self.assertEqual(response.text, "")

    def test_initialization_from_list(self):
        """Test that we can initialize with a list (converted to deque)."""
        responses = ["r1", "r2", "r3"]
        client = DummyLLMClient(responses=deque(responses))

        self.assertEqual(client.complete("p1").text, "r1")
        self.assertEqual(client.complete("p2").text, "r2")
        self.assertEqual(client.complete("p3").text, "r3")


if __name__ == "__main__":
    unittest.main()
