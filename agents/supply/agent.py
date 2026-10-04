from crewai import Agent

from config.settings import GROQ_LLM


def create_supply_agent() -> Agent:
    """Create the specialist responsible for deterministic supplier selection support."""
    return Agent(
        role="Water Supply Specialist",
        goal=(
            "Analyze the supplied supplier options for a water shortage, preserve "
            "the deterministic eligibility and ranking results, and explain why the "
            "recommended supplier is suitable."
        ),
        backstory=(
            "You are AquaSwarm's water supply management specialist. You evaluate "
            "supplier availability, fulfillable quantity, delivery distance, and cost. "
            "The application performs supplier filtering and ranking deterministically; "
            "your job is to interpret those results without inventing supplier data or "
            "changing the selected supplier."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )
