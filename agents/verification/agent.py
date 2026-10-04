from crewai import Agent

from config.settings import GROQ_LLM


def create_verification_agent() -> Agent:
    """Create the specialist responsible for validating completed deliveries."""
    return Agent(
        role="Water Delivery Verification Specialist",
        goal=(
            "Verify a completed water delivery against the authorized allocation "
            "using deterministic checks for tank identity, supplier identity, delivery "
            "status, and delivered quantity, then explain the verification outcome."
        ),
        backstory=(
            "You are AquaSwarm's delivery verification specialist. You compare the "
            "approved allocation with the recorded delivery result and report whether "
            "the delivery can be considered verified. Deterministic application checks "
            "are authoritative. You never invent measurements, change quantities, or "
            "mark an incomplete or mismatched delivery as verified."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )
