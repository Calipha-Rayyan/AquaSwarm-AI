"""Authoritative Agent Registry for AquaSwarm AI.

Defines the 8 operational specialist AI agents in the swarm, their responsibilities,
pipeline stages, execution triggers, and distinguishes AI agents from the human
authorization gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AgentSpec:
    key: str
    name: str
    module_path: str
    stage: str
    role_description: str
    is_conditional: bool = False
    requires_human_gate_after: bool = False


# The 8 Operational AI Specialist Agents
SWARM_AGENTS: List[AgentSpec] = [
    AgentSpec(
        key="demand",
        name="Demand Agent",
        module_path="agents.demand",
        stage="Demand",
        role_description="Calculates water shortage, cover days, net drawdown, and reserve deficit.",
    ),
    AgentSpec(
        key="anomaly",
        name="Anomaly Agent",
        module_path="agents.anomaly",
        stage="Anomaly",
        role_description="Detects rapid depletion, consumption spikes vs recent baseline, and abnormal drawoff.",
    ),
    AgentSpec(
        key="supply",
        name="Supply Agent",
        module_path="agents.supply",
        stage="Supply",
        role_description="Evaluates tanker suppliers, availability, pricing, distance, and transit ETAs.",
    ),
    AgentSpec(
        key="allocation",
        name="Allocation Agent",
        module_path="agents.allocation",
        stage="Allocation",
        role_description="Sizes delivery quota deterministically against shortages and supplier capacity.",
        requires_human_gate_after=True,
    ),
    AgentSpec(
        key="approval_review",
        name="Approval Review Agent",
        module_path="agents.approval",
        stage="Approval",
        role_description="AI risk reviewer briefing the human manager before physical dispatch authorization.",
    ),
    AgentSpec(
        key="delivery",
        name="Delivery Agent",
        module_path="agents.delivery",
        stage="Delivery",
        role_description="Coordinates tanker dispatch, logs departure, and tracks in-transit logistics.",
    ),
    AgentSpec(
        key="verification",
        name="Verification Agent",
        module_path="agents.verification",
        stage="Verification",
        role_description="Audits physically received volume against approved quota and flags discrepancies.",
    ),
    AgentSpec(
        key="replanning",
        name="Replanning Agent",
        module_path="agents.replanning",
        stage="Replanning",
        role_description="Formulates autonomous recovery actions when an allocation is rejected or verification fails.",
        is_conditional=True,
    ),
]

_AGENT_BY_KEY: Dict[str, AgentSpec] = {a.key: a for a in SWARM_AGENTS}
_AGENT_BY_NAME: Dict[str, AgentSpec] = {a.name: a for a in SWARM_AGENTS}
_AGENT_BY_STAGE: Dict[str, AgentSpec] = {a.stage: a for a in SWARM_AGENTS}
OPERATIONAL_AGENTS: Dict[str, AgentSpec] = _AGENT_BY_NAME


def get_agent_registry() -> List[AgentSpec]:
    """Return all 8 configured operational AI agents."""
    return list(SWARM_AGENTS)


def get_configured_agent_count() -> int:
    """Return total configured AI agents count (8)."""
    return len(SWARM_AGENTS)


def get_agent_by_key(key: str) -> Optional[AgentSpec]:
    return _AGENT_BY_KEY.get(key.lower().strip())


def get_agent_by_name(name: str) -> Optional[AgentSpec]:
    return _AGENT_BY_NAME.get(name.strip())


get_agent_spec = get_agent_by_name


def get_agent_by_stage(stage: str) -> Optional[AgentSpec]:
    return _AGENT_BY_STAGE.get(stage.strip())


def get_active_agents_from_state(workflow_state: Any) -> List[str]:
    """Return list of distinct AI agent names that were actively invoked in a workflow state."""
    if not workflow_state:
        return []

    recorded = getattr(workflow_state, "ai_agents", []) or []
    normalized: List[str] = []
    seen = set()

    for item in recorded:
        item_str = str(item).strip()
        matched = None
        for agent in SWARM_AGENTS:
            if agent.name.lower() in item_str.lower() or agent.key in item_str.lower():
                matched = agent.name
                break
        matched = matched or item_str
        if matched not in seen:
            seen.add(matched)
            normalized.append(matched)

    return normalized
