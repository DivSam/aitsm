from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from uuid import uuid4, UUID

load_dotenv()

from models import Case, Priority, Component, Assignee, CaseState, ActionType
from datetime import datetime, timedelta


class CaseStore:
    def __init__(self):
        self.cases = {}
        self.components = {}
        self.assignees = {}
    
    def add_case(self, case: Case) -> str:
        case_id = str(case.id)
        self.cases[case_id] = case
        return case_id
    
    def get_case(self, case_id: str) -> Case:
        return self.cases.get(case_id)
    
    def list_cases(self):
        return list(self.cases.values())
    
    def list_cases_by_customer(self, customer_company: str):
        return [case for case in self.cases.values() if case.customer_company == customer_company]
    
    def list_cases_by_assignee(self, assignee_id: str):
        return [case for case in self.cases.values() if case.assignee_id == assignee_id]
    
    def list_cases_by_component(self, component_id: str):
        return [case for case in self.cases.values() if case.component_id == component_id]
    
    def list_cases_by_priority(self, priority: Priority):
        return [case for case in self.cases.values() if case.priority == priority]
    
    def list_cases_by_state(self, state: CaseState):
        return [case for case in self.cases.values() if case.state == state]
    
class State(TypedDict):
    messages: Annotated[list, add_messages]

store = CaseStore()

# Create components
webapp_component = Component(name="WebApp", description="Main web application component")
applog_component = Component(name="AppLog", description="Application logging component")

# Create assignee (developer who resolved it)
developer = Assignee(name="Mike", email="mike@company.com", department="AppLog Development")

developer_2 = Assignee(name="John", email="john@company.com", department="WebApp Development")



# Create the resolved case
print("Creating resolved case...")

# Create case with initial details (3 days ago)
case_created_time = datetime.utcnow() - timedelta(days=3)

resolved_case = Case(
    title="Web Application Stops When Clicking Run Job Button",
    description="Customer reported that their web application stops running whenever they click on the 'run job' button. Initial investigation suggested WebApp component issue.",
    priority=Priority.HIGH,
    state=CaseState.RESOLVED,
    component_id=applog_component.id,  # Final component after investigation
    assignee_id=developer_2.id,
    customer_company="TechCorp Solutions",
    created_at=case_created_time,
    updated_at=datetime.utcnow()
)

# Add creation action
resolved_case.add_action(
    ActionType.CREATED,
    performed_by_id=developer_2.id,
    performed_by_name=developer_2.name,
    details="Case 'Web Application Stops When Clicking Run Job Button' created for TechCorp Solutions"
)

# Simulate the investigation timeline
# Day 1: Case assigned and investigation started
resolved_case.action_history.append({
    "action_type": ActionType.ASSIGNED,
    "timestamp": case_created_time + timedelta(hours=2),
    "performed_by_id": developer_2.id,
    "performed_by_name": developer_2.name,
    "details": f"Case assigned to {developer_2.name}",
    "new_value": str(developer_2.id)
})

# Day 1: Started investigating WebApp component
resolved_case.action_history.append({
    "action_type": ActionType.COMMENT_ADDED,
    "timestamp": case_created_time + timedelta(hours=4),
    "performed_by_id": developer_2.id,
    "performed_by_name": developer_2.name,
    "details": "Started investigating WebApp component. Initial logs show application crashes on 'run job' button click."
})

# Day 2: State changed to in progress
resolved_case.action_history.append({
    "action_type": ActionType.STATE_CHANGED,
    "timestamp": case_created_time + timedelta(days=1),
    "performed_by_id": developer_2.id,
    "performed_by_name": developer_2.name,
    "details": "State changed from new to in_progress",
    "old_value": "new",
    "new_value": "in_progress"
})

# Day 2: Component reassigned after deeper investigation
resolved_case.action_history.append({
    "action_type": ActionType.UPDATED,
    "timestamp": case_created_time + timedelta(days=1, hours=6),
    "performed_by_id": developer.id,
    "performed_by_name": developer.name,
    "details": f"Component reassigned from WebApp to AppLog after investigation revealed logging component failure",
    "old_value": str(webapp_component.id),
    "new_value": str(applog_component.id)
})

