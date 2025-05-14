import os
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.mcp import MCPServerHTTP
import uvicorn

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    input: str

def get_azure_llm():
    return OpenAIModel(
        "gpt4o",
        provider=AzureProvider(
            azure_endpoint="https://aressgenaisvc.openai.azure.com/",
            api_version="2024-02-15-preview",
            api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        ),
    )

@app.on_event("startup")
async def startup_event():
    global agent, mcp_servers
    llm = get_azure_llm()
    mcp_servers = []
    
    Tavily = MCPServerHTTP(url="http://tavily.eastus.azurecontainer.io:8000/sse")
    await Tavily.__aenter__()
    mcp_servers.append(Tavily)
    
    system_prompt = "You are a helpful AI agent. with access to tools vaadsdas"
    agent = Agent(llm, mcp_servers=mcp_servers, system_prompt=system_prompt)

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await agent.run(request.input)
        return {"output": result.output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)