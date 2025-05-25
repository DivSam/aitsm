#!/usr/bin/env python3
"""
Simple working case management agent without complex workflows
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool
from models import (
    Case, Priority, CaseState, Component, Assignee,
    CreateCaseRequest, AddCommentRequest
)
from uuid import UUID
import json

# Load environment variables
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

# Global store
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

# Define tools
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
    
    case_id = store.add_case(case)
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

def simple_agent():
    """Create a simple agent that can handle case management."""
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found!")
    
    # Initialize LLM with tools
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    tools = [create_case, list_all_cases]
    llm_with_tools = llm.bind_tools(tools)
    
    def process_request(user_message: str):
        """Process a user request and handle tool calls."""
        
        # System message
        system_msg = SystemMessage(content="""You are a helpful AI assistant that manages cases in a case management system.
        You MUST use the available tools to perform case management operations.
        
        Available components: web, api
        Available assignees: john, jane
        
        When a user asks you to create a case, you MUST call the create_case tool.
        Use priority values: LOW, MEDIUM, HIGH, VERY_HIGH
        Use component_key: web or api
        Use creator_key: john or jane""")
        
        # Initial conversation
        messages = [system_msg, HumanMessage(content=user_message)]
        
        print(f"DEBUG: Sending {len(messages)} messages to LLM")
        
        # Get response from LLM
        response = llm_with_tools.invoke(messages)
        print(f"DEBUG: Got response with {len(response.tool_calls) if response.tool_calls else 0} tool calls")
        
        # Handle tool calls if any
        if response.tool_calls:
            # Add the AI response to messages
            messages.append(response)
            
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                print(f"DEBUG: Executing tool {tool_name} with args {tool_args}")
                
                # Find and execute the tool
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            result = tool.invoke(tool_args)
                            print(f"DEBUG: Tool result: {result}")
                            
                            # Add tool result to messages
                            from langchain_core.messages import ToolMessage
                            messages.append(ToolMessage(
                                content=result,
                                tool_call_id=tool_call["id"]
                            ))
                        except Exception as e:
                            print(f"DEBUG: Tool execution failed: {e}")
                            messages.append(ToolMessage(
                                content=f"Error: {str(e)}",
                                tool_call_id=tool_call["id"]
                            ))
                        break
            
            # Get final response from LLM
            final_response = llm.invoke(messages)
            return messages, final_response
        else:
            return messages, response
    
    return process_request

def main():
    try:
        # Create the agent
        agent = simple_agent()
        
        print("=== Starting Simple Case Management Session ===")
        
        # Test the agent
        user_input = "Create a new high priority case about the login page not loading for the web component, created by jane"
        messages, final_response = agent(user_input)
        
        print("\n=== Conversation ===")
        for i, msg in enumerate(messages, 1):
            if isinstance(msg, HumanMessage):
                print(f"{i}. Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                print(f"{i}. AI: {msg.content}")
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"   Tool calls: {len(msg.tool_calls)}")
            elif hasattr(msg, 'content'):
                print(f"{i}. Tool: {msg.content}")
        
        print(f"\nFinal AI Response: {final_response.content}")
        
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
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 