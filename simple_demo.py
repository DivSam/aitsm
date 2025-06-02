from dotenv import load_dotenv
from datetime import datetime, timedelta
from simple_model import Case, Comment, CaseState, Priority, Component, Change
from tools_and_resources import (
    case_store, webapp_dev, applog_dev, support_agent, api_dev, database_admin, security_analyst, ALL_TOOLS
)
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import END, StateGraph, START


load_dotenv()

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

# Create the incoming case for Scenario 1
incoming_case = Case(
    id="CASE-2025-002",  # Different ID from the historical case
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


llm = init_chat_model(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)
tool_node = ToolNode(tools=ALL_TOOLS)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def agent(state: State) -> State:
    system_prompt = """You are an IT Service Management (ITSM) assistant. Your job is to help customers with their support cases.
    You have the following tools at your disposal:
    - review_app_design: Review the app design and suggest a workaround for the customer if you find something, reply directly to the customer. THIS IS THE FIRST THING YOU SHOULD CHECK AS THE ANSWER COULD BE RIGHT THERE.
    - check_past_cases: Check past cases that are similar to the current case via something like vector search.
    - change_case_component: Change the component of the current case.
    - change_case_assignee: Change the assignee of the current case.
    - change_case_state: Change the state of the current case.
    - change_case_priority: Change the priority of the current case.
    - add_comment: Add a comment to the current case.
    - synthesize_comments: Synthesize all the comments into one comment. This is useful when there are a lot of comments and you need to summarize them for developer or support colleagues. Only used this if specified.

    You will be given a case and a message from a customer. You will need to use the tools to help the customer.
    
    You will also have access to the following assignees:
    - {webapp_dev.name} ({webapp_dev.department}) - WebApp Development
    - {applog_dev.name} ({applog_dev.department}) - AppLog Development
    - {support_agent.name} ({support_agent.department}) - Customer Support
    - {api_dev.name} ({api_dev.department}) - API Development
    - {database_admin.name} ({database_admin.department}) - Database Administration
    - {security_analyst.name} ({security_analyst.department}) - Security Team

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
    """.format(webapp_dev=webapp_dev, applog_dev=applog_dev, support_agent=support_agent, api_dev=api_dev, database_admin=database_admin, security_analyst=security_analyst, Component=Component, Priority=Priority, CaseState=CaseState)

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
print("🤖 SCENARIO 1: NEW CASE - AGENT PROCESSING")
print("="*80)

print(f"\n📝 INCOMING CASE: {incoming_case.id}")
print(f"   Title: {incoming_case.title}")
print(f"   Current Component: {incoming_case.component.value.upper()}")
print(f"   Current Assignee: {incoming_case.assignee.name}")

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
def display_tool_calls(messages):
    """Display tool calls with their IDs."""
    for message in messages:
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                print(f"🔧 TOOL CALL: {tool_call['name']} (ID: {tool_call['id']})")
                if tool_call.get('args'):
                    for key, value in tool_call['args'].items():
                        print(f"   └─ {key}: {value}")

result = graph.invoke({
    "messages": [HumanMessage(content=initial_message)]
})

print(f"\n🔧 TOOL CALLS MADE:")
display_tool_calls(result['messages'])

# Get the updated case from the store
updated_case = case_store[incoming_case.id]

print(f"\n📊 FINAL CASE STATUS:")
print(f"   Component: {updated_case.component.value.upper()}")
print(f"   Assignee: {updated_case.assignee.name}")
print(f"   Comments: {len(updated_case.comments)}")
print(f"   Changes: {len(updated_case.change_history)}")

print("\n" + "="*80)
print("✅ SCENARIO 1 COMPLETED")
print("="*80)




# Scenario 2: there is a case that has gotten a lot of comments, the agent needs to synthesize everything relevant into one comment.


# Create a complex case with many comments from different teams
complex_case_created = datetime.now() - timedelta(days=7)
complex_case = Case(
    id="CASE-2025-003",
    title="Performance Issues and Intermittent 500 Errors in Production",
    description="Multiple customers reporting slow response times and intermittent 500 errors across different parts of the application. Issue seems to be affecting the entire platform with no clear pattern.",
    priority=Priority.VERY_HIGH,
    state=CaseState.IN_PROGRESS,
    assignee=webapp_dev,  # Final assignee after investigation
    component=Component.WEBAPP,  # Final component after investigation
    created_at=complex_case_created,
    updated_at=datetime.now(),
    comments=[
        Comment(
            id="comment_complex_001",
            content="Initial customer reports coming in about slow performance and 500 errors. Creating high priority case. Multiple customers affected across different browsers and devices.",
            author=support_agent.name,
            created_at=(complex_case_created).isoformat(),
            updated_at=(complex_case_created).isoformat()
        ),
        Comment(
            id="comment_complex_002", 
            content="Database team investigating performance issues. Initial analysis shows database queries are performing normally. Average response times are within acceptable ranges. No blocking queries detected.",
            author=database_admin.name,
            created_at=(complex_case_created + timedelta(hours=1)).isoformat(),
            updated_at=(complex_case_created + timedelta(hours=1)).isoformat()
        ),
        Comment(
            id="comment_complex_003",
            content="API team analysis: Backend endpoints are responding correctly with normal latency. 500 errors appear to be triggered by malformed requests coming from the frontend. Request payloads contain invalid JSON in some cases.",
            author=api_dev.name,
            created_at=(complex_case_created + timedelta(hours=3)).isoformat(),
            updated_at=(complex_case_created + timedelta(hours=3)).isoformat()
        ),
        Comment(
            id="comment_complex_004",
            content="Security team investigated potential DDoS or attack vectors. No malicious activity detected. Traffic patterns appear normal. The errors seem to be legitimate user interactions gone wrong.",
            author=security_analyst.name,
            created_at=(complex_case_created + timedelta(hours=5)).isoformat(),
            updated_at=(complex_case_created + timedelta(hours=5)).isoformat()
        ),
        Comment(
            id="comment_complex_005",
            content="AppLog analysis shows error patterns correlate with specific user actions: form submissions, file uploads, and search queries. Errors spike during peak usage hours. Frontend seems to be sending corrupted data.",
            author=applog_dev.name,
            created_at=(complex_case_created + timedelta(days=1)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=1)).isoformat()
        ),
        Comment(
            id="comment_complex_006",
            content="WebApp team taking over investigation. Found significant memory leaks in React components. DOM nodes not being properly cleaned up, causing browser performance degradation over time.",
            author=webapp_dev.name,
            created_at=(complex_case_created + timedelta(days=1, hours=6)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=1, hours=6)).isoformat()
        ),
        Comment(
            id="comment_complex_007",
            content="Database team confirming: After WebApp team's investigation, we can see the corrupted requests are causing our input validation to throw 500 errors. Backend is working correctly, issue is definitely frontend data corruption.",
            author=database_admin.name,
            created_at=(complex_case_created + timedelta(days=2)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=2)).isoformat()
        ),
        Comment(
            id="comment_complex_008",
            content="WebApp team deep dive: Memory leaks causing JavaScript heap overflow after prolonged usage. This corrupts form data before submission. Implementing proper component lifecycle management and memory cleanup.",
            author=webapp_dev.name,
            created_at=(complex_case_created + timedelta(days=2, hours=8)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=2, hours=8)).isoformat()
        ),
        Comment(
            id="comment_complex_009",
            content="API team confirming fix effectiveness: After WebApp team deployed memory leak fixes, we're no longer receiving malformed requests. 500 error rate dropped significantly.",
            author=api_dev.name,
            created_at=(complex_case_created + timedelta(days=3)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=3)).isoformat()
        ),
        Comment(
            id="comment_complex_010",
            content="WebApp team final update: Deployed comprehensive fix including React component optimization, proper event listener cleanup, and improved state management. Performance monitoring shows normal memory usage patterns.",
            author=webapp_dev.name,
            created_at=(complex_case_created + timedelta(days=3, hours=4)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=3, hours=4)).isoformat()
        ),
        Comment(
            id="comment_complex_011",
            content="AppLog monitoring confirms resolution: Error rates back to baseline 0.1%. No more corrupted request patterns detected. Frontend performance metrics show stable memory usage.",
            author=applog_dev.name,
            created_at=(complex_case_created + timedelta(days=4)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=4)).isoformat()
        ),
        Comment(
            id="comment_complex_012",
            content="Support team update: Customer reports confirm resolution. No more performance complaints or 500 errors reported. Users experiencing normal application responsiveness. Case ready for closure.",
            author=support_agent.name,
            created_at=(complex_case_created + timedelta(days=4, hours=6)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=4, hours=6)).isoformat()
        )
    ],
    change_history=[
        Change(
            field="priority",
            old_value="high",
            new_value="very_high",
            changed_at=complex_case_created + timedelta(hours=2)
        ),
        Change(
            field="assignee", 
            old_value=support_agent.name,
            new_value=database_admin.name,
            changed_at=complex_case_created + timedelta(hours=1)
        ),
        Change(
            field="assignee",
            old_value=database_admin.name,
            new_value=webapp_dev.name,
            changed_at=complex_case_created + timedelta(days=1, hours=6)
        ),
        Change(
            field="component",
            old_value="other",
            new_value="webapp", 
            changed_at=complex_case_created + timedelta(days=1, hours=6)
        )
    ]
)