# Day 2: Root cause identified
resolved_case.action_history.append({
    "action_type": ActionType.COMMENT_ADDED,
    "timestamp": case_created_time + timedelta(days=1, hours=8),
    "performed_by_id": developer.id,
    "performed_by_name": developer.name,
    "details": "Root cause identified: AppLog component not working properly, causing application crash when job execution tries to write logs."
})

# Day 3: Fix developed and deployed
resolved_case.action_history.append({
    "action_type": ActionType.COMMENT_ADDED,
    "timestamp": case_created_time + timedelta(days=2, hours=4),
    "performed_by_id": developer.id,
    "performed_by_name": developer.name,
    "details": "Fix developed for AppLog component. Deployed to production environment."
})

# Day 3: Case resolved
resolved_case.action_history.append({
    "action_type": ActionType.RESOLVED,
    "timestamp": datetime.utcnow(),
    "performed_by_id": developer.id,
    "performed_by_name": developer.name,
    "details": "Case resolved. AppLog component fix deployed successfully. Customer confirmed web application now works properly with 'run job' button."
})

# Add final comment
resolved_case.add_comment(
    content="Case successfully resolved. The issue was traced to the AppLog component which was failing silently when the application tried to write job execution logs. After fixing the logging component and deploying the update, the customer confirmed that the 'run job' button now works as expected.",
    author_id=developer.id,
    author_name=developer.name,
    is_internal=False
)

# Add case to store
case_id = store.add_case(resolved_case)

print(f"✅ Added resolved case to store:")
print(f"   Case ID: {case_id}")
print(f"   Title: {resolved_case.title}")
print(f"   Customer: {resolved_case.customer_company}")
print(f"   Priority: {resolved_case.priority.value.upper()}")
print(f"   State: {resolved_case.state.value.upper()}")
print(f"   Component: AppLog (reassigned from WebApp)")
print(f"   Assignee: {developer.name}")
print(f"   Created: {resolved_case.created_at.strftime('%Y-%m-%d %H:%M')}")
print(f"   Resolved: {resolved_case.updated_at.strftime('%Y-%m-%d %H:%M')}")
print(f"   Total Actions: {len(resolved_case.action_history)}")
print(f"   Comments: {len(resolved_case.comments)}")

print(resolved_case.action_history)


print(store.list_cases())




@tool
def investigate_cases():
    """In reality, you could expect this to be some sort of database query to get similar cases, but in this demo. we just return the action history of the resolved case"""
    return resolved_case.action_history


@tool
def reroute_case(case_id: str, new_assignee_id: str, new_component_id: str):
    """Reroute a case to a new assignee and component"""
    case = store.get_case(case_id)
    case.assignee_id = new_assignee_id
    case.component_id = new_component_id
    store.add_case(case)
    return f"Case {case_id} rerouted to {new_assignee_id} and {new_component_id}"

@tool
def reply_to_customer(case_id: str, message: str):
    """Reply to the customer with a message"""
    case = store.get_case(case_id)
    case.add_comment(message, author_id=developer.id, author_name=developer.name, is_internal=False)
    case.state = CaseState.AWAITING_CUSTOMER_INFO
    store.add_case(case)
    return f"Case {case_id} replied to with message: {message}"

@tool
def get_case_info(case_id: str):
    """Get the info of a case"""
    case = store.get_case(case_id)
    if not case:
        return f"Case {case_id} not found."
    
    return {
        "id": str(case.id),
        "title": case.title,
        "description": case.description,
        "priority": case.priority.value,
        "state": case.state.value,
        "customer_company": case.customer_company,
        "component_id": str(case.component_id) if case.component_id else None,
        "assignee_id": str(case.assignee_id) if case.assignee_id else None,
        "created_at": case.created_at.isoformat(),
        "comments_count": len(case.comments),
        "actions_count": len(case.action_history)
    }

