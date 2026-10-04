from crewai import Agent

from config.settings import GROQ_LLM


def create_demand_agent() -> Agent:
    """Create the specialist responsible for water demand analysis."""
    return Agent(
        role="Water Demand Analyst",
        goal=(
            "Analyze the supplied tank condition and demand data, preserve the "
            "authoritative deterministic shortage and priority calculations, and "
            "produce a structured demand assessment for the AquaSwarm workflow."
        ),
        backstory=(
            "You are AquaSwarm's water demand analysis specialist. You examine "
            "current water level, tank capacity, daily demand, inflow, and the "
            "precomputed operating signals. You explain the condition clearly, "
            "but you never invent historical demand, forecasts, measurements, "
            "or values that are not present in the input."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )
