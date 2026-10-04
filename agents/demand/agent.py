from crewai import Agent

from config.settings import GROQ_LLM


def create_demand_agent() -> Agent:
    return Agent(
        role="Water Demand Analyst",
        goal=(
            "Analyze water availability and demand data and determine "
            "the required water quantity and priority for a tank."
        ),
        backstory=(
            "You are a water demand analysis specialist. "
            "You examine current water levels and daily demand, "
            "identify shortages, and provide a clear structured assessment."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )