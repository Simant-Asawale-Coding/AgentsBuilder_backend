import uuid
from typing import Dict

# In-memory agent registry (can be replaced with DB later)
agents: Dict[str, dict] = {}

def register_agent(agent_info: dict) -> str:
    agent_id = str(uuid.uuid4())
    agent_info['id'] = agent_id
    agents[agent_id] = agent_info
    framework_id = agent_info['framework'].replace('_', '-')
    final_agent_id = framework_id + "-" + agent_id
    return final_agent_id[:25]

def get_agent(agent_id: str) -> dict:
    return agents.get(agent_id)

def update_agent(agent_id: str, updates: dict):
    if agent_id in agents:
        agents[agent_id].update(updates)


def get_all_agents():
    return list(agents.values())
