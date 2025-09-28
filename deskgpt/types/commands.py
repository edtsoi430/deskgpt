"""
Type definitions for DeskGPT commands and results
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class ActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"


class ScrollDirection(str, Enum):
    UP = "up"
    DOWN = "down"


class ExtractType(str, Enum):
    TEXT = "text"
    HTML = "html"
    LINKS = "links"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WebAction(BaseModel):
    type: ActionType
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    wait_time: Optional[int] = None
    scroll_direction: Optional[ScrollDirection] = None
    extract_type: Optional[ExtractType] = None


class CommandResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot: Optional[str] = None


class AutomationTask(BaseModel):
    id: str
    prompt: str
    actions: List[WebAction] = []
    results: List[CommandResult] = []
    status: TaskStatus = TaskStatus.PENDING