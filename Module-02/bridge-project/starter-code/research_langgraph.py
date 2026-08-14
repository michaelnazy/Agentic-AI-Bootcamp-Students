import os
import sys
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search_tools import NO_RESULTS, SEARCH_UNAVAILABLE, web_search

load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

api_key = os.environ.get("OPENROUTER_API_KEY")
base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

# TODO 1: Build the model client
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    base_url=base_url,
    api_key=api_key,
)

class DeskState(TypedDict):
    question: str      
    query: str         
    evidence: str      
    verdict: str       
    reasoning: str     
    output: str        
    route_taken: str   

def plan_query(state: DeskState) -> DeskState:
    """Node 1: turn the question into something worth searching for."""
    # Updated prompt to force a short, keyword-based search
    prompt = (
        f"Convert this question into a single, concise web search query focused strictly on the core entity.\n"
        f"For example, if the question is 'Who founded Microsoft?', the query should be 'Microsoft founders'.\n"
        f"Output ONLY the query keywords and nothing else.\n"
        f"Question: {state['question']}"
    )
    response = llm.invoke(prompt)
    return {**state, "query": response.content.strip().strip('"')}

def run_search(state: DeskState) -> DeskState:
    """Node 2: the tool. There is no model call in this node at all."""
    # TODO 3: Call web_search (2 lines, no LLM)
    evidence = web_search(state["query"])
    return {**state, "evidence": evidence}

def assess(state: DeskState) -> DeskState:
    """Node 3: is this evidence actually good enough to answer with?"""
    # TODO 4: Handle failure markers BEFORE calling the model to save money
    ev = state["evidence"]
    if ev in (NO_RESULTS, SEARCH_UNAVAILABLE):
        return {
            **state,
            "verdict": "NOT_ENOUGH",
            "reasoning": f"Tool returned {ev}. Cannot verify without evidence."
        }

    # TODO 5: Ask model to evaluate evidence
    prompt = (
        f"Question: {state['question']}\n"
        f"Evidence: {ev}\n\n"
        "Does the evidence provide enough information to completely and accurately answer the question?\n"
        "Provide 1-3 short bullets explaining your reasoning.\n"
        "Then, on the very last line, output exactly one word: ENOUGH or NOT_ENOUGH."
    )
    response = llm.invoke(prompt)
    raw_text = response.content.strip()
    
    return {**state, "verdict": read_verdict(raw_text), "reasoning": raw_text}

def read_verdict(raw: str) -> str:
    """Pull the verdict out of the model's free text."""
    # TODO 6: The trap! "ENOUGH" is inside "NOT_ENOUGH"
    lines = [line.strip() for line in raw.split("\n") if line.strip()]
    if not lines:
        return "NOT_ENOUGH"
        
    last_line = lines[-1].upper()
    
    # We MUST check for NOT_ENOUGH first, and use NOT_ENOUGH as the safe fallback!
    if "NOT_ENOUGH" in last_line or "NOT ENOUGH" in last_line:
        return "NOT_ENOUGH"
    elif "ENOUGH" in last_line:
        return "ENOUGH"
    else:
        return "NOT_ENOUGH"

def choose_next(state: DeskState) -> Literal["write_answer", "report_gap"]:
    """THE ROUTER. Runs no model, writes no state. It only names the next node."""
    # TODO 7: Choose route based on verdict
    if state["verdict"] == "ENOUGH":
        return "write_answer"
    return "report_gap"

def write_answer(state: DeskState) -> DeskState:
    """Node 4a: the ENOUGH path."""
    # TODO 8: Answer using ONLY evidence, cite URL, under 180 words
    prompt = (
        f"Question: {state['question']}\n"
        f"Evidence: {state['evidence']}\n\n"
        "Answer the question using ONLY the provided evidence. Invent nothing.\n"
        "Rules:\n"
        "- Quote at least one source URL from the evidence.\n"
        "- If part of the question is not covered, say so.\n"
        "- Keep the answer under 180 words."
    )
    response = llm.invoke(prompt)
    return {**state, "output": response.content, "route_taken": "write_answer"}

def report_gap(state: DeskState) -> DeskState:
    """Node 4b: the NOT_ENOUGH path. This node must NOT answer the question."""
    # TODO 9: Report the gap
    prompt = (
        f"Question: {state['question']}\n"
        f"Evidence so far: {state['evidence']}\n\n"
        "Do NOT answer the question. Report the gap in information using these rules:\n"
        "- Write one sentence saying plainly that this could not be verified.\n"
        "- Write 1-2 bullets on what is missing.\n"
        "- On the final line, write exactly: NEXT SEARCH: <the one query you would run next>"
    )
    response = llm.invoke(prompt)
    return {**state, "output": response.content, "route_taken": "report_gap"}

def build_graph():
    graph = StateGraph(DeskState)

    # TODO 10: Register all five nodes
    graph.add_node("plan_query", plan_query)
    graph.add_node("run_search", run_search)
    graph.add_node("assess", assess)
    graph.add_node("write_answer", write_answer)
    graph.add_node("report_gap", report_gap)

    # TODO 11: The fixed part of the route
    graph.set_entry_point("plan_query")
    graph.add_edge("plan_query", "run_search")
    graph.add_edge("run_search", "assess")

    # TODO 12: THE CONDITIONAL LINE
    graph.add_conditional_edges(
        "assess",              
        choose_next,           
        {                      
            "write_answer": "write_answer",
            "report_gap":   "report_gap",
        },
    )

    # TODO 13: Both finish at END
    graph.add_edge("write_answer", END)
    graph.add_edge("report_gap", END)

    return graph.compile()

def run(question: str) -> DeskState:
    return build_graph().invoke({
        "question": question,
        "query": "",
        "evidence": "",
        "verdict": "",
        "reasoning": "",
        "output": "",
        "route_taken": "",
    })

def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or \
        "Anthropic was founded by former OpenAI employees"

    result = run(question)

    print("=" * 70)
    print(f"QUESTION : {result['question']}")
    print("=" * 70)
    print(f"\n[1] SEARCH QUERY\n{result['query']}")
    print(f"\n[2] EVIDENCE ({len(result['evidence'])} chars)")
    print(result["evidence"][:700])
    print(f"\n[3] ASSESSMENT\n{result['reasoning']}")
    print("\n" + "=" * 70)
    print(f"VERDICT : {result['verdict']}")
    print(f"ROUTE   : {result['route_taken'].upper()}")
    print("=" * 70)
    print(result["output"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())