from crewai import Agent

from config.settings import GROQ_LLM


def create_allocation_agent() -> Agent:
    """Create the specialist agent responsible for water allocation decisions."""
    return Agent(
        role="Water Allocation Specialist",
        goal=(
            "Determine the water quantity that should be allocated to a tank "
            "and confirm the supplier to use, based only on the validated "
            "Demand Agent and Supply Agent results."
        ),
        backstory=(
            "You are a water resource allocation specialist in the AquaSwarm "
            "AI operations network. You balance shortage, priority, supplier "
            "capacity, and operational constraints. Numerical values already "
            "calculated by upstream agents are authoritative. You explain "
            "your decision clearly and never invent supplier or demand data. "
            "Never allocate more water than the reported shortage or the "
            "recommended supplier's available quantity. Keep the tank ID, "
            "supplier ID, and priority consistent with the upstream results."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )
