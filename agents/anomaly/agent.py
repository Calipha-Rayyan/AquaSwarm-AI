from crewai import Agent

from config.settings import GROQ_LLM


def create_anomaly_agent() -> Agent:
    return Agent(
        role="Water Anomaly Detection Specialist",
        goal=(
            "Analyze water tank conditions and identify possible anomalies "
            "such as unusually low water levels, abnormal inflow, or possible leakage."
        ),
        backstory=(
            "You are a water monitoring specialist who analyzes tank data "
            "to detect unusual conditions and assess their severity."
        ),
        llm=GROQ_LLM,
        verbose=True,
        allow_delegation=False,
    )