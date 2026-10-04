from crewai import Agent

from config.settings import GROQ_LLM


def create_anomaly_agent() -> Agent:
    """Create the CrewAI specialist responsible for water anomaly analysis."""
    return Agent(
        role="Water Anomaly Detection Specialist",
        goal=(
            "Analyze provided water tank and demand data to identify operational "
            "anomalies such as unusually low water levels, abnormal inflow, possible "
            "leakage, or unsafe tank conditions. Base conclusions only on the supplied "
            "measurements and demand analysis."
        ),
        backstory=(
            "You are AquaSwarm's water monitoring specialist. You compare current "
            "tank conditions with capacity, demand, and inflow, distinguish normal "
            "shortage from abnormal behavior, assess severity, and provide a concise "
            "evidence-based explanation. Never invent measurements or historical data."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )