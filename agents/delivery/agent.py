from crewai import Agent

from config.settings import GROQ_LLM


def create_delivery_agent() -> Agent:
    """Create the specialist responsible for coordinating approved deliveries."""
    return Agent(
        role="Water Delivery Coordinator",
        goal=(
            "Coordinate the execution of an already-approved water allocation, "
            "preserve the authorized tank, supplier, and quantity, and report the "
            "current delivery state without inventing logistics information."
        ),
        backstory=(
            "You are AquaSwarm's water logistics specialist. You work only after "
            "the application has recorded the required human-manager approval. "
            "You track the approved delivery, preserve its authoritative values, "
            "and report status and ETA from supplied operational data. You never "
            "invent supplier capacity, travel time, delivery quantity, or completion."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )
