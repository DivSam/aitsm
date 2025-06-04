from datetime import datetime
from simple_model import Comment, Assignee, CaseState, Priority, Component, Change
from langchain_core.tools import tool

# Global case store
case_store = {}

# Create assignees
webapp_dev = Assignee(
    id="dev001",
    name="Sarah Johnson", 
    email="sarah.j@company.com",
    department="WebApp Development"
)

applog_dev = Assignee(
    id="dev002",
    name="Mike Chen",
    email="mike.c@company.com", 
    department="AppLog Development"
)

support_agent = Assignee(
    id="support001",
    name="Alex Rodriguez",
    email="alex.r@company.com",
    department="Customer Support"
)

# Create additional assignees for different teams
api_dev = Assignee(
    id="dev003",
    name="Jennifer Martinez",
    email="jen.m@company.com",
    department="API Development"
)

database_admin = Assignee(
    id="dba001", 
    name="Robert Kim",
    email="robert.k@company.com",
    department="Database Administration"
)

security_analyst = Assignee(
    id="sec001",
    name="Emma Thompson", 
    email="emma.t@company.com",
    department="Security Team"
)

# Tool definitions
@tool
def check_past_cases():
    """ Check past cases that are similar to the current case via something like vector search."""
    # Return the historical resolved case for analysis
    return case_store["CASE-2025-001"]


@tool
def change_case_component(case_id: str, component: str):
    """ Change the component of the specified case. Use values: webapp, applog, api, database, other"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    case = case_store[case_id]
    old_component = case.component.value
    case.component = Component(component)
    case.change_history.append(Change(
        field="component",
        old_value=old_component,
        new_value=component,
        changed_at=datetime.now()
    ))
    return f"Changed component from {old_component} to {component} for case {case_id}"


@tool
def change_case_assignee(case_id: str, assignee_id: str):
    """ Change the assignee of the specified case. Use assignee IDs: dev001 (Sarah Johnson - WebApp), dev002 (Mike Chen - AppLog), dev003 (Jennifer Martinez - API), dba001 (Robert Kim - Database), sec001 (Emma Thompson - Security), support001 (Alex Rodriguez - Support)"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    case = case_store[case_id]
    old_assignee = case.assignee.name
    
    # Map assignee IDs to assignee objects
    assignee_map = {
        "dev001": webapp_dev,
        "dev002": applog_dev,
        "dev003": api_dev,
        "dba001": database_admin,
        "sec001": security_analyst,
        "support001": support_agent
    }
    
    if assignee_id not in assignee_map:
        return f"Invalid assignee ID: {assignee_id}"
    
    new_assignee = assignee_map[assignee_id]
    case.assignee = new_assignee
    case.change_history.append(Change(
        field="assignee",
        old_value=old_assignee,
        new_value=new_assignee.name,
        changed_at=datetime.now()
    ))

    return f"Changed assignee from {old_assignee} to {new_assignee.name} for case {case_id}"


@tool
def change_case_state(case_id: str, state: str):
    """ Change the state of the specified case. Use values: new, in_progress, awaiting_customer_info, resolved"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    case = case_store[case_id]
    old_state = case.state.value
    case.state = CaseState(state)
    case.change_history.append(Change(
        field="state",
        old_value=old_state,
        new_value=state,
        changed_at=datetime.now()
    ))
    return f"Changed state from {old_state} to {state} for case {case_id}"

@tool
def change_case_priority(case_id: str, priority: str):
    """ Change the priority of the specified case. Use values: low, medium, high, very_high"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    case = case_store[case_id]
    old_priority = case.priority.value
    case.priority = Priority(priority)
    case.change_history.append(Change(
        field="priority",
        old_value=old_priority,
        new_value=priority, 
        changed_at=datetime.now()
    ))
    return f"Changed priority from {old_priority} to {priority} for case {case_id}"

@tool
def add_comment(case_id: str, message: str):
    """ Add a comment to the specified case."""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    case = case_store[case_id]
    comment = Comment(
        id=f"AgentComment{len(case.comments) + 1}",
        content=message,
        author="AGENT",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    case.change_history.append(Change(
        field="comments",
        old_value=None,
        new_value=comment.content,
        changed_at=datetime.now()
    ))
    case.comments.append(comment)
    return f"Added comment to case {case_id}: {message}"

@tool
def review_app_design(case_id: str, message: str):
    """ Review the app design and suggest a workaround for the customer. In real life, you could have all the documentation for your app here"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    # Return the design limitation information for the agent to use
    return "DESIGN LIMITATION: Non-Admin users are not permitted to create new jobs. This is by design for security reasons. WORKAROUND: Please contact your administrator to either: 1) Grant you admin privileges, or 2) Have an admin create the job on your behalf."

@tool
def synthesize_comments(case_id: str, message: str):
    """ Synthesize all the comments into one comment. We assume that we have some logic in place to determine when this needs to be called depending on external vs internal message"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    return f"Here is the summary of the comments: \n\n {message}"

# List of all tools for easy import
ALL_TOOLS = [
    check_past_cases, 
    change_case_component, 
    change_case_assignee, 
    change_case_state, 
    change_case_priority, 
    add_comment, 
    review_app_design, 
    synthesize_comments
] 