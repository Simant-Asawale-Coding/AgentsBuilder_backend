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
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    input: str

# --- MCP Tool Config ---
ALL_TOOLS = [
    {"id": "tavily", "desc": "Tavily Search Tool", "url": "https://tavily34-10d85be072--abr4bs5.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io/sse"},
    {"id": "mcpserver2", "desc": "MCPServer2 Data Tool", "url": "http://mcpserver2.eastus.azurecontainer.io:8000/sse"},
]
MCP_TOOL_CONFIGS = ALL_TOOLS

# Track tool health and instances
mcp_tool_status = {tool["id"]: False for tool in MCP_TOOL_CONFIGS}
mcp_tool_instances = {tool["id"]: None for tool in MCP_TOOL_CONFIGS}

async def check_tool_health(tool_id, url):
    old_tool = mcp_tool_instances.get(tool_id)
    tool = MCPServerSse(params={"url": url}, cache_tools_list=True)
    try:
        await tool.connect()
        mcp_tool_status[tool_id] = True
        mcp_tool_instances[tool_id] = tool
        logging.info(f"Tool {tool_id} is available.")
        if old_tool and old_tool is not tool:
            try:
                await old_tool.disconnect()
            except Exception as cleanup_err:
                if "cancel scope" in str(cleanup_err):
                    logging.info(f"Suppressing known async cleanup error for tool {tool_id}")
                else:
                    logging.warning(f"Error closing old tool {tool_id}: {cleanup_err}")
    except Exception as e:
        mcp_tool_status[tool_id] = False
        if old_tool:
            try:
                await old_tool.disconnect()
            except Exception as cleanup_err:
                if "cancel scope" in str(cleanup_err):
                    logging.info(f"Suppressing known async cleanup error for tool {tool_id}")
                else:
                    logging.warning(f"Error closing tool {tool_id}: {cleanup_err}")
        mcp_tool_instances[tool_id] = None
        logging.warning(f"Tool {tool_id} unavailable: {e}")

async def background_health_checker():
    while True:
        try:
            tasks = [check_tool_health(tool["id"], tool["url"]) for tool in MCP_TOOL_CONFIGS]
            await asyncio.gather(*tasks)
        except Exception as loop_err:
            logging.error(f"Health checker loop error: {loop_err}")
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_health_checker())
    await asyncio.sleep(1)  # Give checker a moment to run on startup

# Helper to build dynamic system message
def build_system_message(available_tool_ids):
    all_tool_list = ', '.join([f"{tool['id']} ({tool['desc']})" for tool in ALL_TOOLS])
    available_list = ', '.join([tool['id'] for tool in ALL_TOOLS if tool['id'] in available_tool_ids])
    return (
        f"You are a helpful AI agent. You have access to the following tools: {all_tool_list}.\n"
        f"Currently, the following tools are available: {available_list}.\n"
        "If the user asks for a tool that is not available, inform them that the tool is under maintenance and list the available tools."
    )

# Dynamically create the Agent with available tools
async def get_current_agent():
    openai_client = AsyncAzureOpenAI(
        api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        api_version="2024-10-21",
        azure_endpoint="https://aressgenaisvc.openai.azure.com/",
        azure_deployment="gpt4o"
    )
    set_default_openai_client(openai_client)
    set_tracing_disabled(True)
    available_tools = [mcp_tool_instances[tool['id']] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_instances[tool['id']] is not None]
    available_tool_ids = [tool['id'] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_instances[tool['id']] is not None]
    system_message = build_system_message(available_tool_ids)
    return Agent(
        name="Assistant",
        instructions=system_message,
        model=openai_chatcompletions.OpenAIChatCompletionsModel(
            model="gpt4o",
            openai_client=openai_client,
        ),
        mcp_servers=available_tools,
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    available_tools = [mcp_tool_instances[tool["id"]] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool["id"]] and mcp_tool_instances[tool["id"]] is not None]
    if not available_tools:
        return {"output": "MCP Agent not available at the moment, it may be under maintenance. Please retry after some time."}
    try:
        agent = await get_current_agent()
        result = await Runner.run(
            starting_agent=agent,
            input=request.input
        )
        return {"output": result.final_output}
    except Exception as e:
        logging.error(f"Error during agent run: {e}")
        return {"output": "MCP Agent not available at the moment, it may be under maintenance. Please retry after some time."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