llm = init_chat_model(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools([investigate_cases, reroute_case, reply_to_customer, get_case_info])
tool_node = ToolNode(tools=[investigate_cases, reroute_case, reply_to_customer, get_case_info])

def agent(state: State) -> State:
    system_prompt = """You are an IT Service Management (ITSM) assistant. Your job is to help customers with their support cases.
    
    IMPORTANT RULES:
    1. First, investigate prior cases to understand patterns
    2. Then, if needed, reroute the case to the appropriate assignee/component (only once)
    3. Finally, if appropriate, reply to the customer with status updates (only once per conversation)
    4. Do NOT call the same tool multiple times in one conversation
    5. Do NOT reply to the customer multiple times
    6. After taking actions, provide a summary without calling more tools
    
    Available tools:
    - investigate_cases: Look at historical case data for patterns
    - get_case_info: Get current case details
    - reroute_case: Change assignee and component (use only once if needed)
    - reply_to_customer: Send message to customer (use only once if needed)
    
    Work systematically: investigate → analyze → take action → summarize.
    """

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}

def should_continue(state: State):
    """Router function to decide whether to continue to tools or end."""
    print(f"\n🔀 ROUTER: Determining next step...")
    last_message = state["messages"][-1]
    print(f"📨 ROUTER: Last message type: {type(last_message).__name__}")
    
    # If the last message has tool calls, go to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"🔨 ROUTER: Found {len(last_message.tool_calls)} tool call(s) - routing to TOOLS")
        for i, tool_call in enumerate(last_message.tool_calls):
            # Try different ways to get the tool name
            tool_name = "Unknown"
            if hasattr(tool_call, 'name'):
                tool_name = tool_call.name
            elif hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                tool_name = tool_call.function.name
            elif isinstance(tool_call, dict):
                tool_name = tool_call.get('name', tool_call.get('function', {}).get('name', 'Unknown'))
            
            # Also try to get arguments if available
            tool_args = "No args"
            if hasattr(tool_call, 'args'):
                tool_args = str(tool_call.args)
            elif hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments'):
                tool_args = tool_call.function.arguments
            elif isinstance(tool_call, dict):
                tool_args = str(tool_call.get('args', tool_call.get('function', {}).get('arguments', 'No args')))
            
            print(f"   Tool {i+1}: {tool_name} with args: {tool_args[:100]}...")
        return "tools"
    
    # Otherwise, end the conversation
    print(f"🏁 ROUTER: No tool calls found - routing to END")
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

graph = graph_builder.compile()

# New scenario: Similar webapp/run jobs issue
print("\n" + "="*80)
print("🆕 NEW SCENARIO: Similar WebApp/Run Jobs Issue")
print("="*80)

# Create a new case for the current issue
current_case = Case.create_new(
    title="WebApp Freezes When Running Jobs",
    description="Customer reports webapp becomes unresponsive when clicking run jobs button",
    priority=Priority.HIGH,
    component_id=webapp_component.id,  # Initially assigned to WebApp
    creator_id=developer_2.id,
    creator_name=developer_2.name,
    customer_company="DataFlow Inc"
)

# Assign to WebApp developer initially
current_case.assign_to(
    assignee_id=developer_2.id,
    assignee_name=developer_2.name,
    performed_by_id=developer_2.id,
    performed_by_name=developer_2.name
)

# Add to store
current_case_id = store.add_case(current_case)

print(f"📋 Created new case: {current_case_id}")
print(f"   Customer: DataFlow Inc")
print(f"   Issue: WebApp freezes when clicking run jobs button")
print(f"   Initially assigned to: {developer_2.name} (WebApp Development)")
print(f"   Component: WebApp")

# Now feed this scenario into the graph
user_message = f"""Hi, I'm the support agent handling case {current_case_id}. 

A customer from DataFlow Inc is reporting that their web application freezes and becomes completely unresponsive whenever they click the "run jobs" button. This is causing major business disruption as they can't process their daily batch jobs.

The case is currently assigned to John from WebApp Development team, but I'm wondering if we've seen similar issues before and if there might be a better component assignment or approach based on our past experience.

Can you help investigate this and provide recommendations?"""

print(f"\n🤖 AGENT PROCESSING:")
print(f"User Query: {user_message[:200]}...")

# Process through the graph
from langchain_core.messages import HumanMessage

