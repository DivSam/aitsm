from typing import Annotated

from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]

llm = init_chat_model(model="gpt-3.5-turbo", temperature=0)

def agent(state: State) -> State:
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder = StateGraph(State)

graph_builder.add_node("agent", agent)
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


print(graph.invoke({"messages": [HumanMessage(content="Hello, how are you?")]})["messages"][-1].content)