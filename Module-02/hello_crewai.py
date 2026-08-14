import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Load environment variables
load_dotenv()

# Initialize the LLM for CrewAI 
# Note the "openrouter/" prefix required by CrewAI
llm = LLM(
    model="openrouter/openai/gpt-4o-mini",
    temperature=0,
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def build_crew() -> Crew:
    # 1. Define the Agent (Role, Goal, Backstory)
    definer = Agent(
        role="Concise Encyclopedia",
        goal="Provide highly accurate, one-sentence definitions for any given topic.",
        backstory="You are a strict, no-nonsense dictionary. You only ever speak in single, clear sentences.",
        llm=llm,
        verbose=True,
    )

    # 2. Define the Task
    define_task = Task(
        description="Define the topic '{topic}' in exactly one sentence.",
        expected_output="A single-sentence definition of the topic.",
        agent=definer,
    )

    # 3. Assemble the Crew
    return Crew(
        agents=[definer],
        tasks=[define_task],
        process=Process.sequential,
        verbose=True,
    )

if __name__ == "__main__":
    crew = build_crew()
    # Kick off the process and pass in the topic
    result = crew.kickoff(inputs={"topic": "agentic AI"})
    
    print("\n" + "=" * 50)
    print("FINAL OUTPUT")
    print("=" * 50)
    print(result)