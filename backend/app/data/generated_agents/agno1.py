import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.tools.mcp import MCPTools
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    input: str

@app.on_event("startup")
async def startup_event():
    global agent, mcp_tools
    llm = get_azure_llm()
    mcp_urls = ["http://tavily.eastus.azurecontainer.io:8000/sse"]
    mcp_tools = []
    for url in mcp_urls:
        tool = MCPTools(url=url, transport="sse")
        await tool.__aenter__()
        mcp_tools.append(tool)
    agent = Agent(
        model=llm,
        tools=mcp_tools
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await agent.arun(request.input)
        output = result.content
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_azure_llm():
    return AzureOpenAI(
        id="gpt4o",
        api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        azure_endpoint="https://aressgenaisvc.openai.azure.com/",
        api_version="2024-02-15-preview",
        azure_deployment="gpt4o"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)