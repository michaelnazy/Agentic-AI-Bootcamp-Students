import os
import sys
from typing import TypedDict
from dotenv import find_dotenv, load_dotenv
from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI

load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

# 1. Configure the OpenRouter model
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Define the State (Data Flow)
class StudyGuideState(TypedDict):
    topic: str
    explanation: str
    example: str
    quiz: str

# Node 1
def explain_topic(state: StudyGuideState) -> StudyGuideState:
    """Task 1: explain the topic in plain language."""
    response = llm.invoke(
        f"Explain '{state['topic']}' in 2-3 plain-language sentences for a beginner. Do not invent statistics and do not write a quiz yet."
    )
    return {**state, "explanation": response.content}

# Node 2
def create_example(state: StudyGuideState) -> StudyGuideState:
    """Task 2: use the explanation to create an example and misconception."""
    response = llm.invoke(
        f"Based on this explanation of {state['topic']}:\n{state['explanation']}\n\n"
        f"Provide one practical example and one common misconception. Make a clear distinction between the two."
    )
    return {**state, "example": response.content}

# Node 3
def create_quiz(state: StudyGuideState) -> StudyGuideState:
    """Task 3: use earlier state to create three questions and answers."""
    response = llm.invoke(
        f"Topic: {state['topic']}\n"
        f"Explanation: {state['explanation']}\n"
        f"Example & Misconception: {state['example']}\n\n"
        f"Based on the context above, create exactly three quiz questions followed by an answer key."
    )
    return {**state, "quiz": response.content}

def build_graph():
    graph = StateGraph(StudyGuideState)

    # Register all three nodes
    graph.add_node("explain_topic", explain_topic)
    graph.add_node("create_example", create_example)
    graph.add_node("create_quiz", create_quiz)

    # Explicit Control Flow: set entry point and connect edges
    graph.set_entry_point("explain_topic")
    graph.add_edge("explain_topic", "create_example")
    graph.add_edge("create_example", "create_quiz")
    graph.add_edge("create_quiz", END)

    return graph.compile()

def run_study_guide(topic: str) -> StudyGuideState:
    app = build_graph()
    initial_state: StudyGuideState = {
        "topic": topic,
        "explanation": "",
        "example": "",
        "quiz": "",
    }
    return app.invoke(initial_state)

if __name__ == "__main__":
    # Takes the topic from the command line, defaults to "Model Context Protocol"
    topic = " ".join(sys.argv[1:]).strip() or "Model Context Protocol"
    
    result = run_study_guide(topic)

    print(f"\n# Study Guide: {result['topic']}\n")
    print("## Explanation\n", result["explanation"])
    print("\n## Example and misconception\n", result["example"])
    print("\n## Quiz\n", result["quiz"])