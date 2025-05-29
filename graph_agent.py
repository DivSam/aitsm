from typing import Annotated

from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from models import Case, Priority, Component, Assignee

from dotenv import load_dotenv

load_dotenv()

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

# Global store instance
store = CaseStore()

# Global resource instances to ensure consistent UUIDs
GLOBAL_COMPONENTS = {
    "web": Component(name="Web", description="Web component"),
    "api": Component(name="API", description="API component")
}

GLOBAL_ASSIGNEES = {
    "john": Assignee(name="John", email="john@example.com", department="Engineering Development"),
    "jane": Assignee(name="Jane", email="jane@example.com", department="Engineering Customer Support and Questions")
}

class State(TypedDict):
    messages: Annotated[list, add_messages]

def initialize_resources():
    return {
        "components": GLOBAL_COMPONENTS,
        "assignees": GLOBAL_ASSIGNEES
    }

@tool
def create_case(title: str, description: str, priority: str, component_key: str, assignee_key: str, customer_company: str) -> str:
    """Create a new case with the given details including assignee, component, and customer company."""
    try:
        resources = initialize_resources()
        components = resources["components"]
        assignees = resources["assignees"]
        
        component = components[component_key]
        assignee = assignees[assignee_key]
        
        case = Case.create_new(
            title=title,
            description=description,
            priority=Priority[priority.upper()],
            component_id=component.id,
            creator_id=assignee.id,
            creator_name=assignee.name,
            customer_company=customer_company
        )
        
        # Assign the case to the assignee
        case.assign_to(
            assignee_id=assignee.id,
            assignee_name=assignee.name,
            performed_by_id=assignee.id,
            performed_by_name=assignee.name
        )
        
        # Add to store
        case_id = store.add_case(case)
        print(f"✅ Created case {case_id}: {title} (Priority: {priority}, Assignee: {assignee.name}, Customer: {customer_company})")
        
        return f"Successfully created case with ID: {case_id}\nTitle: {title}\nPriority: {priority}\nComponent: {component.name}\nAssignee: {assignee.name} ({assignee.department})\nCustomer Company: {customer_company}"
    
    except Exception as e:
        print(f"❌ Error creating case: {e}")
        return f"Error creating case: {str(e)}"

@tool
def list_all_cases() -> str:
    """List all cases in the store with detailed information."""
    cases = store.list_cases()
    if not cases:
        return "No cases found in the store"
    
    result = "All cases in store:\n"
    for case in cases:
        # Get assignee name if assigned
        assignee_info = "Unassigned"
        if case.assignee_id:
            # Find assignee name from resources
            resources = initialize_resources()
            assignees = resources["assignees"]
            for key, assignee in assignees.items():
                if assignee.id == case.assignee_id:
                    assignee_info = f"{assignee.name} ({assignee.department})"
                    break
        
        # Get component name if assigned
        component_info = "No component"
        if case.component_id:
            resources = initialize_resources()
            components = resources["components"]
            for key, component in components.items():
                if component.id == case.component_id:
                    component_info = component.name
                    break
        
        # Get customer company from the proper field
        customer_company = case.customer_company or "Unknown"
        
        result += f"- ID: {case.id}\n"
        result += f"  Title: {case.title}\n"
        result += f"  State: {case.state.value}\n"
        result += f"  Priority: {case.priority.value.upper()}\n"
        result += f"  Component: {component_info}\n"
        result += f"  Assignee: {assignee_info}\n"
        result += f"  Customer: {customer_company}\n"
        result += f"  Created: {case.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    return result



llm = init_chat_model(model="gpt-4o-mini", temperature=0)
tools = [create_case, list_all_cases]
llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools=tools)

def agent(state: State) -> State:
    system_prompt = """You are an IT Service Management (ITSM) assistant. Your job is to help customers create support cases.

When a customer describes an issue, extract the following information and create a case:

**Title**: Create a brief, descriptive title for the case based on the customer's issue
**Description**: Use the customer's detailed description of the issue
**Priority**: Determine priority based on business impact:
- HIGH: Business cannot operate, critical systems down
- MEDIUM: Significant impact but workarounds exist
- LOW: Minor issues, feature requests
**Component Key**: Identify the component from customer description:
- "web" for web-related issues
- "api" for API-related issues
**Assignee Key**: Extract or infer the assignee:
- "john" for John/engineering issues
- "jane" for anything that sounds like a question or a support issue
- Use "jane" as default if unclear
**Customer Company**: Extract the customer's company name from their message

Always use the create_case tool when a customer reports an issue. Be helpful and professional."""

    # Build the full conversation with system prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    try:
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ Agent error: {e}")
        from langchain_core.messages import AIMessage
        error_msg = AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")
        return {"messages": [error_msg]}

def should_continue(state: State):
    """Determine if we should continue to tools or end."""
    last_message = state["messages"][-1]
    # If the last message has tool calls, go to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    # Otherwise, end the conversation
    return END

graph_builder = StateGraph(State)

graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("agent", should_continue)

graph_builder.add_edge("tools", "agent")
graph_builder.add_edge(START, "agent")

graph = graph_builder.compile()

# Save graph visualization to PNG file
# try:
#     graph_png = graph.get_graph().draw_mermaid_png()
#     with open("graph_visualization.png", "wb") as f:
#         f.write(graph_png)
#     print("Graph saved to graph_visualization.png")
# except Exception as e:
#     print(f"Could not save graph visualization: {e}")


user_message = "Hi this is Sam from SAP, I cannot open my web app I cannot run my business at all so this is pretty high priority"

print(f"🔄 Processing: {user_message}")
print()

try:
    result = graph.invoke({"messages": [HumanMessage(content=user_message)]})
    
    print("📋 Final Response:")
    print(result["messages"][-1].content)
    print()
    
    print("📊 Cases in Store:")
    cases = store.list_cases()
    if cases:
        for case in cases:
            print(f"  • {case.id}: {case.title} [{case.priority.value.upper()}]")
    else:
        print("  No cases found")
        
except Exception as e:
    print(f"❌ Error: {e}")







second_user_message = "Hi this is Nick from SAP, i have a question about my API component. I seem to be getting an error when I try to create a new object. This is impacting my business but it's not critical. I'm not sure what the issue is so I'd like to create a case for this."

print("\n" + "="*50)
print(f"🔄 Processing: {second_user_message}")
print()

try:
    second_result = graph.invoke({"messages": [HumanMessage(content=second_user_message)]})
    
    print("📋 Final Response:")
    print(second_result["messages"][-1].content)
    print()

except Exception as e:
    print(f"❌ Error: {e}")






print("\n" + "="*50)
print("🔄 Listing all cases...")

try:
    list_response = graph.invoke({"messages": [HumanMessage(content="List all cases")]})
    
    print("📋 Response:")
    print(list_response["messages"][-1].content)
    
except Exception as e:
    print(f"❌ Error listing cases: {e}")