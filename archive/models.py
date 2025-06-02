from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Priority levels for cases"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CaseState(str, Enum):
    """Possible states for a case"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    AWAITING_CUSTOMER_INFO = "awaiting_customer_info"
    RESOLVED = "resolved"


class ActionType(str, Enum):
    """Types of actions that can be performed on a case"""
    CREATED = "created"
    UPDATED = "updated"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    STATE_CHANGED = "state_changed"
    PRIORITY_CHANGED = "priority_changed"
    COMMENT_ADDED = "comment_added"
    RESOLVED = "resolved"


class BaseTimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Component(BaseModel):
    """Component model - represents a system component"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None


class Assignee(BaseModel):
    """Person who can be assigned to a case"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    department: Optional[str] = None


class Comment(BaseTimestampedModel):
    """Comment/conversation entry for a case"""
    id: UUID = Field(default_factory=uuid4)
    content: str
    author_id: UUID
    author_name: str
    is_internal: bool = False  # Whether this comment is internal or visible to customer


class ActionTimestamp(BaseModel):
    """Timestamp entry for actions performed on a case"""
    id: UUID = Field(default_factory=uuid4)
    action_type: ActionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    performed_by_id: Optional[UUID] = None
    performed_by_name: Optional[str] = None
    details: Optional[str] = None  # Additional details about the action
    old_value: Optional[str] = None  # Previous value (for updates)
    new_value: Optional[str] = None  # New value (for updates)


class CaseBase(BaseTimestampedModel):
    """Base Case model with all required fields"""
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    state: CaseState = CaseState.NEW
    component_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    
    # Related objects
    comments: List[Comment] = Field(default_factory=list)
    action_history: List[ActionTimestamp] = Field(default_factory=list)
    
    def add_comment(self, content: str, author_id: UUID, author_name: str, is_internal: bool = False) -> Comment:
        """Add a new comment to the case"""
        comment = Comment(
            content=content,
            author_id=author_id,
            author_name=author_name,
            is_internal=is_internal
        )
        self.comments.append(comment)
        
        # Add action timestamp
        self.add_action(
            ActionType.COMMENT_ADDED,
            performed_by_id=author_id,
            performed_by_name=author_name,
            details=f"Added {'internal' if is_internal else 'external'} comment"
        )
        
        return comment
    
    def add_action(self, action_type: ActionType, performed_by_id: Optional[UUID] = None, 
                  performed_by_name: Optional[str] = None, details: Optional[str] = None,
                  old_value: Optional[str] = None, new_value: Optional[str] = None) -> ActionTimestamp:
        """Add a new action timestamp to the case"""
        action = ActionTimestamp(
            action_type=action_type,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            details=details,
            old_value=old_value,
            new_value=new_value
        )
        self.action_history.append(action)
        self.updated_at = datetime.utcnow()
        return action
    
    def change_state(self, new_state: CaseState, performed_by_id: Optional[UUID] = None,
                    performed_by_name: Optional[str] = None) -> None:
        """Change the state of the case and log the action"""
        old_state = self.state.value
        self.state = new_state
        
        self.add_action(
            ActionType.STATE_CHANGED,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            details=f"State changed from {old_state} to {new_state.value}",
            old_value=old_state,
            new_value=new_state.value
        )
    
    def change_priority(self, new_priority: Priority, performed_by_id: Optional[UUID] = None,
                       performed_by_name: Optional[str] = None) -> None:
        """Change the priority of the case and log the action"""
        old_priority = self.priority.value
        self.priority = new_priority
        
        self.add_action(
            ActionType.PRIORITY_CHANGED,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            details=f"Priority changed from {old_priority} to {new_priority.value}",
            old_value=old_priority,
            new_value=new_priority.value
        )
    
    def assign_to(self, assignee_id: UUID, assignee_name: str, performed_by_id: Optional[UUID] = None,
                 performed_by_name: Optional[str] = None) -> None:
        """Assign the case to someone and log the action"""
        old_assignee = self.assignee_id
        self.assignee_id = assignee_id
        
        self.add_action(
            ActionType.ASSIGNED,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            details=f"Case assigned to {assignee_name}",
            old_value=str(old_assignee) if old_assignee else None,
            new_value=str(assignee_id)
        )
    
    def unassign(self, performed_by_id: Optional[UUID] = None,
                performed_by_name: Optional[str] = None) -> None:
        """Unassign the case and log the action"""
        old_assignee = self.assignee_id
        self.assignee_id = None
        
        self.add_action(
            ActionType.UNASSIGNED,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            details="Case unassigned",
            old_value=str(old_assignee) if old_assignee else None,
            new_value=None
        )


class Case(CaseBase):
    """Full Case model - can be extended with additional fields as needed"""
    
    # You can add additional fields here as the requirements evolve
    customer_id: Optional[UUID] = None
    customer_company: Optional[str] = None  # Company name of the customer
    tags: List[str] = Field(default_factory=list)
    external_reference: Optional[str] = None
    
    @classmethod
    def create_new(cls, title: str, description: Optional[str] = None, 
                  priority: Priority = Priority.MEDIUM, component_id: Optional[UUID] = None,
                  creator_id: Optional[UUID] = None, creator_name: Optional[str] = None,
                  customer_company: Optional[str] = None) -> "Case":
        """Create a new case with initial action timestamp"""
        case = cls(
            title=title,
            description=description,
            priority=priority,
            component_id=component_id,
            customer_company=customer_company
        )
        
        # Add creation action
        case.add_action(
            ActionType.CREATED,
            performed_by_id=creator_id,
            performed_by_name=creator_name,
            details=f"Case '{title}' created for {customer_company or 'unknown customer'}"
        )
        
        return case


# Example usage models for API requests/responses
class CreateCaseRequest(BaseModel):
    """Request model for creating a new case"""
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    component_id: Optional[UUID] = None
    customer_company: Optional[str] = None


class UpdateCaseRequest(BaseModel):
    """Request model for updating a case"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    state: Optional[CaseState] = None
    component_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None


class AddCommentRequest(BaseModel):
    """Request model for adding a comment to a case"""
    content: str
    is_internal: bool = False 