"""Base LLM interface for the Lyzr Agent-powered application."""

from abc import ABC, abstractmethod
from typing import TypeVar, AsyncIterator
from pydantic import BaseModel


# Simple completion response type
class CompletionResponse(BaseModel):
    text: str = ""
    delta: str = ""


# Type alias for async generator
CompletionResponseAsyncGen = AsyncIterator[CompletionResponse]

T = TypeVar("T")


class BaseLLM(ABC):
    """Abstract base class for LLM implementations."""

    @abstractmethod
    async def astream(self, prompt: str) -> CompletionResponseAsyncGen:
        """Stream completion responses asynchronously."""
        pass

    @abstractmethod
    def complete(self, prompt: str) -> CompletionResponse:
        """Get a single completion response."""
        pass

    @abstractmethod
    def structured_complete(self, response_model: type[T], prompt: str) -> T:
        """Get a structured completion response matching a Pydantic model."""
        pass
