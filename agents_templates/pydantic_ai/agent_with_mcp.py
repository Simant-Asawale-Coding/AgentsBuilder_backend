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
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_base = os.getenv("OPENAI_API_BASE")
    openai_api_version = os.getenv("OPENAI_API_VERSION")
    openai_deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
    return OpenAIModel(
        openai_deployment_name,
        provider=AzureProvider(
            azure_endpoint=openai_api_base,
            api_version=openai_api_version,
            api_key=openai_api_key,
        ),
    )

@app.on_event("startup")
async def startup_event():
    global agent, mcp_server
    llm = get_azure_llm()
    mcp_server_url = os.environ.get("MCP_SERVER_URL")
    if not mcp_server_url:
        raise RuntimeError("MCP_SERVER_URL environment variable is required.")
    mcp_server = MCPServerHTTP(url=mcp_server_url)
    await mcp_server.__aenter__()
    agent = Agent(llm, mcp_servers=[mcp_server])

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await agent.run(request.input)
        return {"output": result.output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional: keep CLI test for local/manual testing
async def main():
    llm = get_azure_llm()
    mcp_server_url = os.environ.get("MCP_SERVER_URL")
    if not mcp_server_url:
        raise RuntimeError("MCP_SERVER_URL environment variable is required.")
    mcp_server = MCPServerHTTP(url=mcp_server_url)
    system_message = "You are a helpful AI agent with access to tools."
    agent = Agent(llm, mcp_servers=[mcp_server], system_prompt=system_message)
    async with agent.run_mcp_servers():
        result = await agent.run("can u perform a web search and find the latest value of bitcoin. also tell me the tool u called for the same")
        print(result)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
