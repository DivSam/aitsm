#!/usr/bin/env python3
"""
Example usage of the Case management pydantic models.
This demonstrates how to create cases, add comments, change states, etc.
"""

from uuid import uuid4
from models import (
    Case, Priority, CaseState, Component, Assignee,
    CreateCaseRequest, AddCommentRequest
)


def main():
    # Create some example components and assignees
    web_component = Component(
        name="Web Frontend",
        description="React-based web application frontend"
    )
    
    api_component = Component(
        name="API Backend", 
        description="Python FastAPI backend service"
    )
    
    john_doe = Assignee(
        name="John Doe",
        email="john.doe@company.com",
        department="Engineering"
    )
    
    jane_smith = Assignee(
        name="Jane Smith",
        email="jane.smith@company.com", 
        department="Customer Support"
    )
    
    # Create a new case
    print("=== Creating a new case ===")
    case = Case.create_new(
        title="Login page not loading",
        description="Users are reporting that the login page is not loading properly",
        priority=Priority.HIGH,
        component_id=web_component.id,
        creator_id=jane_smith.id,
        creator_name=jane_smith.name
    )
    
    print(f"Created case: {case.id}")
    print(f"Title: {case.title}")
    print(f"Priority: {case.priority}")
    print(f"State: {case.state}")
    print(f"Actions so far: {len(case.action_history)}")
    
    # Assign the case
    print("\n=== Assigning the case ===")
    case.assign_to(
        assignee_id=john_doe.id,
        assignee_name=john_doe.name,
        performed_by_id=jane_smith.id,
        performed_by_name=jane_smith.name
    )
    
    print(f"Case assigned to: {john_doe.name}")
    print(f"Actions so far: {len(case.action_history)}")
    
    # Change state to in progress
    print("\n=== Changing state to In Progress ===")
    case.change_state(
        new_state=CaseState.IN_PROGRESS,
        performed_by_id=john_doe.id,
        performed_by_name=john_doe.name
    )
    
    print(f"Case state: {case.state}")
    
    # Add some comments
    print("\n=== Adding comments ===")
    case.add_comment(
        content="I'm looking into this issue. Checking server logs now.",
        author_id=john_doe.id,
        author_name=john_doe.name,
        is_internal=True
    )
    
    case.add_comment(
        content="We've identified the issue and are working on a fix. Expected resolution in 2 hours.",
        author_id=john_doe.id,
        author_name=john_doe.name,
        is_internal=False  # External comment visible to customer
    )
    
    print(f"Comments added: {len(case.comments)}")
    print("Latest comment:", case.comments[-1].content)
    
    # Change priority
    print("\n=== Changing priority ===")
    case.change_priority(
        new_priority=Priority.VERY_HIGH,
        performed_by_id=jane_smith.id,
        performed_by_name=jane_smith.name
    )
    
    print(f"New priority: {case.priority}")
    
    # Resolve the case
    print("\n=== Resolving the case ===")
    case.change_state(
        new_state=CaseState.RESOLVED,
        performed_by_id=john_doe.id,
        performed_by_name=john_doe.name
    )
    
    case.add_comment(
        content="Issue has been resolved. The login page is now working correctly.",
        author_id=john_doe.id,
        author_name=john_doe.name,
        is_internal=False
    )
    
    print(f"Case resolved! Final state: {case.state}")
    
    # Print full action history
    print("\n=== Full Action History ===")
    for i, action in enumerate(case.action_history, 1):
        print(f"{i}. {action.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"{action.action_type.value} by {action.performed_by_name or 'System'}")
        if action.details:
            print(f"   Details: {action.details}")
        if action.old_value and action.new_value:
            print(f"   Changed from '{action.old_value}' to '{action.new_value}'")
    
    # Print all comments
    print("\n=== All Comments ===")
    for i, comment in enumerate(case.comments, 1):
        visibility = "Internal" if comment.is_internal else "External"
        print(f"{i}. [{visibility}] {comment.created_at.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"{comment.author_name}:")
        print(f"   {comment.content}")
    
    # Demonstrate JSON serialization
    print("\n=== JSON Serialization ===")
    case_json = case.model_dump_json(indent=2)
    print("Case can be serialized to JSON:")
    print(case_json[:200] + "..." if len(case_json) > 200 else case_json)
    
    # Demonstrate validation with requests
    print("\n=== API Request Models ===")
    create_request = CreateCaseRequest(
        title="New case from API",
        description="This case was created via API request",
        priority=Priority.MEDIUM,
        component_id=api_component.id
    )
    print(f"Create request: {create_request.model_dump()}")
    
    comment_request = AddCommentRequest(
        content="This is a comment from the API",
        is_internal=False
    )
    print(f"Comment request: {comment_request.model_dump()}")


if __name__ == "__main__":
    main() 