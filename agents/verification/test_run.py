from crewai import Crew, Process

from agents.verification.agent import create_verification_agent
from agents.verification.task import create_verification_task


agent = create_verification_agent()
task = create_verification_task()

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n==============================")
print("VERIFICATION AGENT RESULT")
print("==============================")
print(result)