# Add to case store
case_store[complex_case.id] = complex_case

print("\n" + "="*80)
print("📋 SCENARIO 2: COMPLEX CASE WITH MULTIPLE TEAM COMMENTS")
print("="*80)

print(f"\n📝 CASE: {complex_case.id}")
print(f"   Title: {complex_case.title}")
print(f"   Component: {complex_case.component.value.upper()}")
print(f"   Assignee: {complex_case.assignee.name}")
print(f"   Total Comments: {len(complex_case.comments)}")

print(f"\n🤖 AGENT PROCESSING CASE...")

# Create message asking agent to synthesize all the comments
synthesis_message = f"""
Case received that needs analysis and action:

CASE ID: {complex_case.id}
TITLE: {complex_case.title}
DESCRIPTION: {complex_case.description}
PRIORITY: {complex_case.priority.value.upper()}
CURRENT STATE: {complex_case.state.value.upper()}
CURRENT ASSIGNEE: {complex_case.assignee.name} ({complex_case.assignee.department})
CURRENT COMPONENT: {complex_case.component.value.upper()}
CREATED: {complex_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Please read through this case and synthesize for the developer colleagues who will take over investigation.
"""

# Process through the agent
result = graph.invoke({
    "messages": [HumanMessage(content=synthesis_message)]
})

