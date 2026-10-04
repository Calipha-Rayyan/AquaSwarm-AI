from crewai import Agent

from config.settings import GROQ_LLM


def create_verification_agent() -> Agent:
    return Agent(
        role="Water Delivery Verification Specialist",
        goal=(
            "Verify whether the delivered water quantity matches the approved "
            "allocation and identify any delivery discrepancy."
        ),
        backstory=(
            "You are a water delivery verification specialist. "
            "You compare approved allocation quantities with actual delivered "
            "quantities and report discrepancies clearly."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )