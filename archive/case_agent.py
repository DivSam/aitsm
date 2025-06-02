from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import ChatPromptTemplate
from models import (
    Case, Priority, Component, Assignee,
)

from dotenv import load_dotenv
load_dotenv()

# In-memory store for cases
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

# Initialize resources
def initialize_resources():
    components = {
        "web": Component(
            name="Web Frontend",
            description="React-based web application frontend"
        ),
        "api": Component(
            name="API Backend",
            description="Python FastAPI backend service"
        )
    }
    
    assignees = {
        "john": Assignee(
            name="John Doe",
            email="john.doe@company.com",
            department="Engineering"
        ),
        "jane": Assignee(
            name="Jane Smith",
            email="jane.smith@company.com",
            department="Customer Support"
        )
    }
    
    return components, assignees


@tool
def create_case(title: str, description: str, priority: str, component_key: str, creator_key: str) -> str:
    """Create a new case with the given details."""
    components, assignees = initialize_resources()
    component = components[component_key]
    creator = assignees[creator_key]
    
    case = Case.create_new(
        title=title,
        description=description,
        priority=Priority[priority.upper()],
        component_id=component.id,
        creator_id=creator.id,
        creator_name=creator.name
    )
    
    # Add to store - this is the key part!
    case_id = store.add_case(case)
    print(f"DEBUG: Added case {case_id} to store. Total cases: {len(store.list_cases())}")
    
    return f"Successfully created case with ID: {case_id}\nTitle: {title}\nPriority: {priority}\nComponent: {component.name}\nCreator: {creator.name}"

@tool
def list_all_cases() -> str:
    """List all cases in the store."""
    cases = store.list_cases()
    if not cases:
        return "No cases found in the store"
    
    result = "All cases in store:\n"
    for case in cases:
        result += f"- ID: {case.id}, Title: {case.title}, State: {case.state}, Priority: {case.priority}\n"
    return result


def main():
    checkpointer = InMemorySaver()
    components, assignees = initialize_resources()

    # Create a formatted string of available options for the prompt
    component_list = ", ".join(components.keys())
    assignee_list = ", ".join(assignees.keys())
    
    # Create detailed component info
    component_details = "\n".join([f"- {key}: {comp.name} ({comp.description})" for key, comp in components.items()])
    assignee_details = "\n".join([f"- {key}: {assignee.name} ({assignee.email}, {assignee.department})" for key, assignee in assignees.items()])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant that manages cases in a case management system.
        You MUST use the available tools to perform case management operations.
        
        Available components:
        {component_details}
        
        Available assignees:
        {assignee_details}

        When a user asks you to create a case, you MUST call the create_case tool.
        Use priority values: LOW, MEDIUM, HIGH, VERY_HIGH
        Use component_key from: {component_list}
        Use creator_key from: {assignee_list}
        
        Always ensure you provide all required parameters: title, description, priority, component_key, creator_key"""),
        ("placeholder", "{messages}"),
    ]).partial(
        component_details=component_details,
        assignee_details=assignee_details,
        component_list=component_list,
        assignee_list=assignee_list
    )

    agent = create_react_agent(
        model=ChatOpenAI(model="gpt-4o-mini"),
        tools=[create_case, list_all_cases],
        prompt=prompt,  
        checkpointer=checkpointer,
    )

    config = {"configurable": {"thread_id": "1"}}
    
    print("=== Creating a test case ===")
    print(f"Available components: {component_list}")
    print(f"Available assignees: {assignee_list}")
    
    response = agent.invoke(
        {"messages": [HumanMessage(content="Create a case for the web frontend with the title 'Test Case' and description 'This is a test case' with HIGH priority, created by jane")]},
        config=config
    )
    
    print("\n=== Agent Response ===")
    print(response["messages"][-1].content)
    
    print("\n=== Cases in Store ===")
    cases = store.list_cases()
    if cases:
        for case in cases:
            print(f"\nCase ID: {case.id}")
            print(f"Title: {case.title}")
            print(f"Description: {case.description}")
            print(f"Priority: {case.priority}")
            print(f"State: {case.state}")
            print(f"Created: {case.created_at}")
    else:
        print("No cases found in store")
    
    # Test listing cases through the agent
    print("\n=== Testing list_all_cases tool ===")
    list_response = agent.invoke(
        {"messages": [HumanMessage(content="List all cases in the store")]},
        config=config
    )
    print(list_response["messages"][-1].content)


    another_response = agent.invoke(
        {"messages": [HumanMessage(content="Create a case for the api backend with the title 'Test Case 2' and description 'This is a test case 2' with HIGH priority, created by john")]},
        config=config
    )
    print(another_response["messages"][-1].content)


    print("\n=== Cases in Store ===")


    checking_on_past_messages = agent.invoke(
        {"messages": [HumanMessage(content="List all cases in the store")]},
        config=config
    )
    print(checking_on_past_messages["messages"][-1].content)

if __name__ == "__main__":
    main()