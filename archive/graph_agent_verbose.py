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
        print(f"🗄️  STORE: Added case {case_id} to store. Total cases: {len(self.cases)}")
        return case_id
    
    def get_case(self, case_id: str) -> Case:
        case = self.cases.get(case_id)
        print(f"🗄️  STORE: Retrieved case {case_id}: {'Found' if case else 'Not found'}")
        return case
    
    def list_cases(self):
        cases = list(self.cases.values())
        print(f"🗄️  STORE: Listed {len(cases)} cases from store")
        return cases

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

print(f"🔧 INIT: Created global components: {list(GLOBAL_COMPONENTS.keys())}")
print(f"🔧 INIT: Created global assignees: {list(GLOBAL_ASSIGNEES.keys())}")

class State(TypedDict):
    messages: Annotated[list, add_messages]

def initialize_resources():
    print("🔧 RESOURCES: Initializing resources...")
    resources = {
        "components": GLOBAL_COMPONENTS,
        "assignees": GLOBAL_ASSIGNEES
    }
    print(f"🔧 RESOURCES: Returned {len(resources['components'])} components and {len(resources['assignees'])} assignees")
    return resources

@tool
def create_case(title: str, description: str, priority: str, component_key: str, assignee_key: str, customer_company: str) -> str:
    """Create a new case with the given details including assignee, component, and customer company."""
    print(f"\n🔨 TOOL: create_case called")
    print(f"   📝 Parameters:")
    print(f"      - title: {title}")
    print(f"      - description: {description}")
    print(f"      - priority: {priority}")
    print(f"      - component_key: {component_key}")
    print(f"      - assignee_key: {assignee_key}")
    print(f"      - customer_company: {customer_company}")
    
    try:
        print(f"🔧 TOOL: Getting resources...")
        resources = initialize_resources()
        components = resources["components"]
        assignees = resources["assignees"]
        
        print(f"🔍 TOOL: Looking up component '{component_key}'...")
        if component_key not in components:
            print(f"❌ TOOL: Component '{component_key}' not found! Available: {list(components.keys())}")
            return f"Error: Component '{component_key}' not found"
        component = components[component_key]
        print(f"✅ TOOL: Found component: {component.name} (ID: {component.id})")
        
        print(f"🔍 TOOL: Looking up assignee '{assignee_key}'...")
        if assignee_key not in assignees:
            print(f"❌ TOOL: Assignee '{assignee_key}' not found! Available: {list(assignees.keys())}")
            return f"Error: Assignee '{assignee_key}' not found"
        assignee = assignees[assignee_key]
        print(f"✅ TOOL: Found assignee: {assignee.name} (ID: {assignee.id}, Dept: {assignee.department})")
        
        print(f"🏗️  TOOL: Creating case...")
        case = Case.create_new(
            title=title,
            description=description,
            priority=Priority[priority.upper()],
            component_id=component.id,
            creator_id=assignee.id,
            creator_name=assignee.name,
            customer_company=customer_company
        )
        print(f"✅ TOOL: Case created with ID: {case.id}")
        
        print(f"👤 TOOL: Assigning case to {assignee.name}...")
        case.assign_to(
            assignee_id=assignee.id,
            assignee_name=assignee.name,
            performed_by_id=assignee.id,
            performed_by_name=assignee.name
        )
        print(f"✅ TOOL: Case assigned successfully")
        
        print(f"💾 TOOL: Adding case to store...")
        case_id = store.add_case(case)
        
        result = f"Successfully created case with ID: {case_id}\nTitle: {title}\nPriority: {priority}\nComponent: {component.name}\nAssignee: {assignee.name} ({assignee.department})\nCustomer Company: {customer_company}"
        print(f"✅ TOOL: create_case completed successfully")
        print(f"📤 TOOL: Returning result: {result[:100]}...")
        return result
    
    except Exception as e:
        print(f"❌ TOOL: Error in create_case: {e}")
        import traceback
        traceback.print_exc()
        return f"Error creating case: {str(e)}"

@tool
def list_all_cases() -> str:
    """List all cases in the store with detailed information."""
    print(f"\n📋 TOOL: list_all_cases called")
    
    try:
        print(f"🗄️  TOOL: Getting cases from store...")
        cases = store.list_cases()
        if not cases:
            print(f"📋 TOOL: No cases found in store")
            return "No cases found in the store"
        
        print(f"📋 TOOL: Processing {len(cases)} cases...")
        result = "All cases in store:\n"
        
        for i, case in enumerate(cases):
            print(f"📋 TOOL: Processing case {i+1}/{len(cases)}: {case.id}")
            
            # Get assignee name if assigned
            assignee_info = "Unassigned"
            if case.assignee_id:
                print(f"🔍 TOOL: Looking up assignee for case {case.id}...")
                resources = initialize_resources()
                assignees = resources["assignees"]
                for key, assignee in assignees.items():
                    if assignee.id == case.assignee_id:
                        assignee_info = f"{assignee.name} ({assignee.department})"
                        print(f"✅ TOOL: Found assignee: {assignee_info}")
                        break
                else:
                    print(f"❌ TOOL: Assignee with ID {case.assignee_id} not found")
            else:
                print(f"ℹ️  TOOL: Case {case.id} has no assignee")
            
            # Get component name if assigned
            component_info = "No component"
            if case.component_id:
                print(f"🔍 TOOL: Looking up component for case {case.id}...")
                resources = initialize_resources()
                components = resources["components"]
                for key, component in components.items():
                    if component.id == case.component_id:
                        component_info = component.name
                        print(f"✅ TOOL: Found component: {component_info}")
                        break
                else:
                    print(f"❌ TOOL: Component with ID {case.component_id} not found")
            else:
                print(f"ℹ️  TOOL: Case {case.id} has no component")
            
            # Get customer company from the proper field
            customer_company = case.customer_company or "Unknown"
            print(f"ℹ️  TOOL: Customer company: {customer_company}")
            
            result += f"- ID: {case.id}\n"
            result += f"  Title: {case.title}\n"
            result += f"  State: {case.state.value}\n"
            result += f"  Priority: {case.priority.value.upper()}\n"
            result += f"  Component: {component_info}\n"
            result += f"  Assignee: {assignee_info}\n"
            result += f"  Customer: {customer_company}\n"
            result += f"  Created: {case.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        print(f"✅ TOOL: list_all_cases completed successfully")
        print(f"📤 TOOL: Returning result with {len(cases)} cases")
        return result
        
    except Exception as e:
        print(f"❌ TOOL: Error in list_all_cases: {e}")
        import traceback
        traceback.print_exc()
        return f"Error listing cases: {str(e)}"

llm = init_chat_model(model="gpt-4o-mini", temperature=0)
tools = [create_case, list_all_cases]
llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools=tools)

print(f"🤖 INIT: LLM initialized with {len(tools)} tools: {[tool.name for tool in tools]}")

def agent(state: State) -> State:
    print(f"\n🤖 AGENT: Processing message...")
    print(f"📨 AGENT: Input message: {state['messages'][-1].content}")
    print(f"📊 AGENT: Total messages in state: {len(state['messages'])}")
    
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

    print(f"📝 AGENT: Using system prompt ({len(system_prompt)} chars)")
    
    # Build the full conversation with system prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    print(f"💬 AGENT: Built conversation with {len(messages)} messages")
    
    try:
        print(f"🔄 AGENT: Invoking LLM...")
        response = llm_with_tools.invoke(messages)
        print(f"✅ AGENT: LLM response received")
        print(f"📤 AGENT: Response type: {type(response).__name__}")
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"🔨 AGENT: LLM wants to call {len(response.tool_calls)} tool(s):")
            for i, tool_call in enumerate(response.tool_calls):
                print(f"   Tool {i+1}: {getattr(tool_call, 'name', 'Unknown')} with args: {getattr(tool_call, 'args', {})}")
        else:
            print(f"💬 AGENT: LLM response is text only (no tool calls)")
        
        return {"messages": [response]}
        
    except Exception as e:
        print(f"❌ AGENT: Error: {e}")
        import traceback
        traceback.print_exc()
        from langchain_core.messages import AIMessage
        error_msg = AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")
        return {"messages": [error_msg]}

def should_continue(state: State):
    """Determine if we should continue to tools or end."""
    print(f"\n🔀 ROUTER: Determining next step...")
    last_message = state["messages"][-1]
    print(f"📨 ROUTER: Last message type: {type(last_message).__name__}")
    
    # If the last message has tool calls, go to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"🔨 ROUTER: Found {len(last_message.tool_calls)} tool call(s) - routing to TOOLS")
        for i, tool_call in enumerate(last_message.tool_calls):
            print(f"   Tool {i+1}: {getattr(tool_call, 'name', 'Unknown')}")
        return "tools"
    
    # Otherwise, end the conversation
    print(f"🏁 ROUTER: No tool calls found - routing to END")
    return END

print(f"🏗️  INIT: Building graph...")

graph_builder = StateGraph(State)

graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("agent", should_continue)

graph_builder.add_edge("tools", "agent")
graph_builder.add_edge(START, "agent")

graph = graph_builder.compile()

print(f"✅ INIT: Graph compiled successfully")
print(f"🏗️  INIT: Graph nodes: agent, tools")
print(f"🏗️  INIT: Graph edges: START->agent, agent->tools (conditional), tools->agent, agent->END (conditional)")

# Test cases
user_message = "Hi this is Sam from SAP, I cannot open my web app I cannot run my business at all so this is pretty high priority"

print(f"\n{'='*80}")
print(f"🚀 EXECUTION: Starting first test case")
print(f"🔄 Processing: {user_message}")
print(f"{'='*80}")

try:
    result = graph.invoke({"messages": [HumanMessage(content=user_message)]})
    
    print(f"\n📊 EXECUTION: Final result analysis")
    print(f"📨 EXECUTION: Total messages in result: {len(result['messages'])}")
    
    for i, message in enumerate(result["messages"]):
        print(f"📨 Message {i+1}: {type(message).__name__}")
        if hasattr(message, 'content') and message.content:
            print(f"   Content: {message.content[:100]}...")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   Tool calls: {len(message.tool_calls)}")
    
    print(f"\n📋 Final Response:")
    print(result["messages"][-1].content)
    print()
    
    print(f"📊 Cases in Store:")
    cases = store.list_cases()
    if cases:
        for case in cases:
            print(f"  • {case.id}: {case.title} [{case.priority.value.upper()}]")
    else:
        print("  No cases found")
        
except Exception as e:
    print(f"❌ EXECUTION: Error: {e}")
    import traceback
    traceback.print_exc()

# Second test case
second_user_message = "Hi this is Nick from SAP, i have a question about my API component. I seem to be getting an error when I try to create a new object. This is impacting my business but it's not critical. I'm not sure what the issue is so I'd like to create a case for this."

print(f"\n{'='*80}")
print(f"🚀 EXECUTION: Starting second test case")
print(f"🔄 Processing: {second_user_message}")
print(f"{'='*80}")

try:
    second_result = graph.invoke({"messages": [HumanMessage(content=second_user_message)]})
    
    print(f"\n📋 Final Response:")
    print(second_result["messages"][-1].content)
    print()

except Exception as e:
    print(f"❌ EXECUTION: Error: {e}")
    import traceback
    traceback.print_exc()

# List all cases
print(f"\n{'='*80}")
print(f"🚀 EXECUTION: Listing all cases")
print(f"🔄 Listing all cases...")
print(f"{'='*80}")

try:
    list_response = graph.invoke({"messages": [HumanMessage(content="List all cases")]})
    
    print(f"\n📋 Response:")
    print(list_response["messages"][-1].content)
    
except Exception as e:
    print(f"❌ EXECUTION: Error listing cases: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print(f"🏁 EXECUTION: All test cases completed")
print(f"{'='*80}") 