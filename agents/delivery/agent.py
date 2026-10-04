from crewai import Agent

from config.settings import GROQ_LLM


def create_delivery_agent() -> Agent:
    return Agent(
        role="Water Delivery Coordinator",
        goal=(
            "Coordinate water delivery from the selected supplier to the target "
            "tank and determine the delivery status and estimated arrival."
        ),
        backstory=(
            "You are a water logistics specialist. "
            "You coordinate approved water allocations, track delivery quantities, "
            "and provide clear delivery status information."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )