from crewai import Agent

from config.settings import GROQ_LLM


def create_allocation_agent() -> Agent:
    return Agent(
        role="Water Allocation Specialist",
        goal=(
            "Determine the appropriate water quantity to allocate to a tank "
            "and select the appropriate supplier based on shortage and priority."
        ),
        backstory=(
            "You are a water resource allocation specialist. "
            "You analyze shortages, priorities, and supplier availability "
            "to make efficient water allocation decisions."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )