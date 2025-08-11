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
    thread_id: int | None = None
    query: str
    history: List[Message] = Field(default_factory=list)
    pro_search: bool = False


class RelatedQueries(BaseModel):
    related_questions: List[str] = Field(..., min_length=3, max_length=3)


class SearchResult(BaseModel):
    title: str
    url: str
    content: str

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
    thread_id: int | None = None
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
