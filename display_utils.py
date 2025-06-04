from datetime import datetime
from agent_utils import State



def display_raw_messages(result, scenario_name):
    """Display the complete raw StateGraph messages."""
    print(f"\n📋 COMPLETE STATEGRAPH MESSAGES FOR {scenario_name}:")
    print("="*60)
    for i, message in enumerate(result['messages']):
        print(f"\nMessage {i+1}:")
        print(f"Type: {type(message).__name__}")
        if hasattr(message, 'content') and message.content:
            print(f"Content: {message.content}")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"Tool Calls: {message.tool_calls}")
    print("="*60)


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


def print_state_info(state: State, node_name: str, step_type: str = "ENTERING"):
    """Print the complete messages being added."""
    if step_type == "EXITING" and state['messages']:
        last_msg = state['messages'][-1]
        print(f"\n📝 {node_name} added message:")
        
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            print(f"   └─ Tool calls:")
            for tc in last_msg.tool_calls:
                print(f"      🔧 {tc['name']}")
                if tc.get('args'):
                    for key, value in tc['args'].items():
                        # Truncate very long values but show more than before
                        if isinstance(value, str) and len(value) > 300:
                            value_display = value[:300] + "..."
                        else:
                            value_display = value
                        print(f"         └─ {key}: {value_display}")
        elif hasattr(last_msg, 'content') and last_msg.content:
            print(f"   └─ Content:")
            print(f"      {last_msg.content}")


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