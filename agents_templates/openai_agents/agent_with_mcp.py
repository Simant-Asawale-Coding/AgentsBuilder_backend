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
    global agent, mcp_server
    openai_client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"]
    )
    set_default_openai_client(openai_client)
    set_tracing_disabled(True)
    mcp_server = MCPServerSse(
        params={"url": os.environ["MCP_SERVER_URL"]},
        cache_tools_list=True
    )
    await mcp_server.connect()
    system_message = "You are a helpful AI agent with access to tools."
    agent = Agent(
        name="Assistant",
        instructions=system_message,
        model=openai_chatcompletions.OpenAIChatCompletionsModel(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            openai_client=openai_client,
        ),
        mcp_servers=[mcp_server],
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
    uvicorn.run(app, host="0.0.0.0", port=80)