print(f"\n🔧 TOOL CALLS MADE:")
display_tool_calls(result['messages'])

# Show the updated case
updated_complex_case = case_store[complex_case.id]
print(f"\n📊 FINAL CASE STATUS:")
print(f"   Total Comments: {len(updated_complex_case.comments)}")

print("\n" + "="*80)
print("✅ SCENARIO 2 COMPLETED")
print("="*80)


# Scenario 3: A case comes in where the customer cannot achieve something, but it's because the app is not designed to support that behavior. Suggest a workaround

# Create a case for permissions issue
permissions_case = Case(
    id="CASE-2025-004",
    title="Cannot Create New Job - Permission Denied Error",
    description="Customer reports that when they try to create a new job using their regular user account, they get a 'Permission Denied' error. They need to be able to create jobs for their daily workflow but the system is blocking them.",
    priority=Priority.MEDIUM,
    state=CaseState.NEW,
    assignee=support_agent,
    component=Component.WEBAPP,
    created_at=datetime.now() - timedelta(hours=2),
    updated_at=datetime.now() - timedelta(hours=2),
    comments=[],
    change_history=[]
)

# Store the permissions case
case_store[permissions_case.id] = permissions_case

print("\n" + "="*80)
print("🤖 SCENARIO 3: PERMISSIONS ISSUE - AGENT PROCESSING")
print("="*80)

print(f"\n📝 INCOMING CASE: {permissions_case.id}")
print(f"   Title: {permissions_case.title}")
print(f"   Current Component: {permissions_case.component.value.upper()}")
print(f"   Current Assignee: {permissions_case.assignee.name}")

# Create message for the permissions case
permissions_message = f"""
New case received that needs analysis and routing:

CASE ID: {permissions_case.id}
TITLE: {permissions_case.title}
DESCRIPTION: {permissions_case.description}
PRIORITY: {permissions_case.priority.value.upper()}
CURRENT STATE: {permissions_case.state.value.upper()}
CURRENT ASSIGNEE: {permissions_case.assignee.name} ({permissions_case.assignee.department})
CURRENT COMPONENT: {permissions_case.component.value.upper()}
CREATED: {permissions_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

# Process through the agent
result = graph.invoke({
    "messages": [HumanMessage(content=permissions_message)]
})

print(f"\n🔧 TOOL CALLS MADE:")
display_tool_calls(result['messages'])

# Get the updated case from the store
updated_permissions_case = case_store[permissions_case.id]

print(f"\n📊 FINAL CASE STATUS:")
print(f"   Component: {updated_permissions_case.component.value.upper()}")
print(f"   Assignee: {updated_permissions_case.assignee.name}")
print(f"   Comments: {len(updated_permissions_case.comments)}")
print(f"   Changes: {len(updated_permissions_case.change_history)}")

print("\n" + "="*80)
print("✅ SCENARIO 3 COMPLETED")
print("="*80)







