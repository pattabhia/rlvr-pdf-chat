"""
LLM Port - Interface for Language Model implementations

This port allows swapping between different LLM backends:
- Ollama (local)
- AWS SageMaker/Inference Endpoint (custom trained model)
- HuggingFace Inference Endpoint
- OpenAI API
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    """
    Port for Language Model implementations.

    Any LLM adapter must implement this interface.
    """

    def invoke(self, prompt: str, temperature: float | None = None) -> str:
        """
        Invoke the language model with a prompt.

        Args:
            prompt: Input prompt text
            temperature: Optional temperature override for this invocation

        Returns:
            Generated response text
        """
        ...

    def get_model_name(self) -> str:
        """
        Get the model name/identifier.

        Returns:
            Model name string
        """
        ...

