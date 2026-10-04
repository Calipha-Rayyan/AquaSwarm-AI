from crewai import Crew, Process

from agents.orchestrator.agent import create_orchestrator_agent
from agents.orchestrator.task import create_orchestrator_task


agent = create_orchestrator_agent()
task = create_orchestrator_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("ORCHESTRATOR AGENT RESULT")
print("==============================")
print(result)