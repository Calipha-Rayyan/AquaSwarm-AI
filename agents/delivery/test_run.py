from crewai import Crew, Process

from agents.delivery.agent import create_delivery_agent
from agents.delivery.task import create_delivery_task


agent = create_delivery_agent()
task = create_delivery_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("DELIVERY AGENT RESULT")
print("==============================")
print(result)