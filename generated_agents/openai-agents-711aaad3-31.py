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

from typing import List, Optional
import logging
logging.basicConfig(level=logging.INFO)

class ChatRequest(BaseModel):
    input: str
    chat_history: Optional[List[str]] = None  # List of previous messages (user/assistant turns)

# --- MCP Tool Config ---
ALL_TOOLS = [
    
    {"id": "Tavily", "desc": "Tavily", "url": "https://tavily34-10d85be072.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io/sse"},
    
    {"id": "SOQL", "desc": "SOQL", "url": "http://mcpserver2.eastus.azurecontainer.io:8000/sse"},
    
]
MCP_TOOL_CONFIGS = ALL_TOOLS

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

def build_system_message(available_tool_ids):
    all_tool_list = ', '.join([f"{tool['id']} ({tool['desc']})" for tool in ALL_TOOLS])
    available_list = ', '.join([tool['id'] for tool in ALL_TOOLS if tool['id'] in available_tool_ids])
    return (
        f"You are a helpful AI agent. You have access to the following tools: {all_tool_list}.\n"
        f"Currently, the following tools are available: {available_list}.\n"
        "If the user asks for a tool that is not available, inform them that the tool is under maintenance and list the available tools."
    )

async def get_current_agent():
    openai_client = AsyncAzureOpenAI(
        api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        api_version="2024-02-15-preview",
        azure_endpoint="https://aressgenaisvc.openai.azure.com/",
        azure_deployment="gpt4o"
    )
    set_default_openai_client(openai_client)
    set_tracing_disabled(True)
    available_tools = [mcp_tool_instances[tool['id']] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_instances[tool['id']] is not None]
    available_tool_ids = [tool['id'] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_instances[tool['id']] is not None]
    system_message = build_system_message(available_tool_ids)
    return Agent(
        name="agent_openai_agents_75b03a9c",
        instructions=system_message,
        model=openai_chatcompletions.OpenAIChatCompletionsModel(
            model="gpt4o",
            openai_client=openai_client,
        ),
        mcp_servers=available_tools,
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    # Format chat history as a natural conversation transcript
    chat_history = request.chat_history or []
    conversation = []
    for msg in chat_history:
        msg_strip = msg.strip()
        if msg_strip.lower().startswith("user:"):
            conversation.append(f"User: {msg_strip[5:].strip()}")
        elif msg_strip.lower().startswith("assistant:"):
            conversation.append(f"Assistant: {msg_strip[10:].strip()}")
        else:
            conversation.append(msg_strip)
    conversation.append(f"User: {request.input.strip()}")
    final_query = "Conversation so far:\n" + "\n".join(conversation)
    try:
        agent = await get_current_agent()
        result = await Runner.run(
            starting_agent=agent,
            input=final_query
        )
        return {"output": result.final_output}
    except Exception as e:
        logging.error(f"Error during agent run: {e}")
        return {"output": "An error occurred while fetching the response. Please try again later and make sure the prompt follows safety guidelines."}

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=80)
    except (RuntimeError, asyncio.CancelledError) as e:
        if "Attempted to exit cancel scope" in str(e) or isinstance(e, asyncio.CancelledError):
            pass