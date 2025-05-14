import os
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled
from openai import AsyncAzureOpenAI
from agents.models import openai_chatcompletions
from agents.mcp import MCPServerSse
import uvicorn

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    input: str

@app.on_event("startup")
async def startup_event():
    global agent, mcp_servers
    openai_client = AsyncAzureOpenAI(
        api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        api_version="2024-02-15-preview",
        azure_endpoint="https://aressgenaisvc.openai.azure.com/",
        azure_deployment="gpt4o"
    )
    set_default_openai_client(openai_client)
    set_tracing_disabled(True)
    mcp_servers = []
    
    Tavily = MCPServerSse(
        params={"url": "http://tavily.eastus.azurecontainer.io:8000/sse"},
        cache_tools_list=True
    )
    await Tavily.connect()
    mcp_servers.append(Tavily)
    
    system_message = "You are a helpful AI agent. with access to tools vaadsdas"
    agent = Agent(
        name="agent_openai_agents_62b028ae",
        instructions=system_message,
        model=openai_chatcompletions.OpenAIChatCompletionsModel(
            model="gpt4o",
            openai_client=openai_client,
        ),
        mcp_servers=mcp_servers,
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await Runner.run(
            starting_agent=agent,
            input=request.input
        )
        return {"output": result.final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=80)
    except (RuntimeError, asyncio.CancelledError) as e:
        if "Attempted to exit cancel scope" in str(e) or isinstance(e, asyncio.CancelledError):
            pass