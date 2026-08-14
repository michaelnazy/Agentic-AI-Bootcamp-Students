# Module 2 Bridge Project: The Evidence Desk

## 1. Which framework would you ship for your use case, and why?
[YOUR ANSWER HERE - e.g., Would you prefer LangGraph's strict predictability, or CrewAI's autonomous persistence (like retrying searches)?]

## 2. On the nonsense query — did each version refuse? Paste what they actually produced.
Yes, both versions successfully refused to invent information. 
* **LangGraph Output:** [Paste your terminal output starting from VERDICT: NOT_ENOUGH]
* **CrewAI Output:** [Paste your terminal output starting from VERDICT: COULD NOT VERIFY]

## 3. Where does the decision live in each one? Which could you prove to a customer who asks "how do I know it will never make something up?"
* In **LangGraph**, the decision lives in physical Python code (the `choose_next` router function and `add_conditional_edges`).
* In **CrewAI**, the decision lives inside the LLM prompt (the Manager interpreting the Writer's instructions).
* I could strictly prove the **LangGraph** version to a customer because refusing is a hardcoded code path; the `report_gap` node physically does not contain a prompt that allows it to generate an answer.

## 4. Your `report_gap` ended with `NEXT SEARCH: ...`. Why couldn't your agent run that search?
[YOUR ANSWER HERE - Look at your LangGraph `build_graph()` function. Where does the edge coming out of `report_gap` point to?]