from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool
from dotenv import find_dotenv, load_dotenv

try:
    from crewai.events.listeners.tracing.utils import mark_first_execution_done
    mark_first_execution_done()
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search_tools import web_search

load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

# TODO 1: Model Client
llm = LLM(
    model="openrouter/openai/gpt-4o-mini",
    temperature=0,
    api_key=api_key,
)

# TODO 2: Tool Wrapper
@tool("Web Search")
def search_web(query: str) -> str:
    """Search the web for factual evidence.
    Returns numbered snippets with source URLs.
    May return the literal strings 'NO_RESULTS' if nothing was found or
    'SEARCH_UNAVAILABLE' if the network failed.
    """
    return web_search(query)


def build_crew() -> Crew:
    # TODO 3: The Researcher Agent
    researcher = Agent(
        role="Factual Web Researcher",
        goal="Search the web and gather raw, verified evidence with exact source URLs.",
        backstory=(
            "You are a meticulous research assistant. You search using keywords, extract relevant facts, "
            "and always retain the source URLs. If the search returns NO_RESULTS or SEARCH_UNAVAILABLE, "
            "you report that plainly without inventing details from memory."
        ),
        tools=[search_web],
        llm=llm,
        verbose=True,
        max_iter=4,
    )

    # TODO 4: The Writer Agent
    writer = Agent(
        role="Evidence-Based Technical Writer",
        goal="Synthesize evidence into concise answers or report information gaps honestly.",
        backstory=(
            "You write strict, evidence-backed summaries. You never invent facts or statistics. "
            "If the research contains sufficient evidence, you write a concise summary citing source URLs. "
            "If the research contains NO_RESULTS or lacks sufficient evidence, you strictly refuse to answer, "
            "report what is missing, and provide a NEXT SEARCH query."
        ),
        llm=llm,
        verbose=True,
        max_iter=4,
    )

    # TODO 5: Research Task (No agent= in hierarchical mode)
    research_task = Task(
        description=(
            "Use the Web Search tool to find factual evidence regarding: '{question}'. "
            "Extract findings with source URLs. If no relevant info is found, return the exact tool output."
        ),
        expected_output="A list of factual findings with URLs, or a statement that no results were found.",
    )

    # TODO 6: Writing Task (The branch lives in the instructions)
    write_task = Task(
        description=(
            "Review the findings for the question: '{question}'.\n"
            "Determine if there is enough evidence to answer accurately.\n\n"
            "If YES (Enough Evidence):\n"
            "- Start with 'VERDICT: ANSWERED'\n"
            "- Provide a clear response under 180 words\n"
            "- Quote at least one source URL\n\n"
            "If NO (Not Enough Evidence or NO_RESULTS):\n"
            "- Start with 'VERDICT: COULD NOT VERIFY'\n"
            "- State plainly in one sentence that this could not be verified\n"
            "- Provide 1-2 bullet points explaining what is missing\n"
            "- End with exactly: 'NEXT SEARCH: <suggested query>'"
        ),
        expected_output="A formatted final report starting with VERDICT: ANSWERED or VERDICT: COULD NOT VERIFY.",
    )

    # TODO 7: Hierarchical Process with manager_llm
    return Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.hierarchical,
        manager_llm=llm,
        verbose=True,
        tracing=False,
    )


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or \
        "Anthropic was founded by former OpenAI employees"

    result = str(build_crew().kickoff(inputs={"question": question}))

    print("\n" + "=" * 70)
    print(f"QUESTION : {question}")
    print("=" * 70)
    print(result)

    # TODO 8: Determine which route the crew took
    if "VERDICT: ANSWERED" in result:
        route = "ANSWERED"
    elif "VERDICT: COULD NOT VERIFY" in result or "NEXT SEARCH:" in result:
        route = "GAP REPORTED"
    else:
        route = "UNKNOWN"

    print("\n" + "=" * 70)
    print(f"ROUTE : {route}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())