try:
    result = graph.invoke({"messages": [HumanMessage(content=user_message)]})
    
    print(f"\n🔍 AGENT RESPONSE:")
    print(result["messages"][-1].content)
    
    # Check if case was modified
    updated_case = store.get_case(current_case_id)
    print(f"\n📊 CASE STATUS AFTER AGENT PROCESSING:")
    print(f"   Case ID: {current_case_id}")
    print(f"   State: {updated_case.state.value}")
    print(f"   Assignee ID: {updated_case.assignee_id}")
    print(f"   Component ID: {updated_case.component_id}")
    print(f"   Recent Comments: {len(updated_case.comments)}")
    
    if updated_case.comments:
        print(f"   Latest Comment: {updated_case.comments[-1].content[:100]}...")
        
except Exception as e:
    print(f"❌ Error processing through graph: {e}")
    import traceback
    traceback.print_exc()

print(f"\n📈 FINAL STORE STATUS:")
all_cases = store.list_cases()
print(f"Total cases in store: {len(all_cases)}")
for case in all_cases:
    print(f"  • {case.id}: {case.title[:50]}... [{case.state.value.upper()}] - {case.customer_company}")

# Print complete case history for the current case
print(f"\n" + "="*80)
print(f"📋 COMPLETE CASE HISTORY: {current_case_id}")
print("="*80)

final_case = store.get_case(current_case_id)
if final_case:
    print(f"📝 CASE DETAILS:")
    print(f"   ID: {final_case.id}")
    print(f"   Title: {final_case.title}")
    print(f"   Description: {final_case.description}")
    print(f"   Customer: {final_case.customer_company}")
    print(f"   Priority: {final_case.priority.value.upper()}")
    print(f"   State: {final_case.state.value.upper()}")
    print(f"   Component ID: {final_case.component_id}")
    print(f"   Assignee ID: {final_case.assignee_id}")
    print(f"   Created: {final_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Updated: {final_case.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📅 ACTION HISTORY ({len(final_case.action_history)} actions):")
    for i, action in enumerate(final_case.action_history):
        timestamp = action.timestamp if hasattr(action, 'timestamp') else "Unknown time"
        if hasattr(timestamp, 'strftime'):
            timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        action_type = action.action_type if hasattr(action, 'action_type') else action.get('action_type', 'Unknown')
        details = action.details if hasattr(action, 'details') else action.get('details', 'No details')
        performer = action.performed_by_name if hasattr(action, 'performed_by_name') else action.get('performed_by_name', 'Unknown')
        
        print(f"   {i+1}. [{timestamp}] {action_type} by {performer}")
        print(f"      └─ {details}")
    
    print(f"\n💬 COMMENTS ({len(final_case.comments)} comments):")
    if final_case.comments:
        for i, comment in enumerate(final_case.comments):
            comment_time = comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            comment_type = "🔒 Internal" if comment.is_internal else "👥 External"
            print(f"   {i+1}. [{comment_time}] {comment_type} - {comment.author_name}")
            print(f"      └─ {comment.content}")
    else:
        print("   No comments")
    
    # Show component and assignee details
    print(f"\n🔧 COMPONENT & ASSIGNEE DETAILS:")
    if final_case.component_id:
        if str(final_case.component_id) == str(webapp_component.id):
            print(f"   Component: {webapp_component.name} - {webapp_component.description}")
        elif str(final_case.component_id) == str(applog_component.id):
            print(f"   Component: {applog_component.name} - {applog_component.description}")
        else:
            print(f"   Component: Unknown component ID {final_case.component_id}")
    
    if final_case.assignee_id:
        if str(final_case.assignee_id) == str(developer.id):
            print(f"   Assignee: {developer.name} ({developer.department}) - {developer.email}")
        elif str(final_case.assignee_id) == str(developer_2.id):
            print(f"   Assignee: {developer_2.name} ({developer_2.department}) - {developer_2.email}")
        else:
            print(f"   Assignee: Unknown assignee ID {final_case.assignee_id}")

print("\n" + "="*80)
print("🏁 DEMO COMPLETED")
print("="*80)






