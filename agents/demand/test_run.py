from crewai import Crew, Process

from agents.demand.agent import create_demand_agent
from agents.demand.task import create_demand_task


agent = create_demand_agent()
task = create_demand_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("DEMAND AGENT RESULT")
print("==============================")
print(result)