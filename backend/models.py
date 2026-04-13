from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SessionStatus(str, Enum):
    IDLE = "idle"
    DEBATING = "debating"
    COMPLETED = "completed"


class DebaterRole(str, Enum):
    ADVOCATE = "Advocate"
    CRITIC = "Critic"
    RESEARCHER = "Researcher"
    DEVILS_ADVOCATE = "Devil's Advocate"
    JUDGE = "Judge"


AVAILABLE_MODELS = [
    # OpenAI
    "gpt-5.4-pro",
    "gpt-5.4-mini",
    "gpt-4o",
    "gpt-4o-mini",
    # Anthropic
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-3.5-sonnet",
    # Google
    "gemini-3.1-pro",
    "gemini-3-flash",
    "gemini-2.5-flash-lite",
    # Llama (via Groq)
    "llama-4-maverick",
    "llama-4-scout",
    "llama-3.3-70b",
    # MiniMax
    "minimax-m2.7",
    "minimax-m2.5-lightning",
]

# LiteLLM model mapping
MODEL_MAP = {
    "gpt-5.4-pro": "openai/gpt-5.4-pro",
    "gpt-5.4-mini": "openai/gpt-5.4-mini",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "claude-opus-4-6": "anthropic/claude-opus-4-6",
    "claude-sonnet-4-6": "anthropic/claude-sonnet-4-6",
    "claude-haiku-4-5": "anthropic/claude-haiku-4-5",
    "claude-3.5-sonnet": "anthropic/claude-3-5-sonnet-20241022",
    "gemini-3.1-pro": "gemini/gemini-3.1-pro",
    "gemini-3-flash": "gemini/gemini-3-flash",
    "gemini-2.5-flash-lite": "gemini/gemini-2.5-flash-lite",
    "llama-4-maverick": "groq/meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-4-scout": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b": "groq/llama-3.3-70b-versatile",
    "minimax-m2.7": "minimax/MiniMax-M2.7",
    "minimax-m2.5-lightning": "minimax/MiniMax-M2.5-lightning",
}


class CreateSessionRequest(BaseModel):
    model: str = "gpt-4o"


class RenameSessionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class StartDebateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=1000)
    model: Optional[str] = None
    rounds: int = Field(default=2, ge=1, le=5)


class SessionResponse(BaseModel):
    id: int
    name: str
    session_number: int
    model: str
    topic: Optional[str]
    status: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: str
