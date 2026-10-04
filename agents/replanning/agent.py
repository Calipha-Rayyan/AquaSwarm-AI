from crewai import Agent

from config.settings import GROQ_LLM


def create_replanning_agent() -> Agent:
    return Agent(
        role="Water Allocation Replanning Specialist",
        goal=(
            "Reassess a rejected water allocation and determine the next "
            "appropriate action for the water supply workflow."
        ),
        backstory=(
            "You are a water resource replanning specialist. "
            "When a manager rejects an allocation, you review the situation "
            "and determine whether the allocation should be reconsidered, "
            "adjusted, or sent back for another planning cycle."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )