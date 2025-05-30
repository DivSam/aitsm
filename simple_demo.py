from dotenv import load_dotenv
from datetime import datetime, timedelta
from simple_model import Case, Comment, Assignee, CaseState, Priority, Component, Change
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph, START


load_dotenv()

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

# Create timeline
case_created = datetime.now() - timedelta(days=4)
investigation_start = case_created + timedelta(hours=2)
component_change = case_created + timedelta(days=1, hours=6)
resolution = case_created + timedelta(days=3)

# Create the case
case = Case(
    id="CASE-2025-001",
    title="WebApp Hangs When Clicking Run Job Button",
    description="Customer reports that clicking the 'run job' button causes the entire web application to hang and become unresponsive. This makes the app completely unusable for their business operations.",
    priority=Priority.HIGH,
    state=CaseState.RESOLVED,
    assignee=applog_dev,  # Final assignee after investigation
    component=Component.APPLOG,  # Final component after investigation
    created_at=case_created,
    updated_at=resolution,
    comments=[
        Comment(
            id="comment001",
            content="Initial report received from customer. WebApp freezes when 'run job' button is clicked. Assigning to WebApp development team for initial investigation.",
            author=support_agent.name,
            created_at=case_created.isoformat(),
            updated_at=case_created.isoformat()
        ),
        Comment(
            id="comment002", 
            content="Started investigation. Checking WebApp frontend code and button click handlers. Initial tests show button click triggers but app becomes unresponsive.",
            author=webapp_dev.name,
            created_at=investigation_start.isoformat(),
            updated_at=investigation_start.isoformat()
        ),
        Comment(
            id="comment003",
            content="WebApp frontend code appears correct. Button click successfully initiates job process. However, discovered that app hangs occur when job tries to write logs. Suspecting AppLog component issue. Reassigning to AppLog team.",
            author=webapp_dev.name,
            created_at=component_change.isoformat(),
            updated_at=component_change.isoformat()
        ),
        Comment(
            id="comment004",
            content="Investigation confirmed: AppLog component has a deadlock issue when multiple log entries are written simultaneously during job execution. This causes the entire application to hang waiting for log writes to complete.",
            author=applog_dev.name,
            created_at=(component_change + timedelta(hours=4)).isoformat(),
            updated_at=(component_change + timedelta(hours=4)).isoformat()
        ),
        Comment(
            id="comment005",
            content="Fix implemented: Updated AppLog component to use async logging with proper queue management. Deployed to production. Customer confirmed 'run job' button now works correctly without hanging.",
            author=applog_dev.name,
            created_at=resolution.isoformat(),
            updated_at=resolution.isoformat()
        )
    ],
    change_history=[
        Change(
            field="state",
            old_value="new",
            new_value="in_progress", 
            changed_at=investigation_start
        ),
        Change(
            field="assignee",
            old_value=webapp_dev.name,
            new_value=applog_dev.name,
            changed_at=component_change
        ),
        Change(
            field="component",
            old_value="webapp",
            new_value="applog",
            changed_at=component_change
        ),
        Change(
            field="state",
            old_value="in_progress",
            new_value="resolved",
            changed_at=resolution
        )
    ]
)

# Add to store
case_store[case.id] = case

print("="*80)
print("📋 CASE CREATED: WebApp Run Job Button Issue")
print("="*80)

print(f"📝 CASE DETAILS:")
print(f"   ID: {case.id}")
print(f"   Title: {case.title}")
print(f"   Description: {case.description}")
print(f"   Priority: {case.priority.value.upper()}")
print(f"   Final State: {case.state.value.upper()}")
print(f"   Final Component: {case.component.value.upper()}")
print(f"   Final Assignee: {case.assignee.name} ({case.assignee.department})")
print(f"   Created: {case.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Resolved: {case.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

print(f"\n📅 CHANGE HISTORY ({len(case.change_history)} changes):")
for i, change in enumerate(case.change_history):
    print(f"   {i+1}. [{change.changed_at.strftime('%Y-%m-%d %H:%M:%S')}] {change.field.upper()}")
    print(f"      └─ Changed from '{change.old_value}' to '{change.new_value}'")

print(f"\n💬 COMMENTS ({len(case.comments)} comments):")
for i, comment in enumerate(case.comments):
    comment_time = datetime.fromisoformat(comment.created_at).strftime('%Y-%m-%d %H:%M:%S')
    print(f"   {i+1}. [{comment_time}] {comment.author}")
    print(f"      └─ {comment.content}")

print(f"\n👥 TEAM MEMBERS INVOLVED:")
print(f"   📞 {support_agent.name} ({support_agent.department}) - Initial case handling")
print(f"   🌐 {webapp_dev.name} ({webapp_dev.department}) - Initial investigation")
print(f"   📊 {applog_dev.name} ({applog_dev.department}) - Root cause analysis & resolution")

print(f"\n🔍 CASE SUMMARY:")
print(f"   • Initial Report: WebApp hanging on 'run job' button click")
print(f"   • Initial Assignment: WebApp Development (frontend investigation)")
print(f"   • Root Cause Discovery: AppLog component deadlock during concurrent logging")
print(f"   • Component Reassignment: WebApp → AppLog")
print(f"   • Resolution: Async logging with queue management implemented")
print(f"   • Customer Outcome: 'Run job' button now works correctly")

print("\n" + "="*80)
print("✅ CASE RESOLUTION COMPLETED")
print("="*80)






incoming_case = Case(
    id="CASE-2024-002",  # Different ID from the historical case
    title="WebApp Hangs When Clicking Run Job Button",
    description="Customer reports that clicking the 'run job' button causes the entire web application to hang and become unresponsive. This makes the app completely unusable for their business operations.",
    priority=Priority.HIGH,
    state=CaseState.NEW,
    assignee=webapp_dev,
    component=Component.WEBAPP,
    created_at=case_created,
    updated_at=case_created,
    comments=[],
    change_history=[]
)

# Store the incoming case in the case store
case_store[incoming_case.id] = incoming_case


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
    """ Change the assignee of the specified case. Use assignee IDs: dev001 (Sarah Johnson - WebApp), dev002 (Mike Chen - AppLog), support001 (Alex Rodriguez - Support)"""
    if case_id not in case_store:
        return f"Case {case_id} not found"
    
    case = case_store[case_id]
    old_assignee = case.assignee.name
    
    # Map assignee IDs to assignee objects
    assignee_map = {
        "dev001": webapp_dev,
        "dev002": applog_dev,
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



llm = init_chat_model(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools([check_past_cases, change_case_component, change_case_assignee, change_case_state, change_case_priority, add_comment])
tool_node = ToolNode(tools=[check_past_cases, change_case_component, change_case_assignee, change_case_state, change_case_priority, add_comment])


class State(TypedDict):
    messages: Annotated[list, add_messages]


def agent(state: State) -> State:
    system_prompt = """You are an IT Service Management (ITSM) assistant. Your job is to help customers with their support cases.
    You have the following tools at your disposal:
    - check_past_cases: Check past cases that are similar to the current case via something like vector search.
    - change_case_component: Change the component of the current case.
    - change_case_assignee: Change the assignee of the current case.
    - change_case_state: Change the state of the current case.
    - change_case_priority: Change the priority of the current case.
    - add_comment: Add a comment to the current case.

    You will be given a case and a message from a customer. You will need to use the tools to help the customer.
    
    You will also have access to the following assignees:
    - {webapp_dev.name} ({webapp_dev.department}) - WebApp Development
    - {applog_dev.name} ({applog_dev.department}) - AppLog Development
    - {support_agent.name} ({support_agent.department}) - Customer Support

    You will also have access to the following components:
    - {Component.WEBAPP} - WebApp
    - {Component.APPLOG} - AppLog
    - {Component.API} - API
    - {Component.DATABASE} - Database
    - {Component.OTHER} - Other

    You will also have access to the following priorities:
    - {Priority.LOW} - Low
    - {Priority.MEDIUM} - Medium - {Priority.HIGH} - High - {Priority.VERY_HIGH} - Very High You will also have access to the following states: - {CaseState.NEW} - New - {CaseState.IN_PROGRESS} - In Progress
    - {CaseState.AWAITING_CUSTOMER_INFO} - Awaiting Customer Info
    - {CaseState.RESOLVED} - Resolved
    """.format(webapp_dev=webapp_dev, applog_dev=applog_dev, support_agent=support_agent, Component=Component, Priority=Priority, CaseState=CaseState)

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def should_continue(state: State):
    """Router function to decide whether to continue to tools or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    else:
        return END


graph_builder = StateGraph(State)

graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})
graph_builder.add_edge("tools", "agent")
graph_builder.add_edge("agent", END)

graph = graph_builder.compile()

print("\n" + "="*80)
print("🤖 NEW CASE - AGENT PROCESSING")
print("="*80)

print(f"\n📝 INCOMING CASE DETAILS:")
print(f"   ID: {incoming_case.id}")
print(f"   Title: {incoming_case.title}")
print(f"   Description: {incoming_case.description}")
print(f"   Priority: {incoming_case.priority.value.upper()}")
print(f"   Current State: {incoming_case.state.value.upper()}")
print(f"   Current Assignee: {incoming_case.assignee.name} ({incoming_case.assignee.department})")
print(f"   Current Component: {incoming_case.component.value.upper()}")
print(f"   Created: {incoming_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

# Create initial message with case details for the agent
initial_message = f"""
New case received that needs analysis and routing:

CASE ID: {incoming_case.id}
TITLE: {incoming_case.title}
DESCRIPTION: {incoming_case.description}
PRIORITY: {incoming_case.priority.value.upper()}
CURRENT STATE: {incoming_case.state.value.upper()}
CURRENT ASSIGNEE: {incoming_case.assignee.name} ({incoming_case.assignee.department})
CURRENT COMPONENT: {incoming_case.component.value.upper()}
CREATED: {incoming_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

# Invoke the graph with the case information
from langchain_core.messages import HumanMessage

result = graph.invoke({
    "messages": [HumanMessage(content=initial_message)]
})

print(f"\n🤖 AGENT ANALYSIS:")
print(f"{result['messages'][-1].content}")

# Get the updated case from the store
updated_case = case_store[incoming_case.id]

print(f"\n📊 CASE STATUS AFTER AGENT PROCESSING:")
print(f"   ID: {updated_case.id}")
print(f"   State: {updated_case.state.value.upper()}")
print(f"   Component: {updated_case.component.value.upper()}")
print(f"   Assignee: {updated_case.assignee.name} ({updated_case.assignee.department})")
print(f"   Comments: {len(updated_case.comments)} total")
print(f"   Changes: {len(updated_case.change_history)} total")

if updated_case.comments:
    print(f"\n💬 AGENT COMMENTS:")
    for i, comment in enumerate(updated_case.comments):
        if comment.author == "AGENT":
            comment_time = datetime.fromisoformat(comment.created_at).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   {i+1}. [{comment_time}] {comment.author}")
            print(f"      └─ {comment.content}")

if updated_case.change_history:
    print(f"\n📅 CHANGES MADE BY AGENT:")
    for i, change in enumerate(updated_case.change_history):
        print(f"   {i+1}. [{change.changed_at.strftime('%Y-%m-%d %H:%M:%S')}] {change.field.upper()}")
        print(f"      └─ Changed from '{change.old_value}' to '{change.new_value}'")

print("\n" + "="*80)
print("✅ AGENT PROCESSING COMPLETED")
print("="*80)









