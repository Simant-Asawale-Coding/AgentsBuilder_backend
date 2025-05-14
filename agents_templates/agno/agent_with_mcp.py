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
    global agent, mcp_tool
    llm = get_azure_llm()
    mcp_tool = MCPTools(url=os.environ["MCP_SERVER_URL"], transport="sse")
    await mcp_tool.__aenter__()
    system_message = "You are a helpful AI agent with access to tools."
    agent = Agent(
        model=llm,
        tools=[mcp_tool],
        system_message=system_message
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await agent.arun(request.input)
        # Try to extract a string answer from the result object
        output = result.content
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_azure_llm():
    return AzureOpenAI(
        id="gpt-4o",
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
