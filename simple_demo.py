from dotenv import load_dotenv
from datetime import datetime, timedelta
from simple_model import Case, Comment, CaseState, Priority, Component, Change
from tools_and_resources import (
    case_store, webapp_dev, applog_dev, support_agent, api_dev, database_admin, security_analyst, ALL_TOOLS
)
from cases import load_all_cases
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import END, StateGraph, START


load_dotenv()

# Load all cases into the store
cases = load_all_cases()
incoming_case = cases["incoming_case"]
complex_case = cases["complex_case"] 
permissions_case = cases["permissions_case"]

llm = init_chat_model(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)
tool_node = ToolNode(tools=ALL_TOOLS)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def agent(state: State) -> State:
    system_prompt = """You are an IT Service Management (ITSM) assistant. Your job is to help customers with their support cases.
    
    IMPORTANT: Only make tool calls when necessary. Once you have addressed the customer's issue, provide a final response without tool calls to end the conversation.
    
    You have the following tools at your disposal:
    - review_app_design: Review the app design and suggest a workaround for the customer if you find something, reply directly to the customer. THIS IS THE FIRST THING YOU SHOULD CHECK AS THE ANSWER COULD BE RIGHT THERE.
    - check_past_cases: Check past cases that are similar to the current case via something like vector search. THIS IS THE SECOND THING YOU SHOULD CHECK.
    - change_case_component: Change the component of the current case.
    - change_case_assignee: Change the assignee of the current case.
    - change_case_state: Change the state of the current case.
    - change_case_priority: Change the priority of the current case.
    - add_comment: Add a comment to the current case.
    - synthesize_comments: Synthesize all the comments into one comment. This is useful when there are a lot of comments and you need to summarize them for developer or support colleagues. Only used this if specified.

    WORKFLOW:
    1. For permission/access issues: Use review_app_design first
    2. For technical issues: Use check_past_cases to find similar resolved cases
    3. Make necessary changes (component, assignee, etc.) based on findings
    4. Add comments if needed
    5. If you feel like you have enough info to close the case without any other human intervention, change the case state to resolved
    6. Provide a final summary response WITHOUT tool calls to end the process

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

# Configure recursion limit and add debugging
config = {"recursion_limit": 10}  # Lower limit to catch issues faster

def display_tool_calls(messages):
    """Display tool calls with their IDs."""
    for message in messages:
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                print(f"🔧 TOOL CALL: {tool_call['name']} (ID: {tool_call['id']})")
                if tool_call.get('args'):
                    for key, value in tool_call['args'].items():
                        print(f"   └─ {key}: {value}")

def display_case_info(case, title="CASE INFO"):
    """Display detailed case information."""
    print(f"\n📋 {title}:")
    print(f"   ID: {case.id}")
    print(f"   Title: {case.title}")
    print(f"   Priority: {case.priority.value.upper()}")
    print(f"   State: {case.state.value.upper()}")
    print(f"   Component: {case.component.value.upper()}")
    print(f"   Assignee: {case.assignee.name} ({case.assignee.department})")
    print(f"   Comments: {len(case.comments)}")
    print(f"   Changes: {len(case.change_history)}")
    
    if case.comments:
        print(f"\n   💬 RECENT COMMENTS:")
        # Show last 3 comments if more than 3, otherwise show all
        recent_comments = case.comments[-3:] if len(case.comments) > 3 else case.comments
        for i, comment in enumerate(recent_comments):
            comment_time = datetime.fromisoformat(comment.created_at).strftime('%m-%d %H:%M')
            print(f"      [{comment_time}] {comment.author}: {comment.content[:80]}...")
    
    if case.change_history:
        print(f"\n   📅 RECENT CHANGES:")
        # Show last 3 changes if more than 3, otherwise show all
        recent_changes = case.change_history[-3:] if len(case.change_history) > 3 else case.change_history
        for change in recent_changes:
            change_time = change.changed_at.strftime('%m-%d %H:%M')
            print(f"      [{change_time}] {change.field}: '{change.old_value}' → '{change.new_value}'")

print("\n" + "="*80)
print("🤖 SCENARIO 1: NEW CASE - AGENT PROCESSING")
print("="*80)

display_case_info(incoming_case, "BEFORE - INCOMING CASE")

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
result = graph.invoke({
    "messages": [HumanMessage(content=initial_message)]
}, config=config)

print(f"\n🔧 TOOL CALLS MADE:")
display_tool_calls(result['messages'])

# Get the updated case from the store
updated_case = case_store[incoming_case.id]

display_case_info(updated_case, "AFTER - CASE PROCESSED")

print("\n" + "="*80)
print("✅ SCENARIO 1 COMPLETED")
print("="*80)


# Scenario 2: there is a case that has gotten a lot of comments, the agent needs to synthesize everything relevant into one comment.

print("\n" + "="*80)
print("📋 SCENARIO 2: COMPLEX CASE WITH MULTIPLE TEAM COMMENTS")
print("="*80)

display_case_info(complex_case, "BEFORE - COMPLEX CASE")

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
}, config=config)

print(f"\n🔧 TOOL CALLS MADE:")
display_tool_calls(result['messages'])

# Show the updated case
updated_complex_case = case_store[complex_case.id]

display_case_info(updated_complex_case, "AFTER - CASE PROCESSED")

print("\n" + "="*80)
print("✅ SCENARIO 2 COMPLETED")
print("="*80)


# Scenario 3: A case comes in where the customer cannot achieve something, but it's because the app is not designed to support that behavior. Suggest a workaround

print("\n" + "="*80)
print("🤖 SCENARIO 3: PERMISSIONS ISSUE - AGENT PROCESSING")
print("="*80)

display_case_info(permissions_case, "BEFORE - PERMISSIONS CASE")

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
}, config=config)

print(f"\n🔧 TOOL CALLS MADE:")
display_tool_calls(result['messages'])

# Get the updated case from the store
updated_permissions_case = case_store[permissions_case.id]

display_case_info(updated_permissions_case, "AFTER - CASE PROCESSED")

print("\n" + "="*80)
print("✅ SCENARIO 3 COMPLETED")
print("="*80)

def debug_graph_execution(result):
    """Debug function to see what happened during graph execution."""
    print(f"\n🐛 DEBUG INFO:")
    print(f"   Total messages: {len(result['messages'])}")
    for i, message in enumerate(result['messages']):
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   Message {i}: Tool calls - {[tc['name'] for tc in message.tool_calls]}")
        else:
            print(f"   Message {i}: Response (no tool calls)")
    print()







