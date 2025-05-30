from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class Comment(BaseModel):
    id: str
    content: str
    author: str
    created_at: str
    updated_at: str


class Assignee(BaseModel):
    id: str
    name: str
    email: str
    department: str

class CaseState(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    AWAITING_CUSTOMER_INFO = "awaiting_customer_info"
    RESOLVED = "resolved"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class Component(str, Enum):
    WEBAPP = "webapp"
    APPLOG = "applog"
    API = "api"
    DATABASE = "database"
    OTHER = "other"

class Change(BaseModel):
    field: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime

class Case(BaseModel):
    id: str
    title: str
    description: str
    priority: Priority
    state: CaseState
    assignee: Assignee
    comments: list[Comment] = []
    component: Component
    created_at: datetime
    updated_at: datetime
    change_history: list[Change] = []

