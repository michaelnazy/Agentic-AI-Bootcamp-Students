import os
import sys
from typing import Literal, Optional, TypedDict

# Lets you run the file from either folder easily
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from registry_tools import LOOKUP_UNAVAILABLE, NO_RECORDS, NO_SANCTIONS_MATCH, gleif_lookup, sanctions_screen
from search_tools import web_search

load_dotenv()

# We only have 9 lookups to spend!
MAX_LOOKUPS = 9
BUDGET = {"used": 0}

def spend(what: str) -> bool:
    """Spends 1 budget point. Returns False if we are out of money."""
    if BUDGET["used"] >= MAX_LOOKUPS:
        return False
    BUDGET["used"] += 1
    print(f"  [{BUDGET['used']:2}/{MAX_LOOKUPS}] {what}")
    return True

# Set up the AI Brain
llm = ChatOpenAI(
    model="openai/gpt-4o-mini", 
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

# ==========================================
# 1 - THE FORMS (Schemas)
# ==========================================
class Supplier(BaseModel):
    name: str

class TriagePlan(BaseModel):
    suppliers: list[Supplier]

class Verdict(BaseModel):
    supplier: str
    verdict: Literal["APPROVE", "CONDITIONS", "REJECT", "INSUFFICIENT"]
    reason: str = Field(description="Why? Tell Rana in simple words.")
    action_required: str = Field(description="What specific thing does Rana need to do next?")

# ==========================================
# 2 - THE MEMORY (State)
# ==========================================
class State(TypedDict):
    request: str
    queue: list[str]
    evidence: list[str]
    verdicts: list[dict]
    skipped: list[str]
    current_supplier: str

# ==========================================
# 3 - THE STEPS (Nodes)
# ==========================================
def triage(state: State) -> State:
    """Reads the email and makes a to-do list of suppliers."""
    print("\n--- TRIAGE: Reading Email ---")
    prompt = f"Extract the company names from this email:\n{state['request']}"
    res = llm.with_structured_output(TriagePlan).invoke(prompt)
    
    queue = [s.name for s in res.suppliers]
    return {**state, "queue": queue, "verdicts": [], "skipped": [], "evidence": []}

def screen(state: State) -> State:
    """Gathers evidence for ONE supplier."""
    queue = state["queue"]
    current = queue.pop(0)
    print(f"\n--- SCREENING: {current} ---")
    
    evidence = []
    
    # 1. Sanctions screen is ALWAYS FREE
    s_result = sanctions_screen(current)
    evidence.append(f"Sanctions Screen:\n{s_result}")
    
    # 2. GLEIF lookup COSTS 1 BUDGET POINT
    if spend(f"GLEIF lookup for {current}"):
        g_result = gleif_lookup(current)
        evidence.append(f"GLEIF Register:\n{g_result}")
        
        # 3. If GLEIF finds nothing, try a Web Search (COSTS 1 BUDGET POINT)
        if NO_RECORDS in g_result and spend(f"Web search for {current}"):
            w_result = web_search(current + " company profile")
            evidence.append(f"Web Search:\n{w_result}")
    else:
        evidence.append("GLEIF lookup skipped - NO BUDGET LEFT")

    return {**state, "current_supplier": current, "evidence": evidence, "queue": queue}

def decide(state: State) -> State:
    """Looks at the evidence and picks a verdict."""
    current = state["current_supplier"]
    print(f"--- DECIDING: {current} ---")
    
    ev_str = "\n\n".join(state["evidence"])
    
    # If we had no budget to check them, we must skip them honestly
    if "NO BUDGET LEFT" in ev_str:
        state["skipped"].append(current)
        return state
        
    prompt = f"""
    Review the evidence for '{current}' and pick a verdict: APPROVE, CONDITIONS, REJECT, or INSUFFICIENT.
    - If OFAC similarity is 0.90+ for the exact name, REJECT.
    - If multiple GLEIF candidates exist and no exact match, CONDITIONS.
    - If registration status is LAPSED, CONDITIONS.
    - If NO_RECORDS in GLEIF and no Web evidence, INSUFFICIENT.
    
    Evidence:
    {ev_str}
    """
    verdict = llm.with_structured_output(Verdict).invoke(prompt)
    state["verdicts"].append(verdict.model_dump())
    return state

def budget_left(state: State) -> str:
    """The Router: Checks if we should loop or stop."""
    if len(state["queue"]) > 0:
        return "next"
    return "memo"

def write_memo(state: State) -> State:
    """Prints the final report."""
    print("\n" + "="*60)
    print("SUPPLIER REVIEW · Thursday payment run")
    print("="*60 + "\n")
    
    for v in state["verdicts"]:
        print(f"[{v['verdict']}] {v['supplier']}")
        print(f"      Reason: {v['reason']}")
        print(f"      Action: {v['action_required']}\n")
        
    print("NOT CHECKED (Out of Budget):")
    for s in state["skipped"]:
        print(f"      {s} - Residual risk: accepted, not assessed.")
    print("="*60 + "\n")
    
    return state

# ==========================================
# 4 - BUILD THE LOOP
# ==========================================
def build_graph():
    g = StateGraph(State)
    g.add_node("triage", triage)
    g.add_node("screen", screen)
    g.add_node("decide", decide)
    g.add_node("write_memo", write_memo)
    
    g.set_entry_point("triage")
    g.add_edge("triage", "screen")
    g.add_edge("screen", "decide")
    # THE LOOP: Go back to screen if we have budget/queue left, else go to memo
    g.add_conditional_edges("decide", budget_left, {"next": "screen", "memo": "write_memo"})
    g.add_edge("write_memo", END)
    
    return g.compile()

if __name__ == "__main__":
    # Read Rana's email
    with open("REQUEST.md", "r", encoding="utf-8") as f:
        request_text = f.read()
    
    # Run the agent!
    app = build_graph()
    app.invoke({
        "request": request_text,
        "queue": [],
        "evidence": [],
        "verdicts": [],
        "skipped": [],
        "current_supplier": ""
    })