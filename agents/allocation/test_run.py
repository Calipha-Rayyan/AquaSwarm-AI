from crewai import Crew, Process

from agents.allocation.agent import create_allocation_agent
from agents.allocation.task import create_allocation_task


agent = create_allocation_agent()
task = create_allocation_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("ALLOCATION AGENT RESULT")
print("==============================")
print(result)