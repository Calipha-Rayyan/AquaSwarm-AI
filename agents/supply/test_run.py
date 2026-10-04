from crewai import Crew, Process

from agents.supply.agent import create_supply_agent
from agents.supply.task import create_supply_task


agent = create_supply_agent()
task = create_supply_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("SUPPLY AGENT RESULT")
print("==============================")
print(result)