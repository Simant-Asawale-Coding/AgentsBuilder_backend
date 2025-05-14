from fastapi import APIRouter, HTTPException
from app.services.agent_registry import get_agent

router = APIRouter()

@router.get("/agents/{agent_id}/status")
def get_agent_status(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": agent.get("status", "unknown")}

@router.get("/agents/{agent_id}/endpoint")
def get_agent_endpoint(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"endpoint": agent.get("endpoint", "")}

@router.post("/agents/{agent_id}/query")
def query_agent(agent_id: str, body: dict):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Placeholder: In production, proxy this query to the running agent
    return {"result": f"Query received for agent {agent_id} (not yet implemented)"}

@router.get("/agents/{agent_id}/tools")
def get_agent_tools(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"tools": agent.get("tools", [])}
