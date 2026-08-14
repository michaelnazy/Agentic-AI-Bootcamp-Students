import os
from typing import TypedDict
from dotenv import find_dotenv, load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

class State(TypedDict):
    topic: str
    definition: str

# Step 3: Initialize the chat model pointing to OpenRouter
llm = ChatOpenAI(
    model="openai/gpt-4o-mini", 
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def define(state: State) -> State:
    """Node: produce a one-sentence definition of state['topic']."""
    prompt = f"Define '{state['topic']}' in exactly one sentence."
    response = llm.invoke(prompt)
    
    # Write the text into state["definition"]
    return {"topic": state["topic"], "definition": response.content}

def format_output(state: State) -> State:
    """Node (Step 4): wrap the definition with a prefix."""
    formatted_def = f"Definition: {state['definition']}"
    return {"topic": state["topic"], "definition": formatted_def}

def build_graph():
    g = StateGraph(State)
    
    # Register both nodes
    g.add_node("define", define)
    g.add_node("format_output", format_output)
    
    # Explicit Control Flow: Wire the edges
    g.set_entry_point("define")
    g.add_edge("define", "format_output")
    g.add_edge("format_output", END)
    
    return g.compile()

if __name__ == "__main__":
    app = build_graph()
    # Invoke the graph with the initial state
    result = app.invoke({"topic": "agentic AI", "definition": ""})
    print(result["definition"])