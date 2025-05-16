from pydantic import BaseModel, Field
from typing import List, Dict, Any
######## add told_id
class MCPServerConfig(BaseModel):
    name: str
    url: str
    transport: str

class AgentCreateRequest(BaseModel):
    tools: List[MCPServerConfig]
    prompt: str
    framework: str
    credentials: Dict[str, Any]

class AgentInfo(BaseModel):
    id: str
    status: str
    endpoint: str
    tools: List[MCPServerConfig]
    framework: str
    prompt: str
