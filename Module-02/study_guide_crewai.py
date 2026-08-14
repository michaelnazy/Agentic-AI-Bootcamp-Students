import os
import sys
from dotenv import find_dotenv, load_dotenv
from crewai import Agent, Crew, LLM, Process, Task

load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

# 1. Configure the OpenRouter model for CrewAI
llm = LLM(
    model="openrouter/openai/gpt-4o-mini",
    temperature=0,
    api_key=api_key,
)

def build_crew() -> Crew:
    # 2. Create the study-guide Agent
    teacher = Agent(
        role="Patient Study Guide Teacher",
        goal="Produce accurate, understandable, and well-structured learning material for students.",
        backstory="You are an expert educator who breaks down complex technical topics. You never invent facts or statistics.",
        llm=llm,
        verbose=True,
    )

    # 3. Create Task 1 (Explanation)
    explain_task = Task(
        description="Explain the topic '{topic}' in 2-3 plain-language sentences. Do not include a quiz or examples yet.",
        expected_output="A concise 2-3 sentence plain-language explanation of the topic.",
        agent=teacher,
    )

    # 4. Create Task 2 (Example/Misconception), explicitly passing Task 1's context
    example_task = Task(
        description="Create one practical example and identify one common misconception for the topic '{topic}'.",
        expected_output="One practical example and one common misconception, clearly distinguished.",
        agent=teacher,
        context=[explain_task],
    )

    # 5. Create Task 3 (Assembly & Quiz), passing both previous tasks as context
    quiz_task = Task(
        description=(
            "Assemble the complete study guide for '{topic}'. You MUST preserve and include the exact explanation from the first task, "
            "the exact example and misconception from the second task. Then, generate exactly three quiz questions "
            "followed by a matching answer key."
        ),
        expected_output=(
            "A complete markdown-formatted guide containing all earlier work, organized with '## Explanation', '## Example and misconception', and '## Quiz' headers."
        ),
        agent=teacher,
        context=[explain_task, example_task],
    )

    # 6. Assemble one sequential Crew
    return Crew(
        agents=[teacher],
        tasks=[explain_task, example_task, quiz_task],
        process=Process.sequential,
        verbose=True,
        tracing=False,
    )

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]).strip() or "Model Context Protocol"
    
    crew = build_crew()
    result = crew.kickoff(inputs={"topic": topic})
    
    print("\n" + "="*60)
    print(f"# Final Study Guide Output")
    print("="*60)
    print(result)