from crewai import Agent

from config.settings import GROQ_LLM


def create_orchestrator_agent() -> Agent:
    """Create the agent that summarizes workflow state and recommends the next action."""
    return Agent(
        role="AquaSwarm Workflow Orchestrator",
        goal=(
            "Review the supplied outputs from AquaSwarm specialist agents, identify "
            "the current workflow stage, determine the next operational step, and "
            "state whether replanning is required. Do not replace deterministic "
            "workflow rules or human approval."
        ),
        backstory=(
            "You are AquaSwarm's workflow coordination specialist. You interpret "
            "results from demand, anomaly, supply, allocation, delivery, verification, "
            "and replanning stages. You maintain consistency across the workflow and "
            "provide a concise status summary. Physical actions, manager approval, "
            "state transitions, and safety constraints remain controlled by the "
            "application workflow rather than by the LLM."
        ),
        llm=GROQ_LLM,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=1,
    )
