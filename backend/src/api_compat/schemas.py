"""OpenAI-compatible API schemas for external integrations."""

import time
from enum import Enum
from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Chat message role"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Single chat message in OpenAI format"""
    role: MessageRole
    content: str


class ChatCompletionRequest(BaseModel):
    """
    OpenAI-compatible chat completion request.
    Supports both standard OpenAI params and our custom extensions.
    """
    # Required OpenAI fields
    model: str = Field(default="default", description="Model to use")
    messages: List[ChatMessage] = Field(..., description="Chat messages")

    # OpenAI streaming
    stream: bool = Field(default=False, description="Enable streaming responses")

    # OpenAI parameters (accepted but may not affect output)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    max_tokens: Optional[int] = Field(default=None, gt=0)

    # Perplexity-compatible search filters
    return_images: bool = Field(default=False, description="Include image results")
    return_related_questions: bool = Field(
        default=False,
        description="Include related follow-up questions"
    )
    search_domain_filter: Optional[List[str]] = Field(
        default=None,
        description="Limit search to specific domains"
    )
    search_recency_filter: Optional[Literal["day", "week", "month", "year"]] = Field(
        default=None,
        description="Filter by time range"
    )

    # Our custom extensions
    pro_search: bool = Field(
        default=False,
        description="Enable multi-step reasoning (Perplexity OSS extension)"
    )
    max_results: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Number of search results to use (Perplexity OSS extension)"
    )


class UsageInfo(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class SearchResultCompat(BaseModel):
    """Search result in compatibility format"""
    title: str
    url: str
    content: str = Field(alias="snippet")  # Accept both content and snippet

    class Config:
        populate_by_name = True  # Allow both field names


class ChatCompletionMessage(BaseModel):
    """Message in response"""
    role: MessageRole = MessageRole.ASSISTANT
    content: str


class ChatCompletionChoice(BaseModel):
    """Choice in non-streaming response"""
    index: int = 0
    message: ChatCompletionMessage
    finish_reason: Optional[Literal["stop", "length"]] = "stop"


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response (non-streaming)"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{int(time.time())}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo

    # Our extensions (not part of OpenAI spec)
    search_results: Optional[List[SearchResultCompat]] = None
    related_questions: Optional[List[str]] = None
    images: Optional[List[str]] = None


class ChatCompletionChunkDelta(BaseModel):
    """Delta content in streaming chunk"""
    role: Optional[MessageRole] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    """Choice in streaming chunk"""
    index: int = 0
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[Literal["stop", "length"]] = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk"""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
