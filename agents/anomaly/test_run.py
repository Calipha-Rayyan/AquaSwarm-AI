from crewai import Crew, Process

from agents.anomaly.agent import create_anomaly_agent
from agents.anomaly.task import create_anomaly_task


agent = create_anomaly_agent()
task = create_anomaly_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("ANOMALY AGENT RESULT")
print("==============================")
print(result)