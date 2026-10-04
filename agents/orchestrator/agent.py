from crewai import Agent

from config.settings import GROQ_LLM


def create_orchestrator_agent() -> Agent:
    return Agent(
        role="AquaSwarm Orchestrator",
        goal=(
            "Coordinate the water management workflow by analyzing agent results, "
            "identifying the required next action, and ensuring the process moves "
            "from analysis to allocation, delivery, verification, and replanning."
        ),
        backstory=(
            "You are the central coordinator of the AquaSwarm multi-agent system. "
            "You oversee water demand, anomaly detection, supply, allocation, "
            "delivery, and verification results. You ensure that information "
            "flows between agents and that appropriate next actions are identified."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )