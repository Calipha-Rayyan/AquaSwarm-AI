from crewai import Agent

from config.settings import GROQ_LLM


def create_supply_agent() -> Agent:
    return Agent(
        role="Water Supply Specialist",
        goal=(
            "Analyze available water suppliers and identify the most suitable "
            "supplier based on quantity, distance, and estimated cost."
        ),
        backstory=(
            "You are a water supply management specialist. "
            "You evaluate supplier availability, delivery distance, and cost "
            "to support reliable and efficient water procurement."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )