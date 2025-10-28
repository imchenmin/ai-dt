"""
API models for OpenAI-compatible interface
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class MessageRole(str, Enum):
    """Message roles for chat completion"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Chat message"""
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class ChatCompletionRequest:
    """OpenAI-compatible chat completion request"""
    messages: List[Message]
    model: str = "gpt-3.5-turbo"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatCompletionRequest':
        """Create request from dictionary"""
        messages = []
        for msg_data in data.get("messages", []):
            role = MessageRole(msg_data["role"])
            content = msg_data["content"]
            messages.append(Message(role=role, content=content))
        
        return cls(
            messages=messages,
            model=data.get("model", "gpt-3.5-turbo"),
            max_tokens=data.get("max_tokens"),
            temperature=data.get("temperature"),
            top_p=data.get("top_p"),
            n=data.get("n"),
            stream=data.get("stream", False),
            stop=data.get("stop"),
            presence_penalty=data.get("presence_penalty"),
            frequency_penalty=data.get("frequency_penalty"),
            logit_bias=data.get("logit_bias"),
            user=data.get("user")
        )


@dataclass
class Usage:
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Choice:
    """Chat completion choice"""
    index: int
    message: Message
    finish_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "message": self.message.to_dict(),
            "finish_reason": self.finish_reason
        }


@dataclass
class ChatCompletionResponse:
    """OpenAI-compatible chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: List[Choice] = None
    usage: Optional[Usage] = None
    
    def __post_init__(self):
        if self.choices is None:
            self.choices = []
        if self.created == 0:
            import time
            self.created = int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [choice.to_dict() for choice in self.choices],
            "usage": self.usage.to_dict() if self.usage else None
        }


@dataclass
class ErrorResponse:
    """Error response"""
    error: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def create(cls, message: str, type: str = "invalid_request_error", code: str = None) -> 'ErrorResponse':
        """Create error response"""
        error_data = {
            "message": message,
            "type": type
        }
        if code:
            error_data["code"] = code
        
        return cls(error=error_data)