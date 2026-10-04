from crewai import Agent

from config.settings import GROQ_LLM


def create_manager_approval_agent() -> Agent:
    return Agent(
        role="Water Allocation Manager",
        goal=(
            "Review the proposed water allocation and decide whether it "
            "should be approved for delivery."
        ),
        backstory=(
            "You are a water resource manager responsible for reviewing "
            "allocation decisions before delivery. You consider the tank "
            "shortage, priority, supplier selection, and allocated quantity "
            "before making an approval decision."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )