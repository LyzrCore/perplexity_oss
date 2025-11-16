import os
from enum import Enum
from typing import List, Union

from dotenv import load_dotenv

from pydantic import BaseModel, Field

from utils import strtobool

load_dotenv()


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    content: str
    role: MessageRole


LOCAL_MODELS_ENABLED = strtobool(os.getenv("ENABLE_LOCAL_MODELS", False))


class ChatRequest(BaseModel):
    thread_id: int | None = None  # Deprecated: use session_id instead
    session_id: str | None = Field(
        default=None,
        description="Session ID for maintaining conversation history. If not provided, a new session will be created."
    )
    query: str
    # history parameter removed - Lyzr manages conversation history via session_id
    pro_search: bool = False
    time_range: str | None = None  # SearXNG time filter: "day", "week", "month", "year"
    start_date: str | None = Field(
        default=None,
        description="Start date for custom date range (format: YYYY-MM-DD). Appends 'after:' operator to query."
    )
    end_date: str | None = Field(
        default=None,
        description="End date for custom date range (format: YYYY-MM-DD). Appends 'before:' operator to query."
    )
    max_results: int = Field(default=10, ge=1, le=100)  # Number of results per query


class RelatedQueries(BaseModel):
    related_questions: List[str] = Field(..., min_length=3, max_length=3)


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    published_date: str | None = None  # Optional: backwards compatible

    def __str__(self):
        return f"Title: {self.title}\nURL: {self.url}\n Summary: {self.content}"


class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)


class AgentSearchStepStatus(str, Enum):
    DONE = "done"
    CURRENT = "current"
    DEFAULT = "default"


class AgentSearchStep(BaseModel):
    step_number: int
    step: str
    queries: List[str] = Field(default_factory=list)
    results: List[SearchResult] = Field(default_factory=list)
    status: AgentSearchStepStatus = AgentSearchStepStatus.DEFAULT


class AgentSearchFullResponse(BaseModel):
    steps: list[str] = Field(default_factory=list)
    steps_details: List[AgentSearchStep] = Field(default_factory=list)


class StreamEvent(str, Enum):
    BEGIN_STREAM = "begin-stream"
    SEARCH_RESULTS = "search-results"
    TEXT_CHUNK = "text-chunk"
    RELATED_QUERIES = "related-queries"
    STREAM_END = "stream-end"
    FINAL_RESPONSE = "final-response"
    ERROR = "error"
    RETRY_ATTEMPT = "retry-attempt"  # New: indicates a retry is being attempted

    # Agent Events
    AGENT_QUERY_PLAN = "agent-query-plan"
    AGENT_SEARCH_QUERIES = "agent-search-queries"
    AGENT_READ_RESULTS = "agent-read-results"
    AGENT_FINISH = "agent-finish"
    AGENT_FULL_RESPONSE = "agent-full-response"


class ChatObject(BaseModel):
    event_type: StreamEvent


class BeginStream(ChatObject):
    event_type: StreamEvent = StreamEvent.BEGIN_STREAM
    query: str


class SearchResultStream(ChatObject):
    event_type: StreamEvent = StreamEvent.SEARCH_RESULTS
    results: List[SearchResult] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)


class TextChunkStream(ChatObject):
    event_type: StreamEvent = StreamEvent.TEXT_CHUNK
    text: str


class RelatedQueriesStream(ChatObject):
    event_type: StreamEvent = StreamEvent.RELATED_QUERIES
    related_queries: List[str] = Field(default_factory=list)


class StreamEndStream(ChatObject):
    thread_id: int | None = None  # Deprecated: use session_id instead
    session_id: str | None = None
    event_type: StreamEvent = StreamEvent.STREAM_END


class FinalResponseStream(ChatObject):
    event_type: StreamEvent = StreamEvent.FINAL_RESPONSE
    message: str


class ErrorStream(ChatObject):
    event_type: StreamEvent = StreamEvent.ERROR
    detail: str


class AgentQueryPlanStream(ChatObject):
    event_type: StreamEvent = StreamEvent.AGENT_QUERY_PLAN
    steps: List[str] = Field(default_factory=list)


class AgentSearchQueriesStream(ChatObject):
    event_type: StreamEvent = StreamEvent.AGENT_SEARCH_QUERIES
    step_number: int
    queries: List[str] = Field(default_factory=list)


class AgentReadResultsStream(ChatObject):
    event_type: StreamEvent = StreamEvent.AGENT_READ_RESULTS
    step_number: int
    results: List[SearchResult] = Field(default_factory=list)


class AgentSearchFullResponseStream(ChatObject):
    event_type: StreamEvent = StreamEvent.AGENT_FULL_RESPONSE
    response: AgentSearchFullResponse


class AgentFinishStream(ChatObject):
    event_type: StreamEvent = StreamEvent.AGENT_FINISH


class RetryAttemptStream(ChatObject):
    """Event emitted when a retry attempt is being made"""
    event_type: StreamEvent = StreamEvent.RETRY_ATTEMPT
    attempt: int  # Current attempt number
    max_attempts: int  # Maximum number of attempts
    reason: str  # Reason for retry (e.g., "Connection error", "Timeout")
    delay_seconds: float  # Delay before next attempt


class ChatResponseEvent(BaseModel):
    event: StreamEvent
    data: Union[
        BeginStream,
        SearchResultStream,
        TextChunkStream,
        RelatedQueriesStream,
        StreamEndStream,
        FinalResponseStream,
        ErrorStream,
        RetryAttemptStream,
        AgentQueryPlanStream,
        AgentSearchQueriesStream,
        AgentReadResultsStream,
        AgentFinishStream,
        AgentSearchFullResponseStream,
    ]


class ChatMessage(BaseModel):
    content: str
    role: MessageRole
    related_queries: List[str] | None = None
    sources: List[SearchResult] | None = None
    images: List[str] | None = None
    is_error_message: bool = False
    agent_response: AgentSearchFullResponse | None = None
