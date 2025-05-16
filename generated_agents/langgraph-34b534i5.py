import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI()

def get_azure_llm():
    return AzureChatOpenAI(
        azure_endpoint="https://aressgenaisvc.openai.azure.com/",
        api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        api_version="2024-10-21",
        azure_deployment="gpt4o"
    )

from typing import List, Optional

class ChatRequest(BaseModel):
    input: str
    chat_history: Optional[List[str]] = None  # List of previous messages (user/assistant turns)

# --- MCP Tool Config ---
ALL_TOOLS = [
    {"id": "tavily", "desc": "Tavily Search Tool", "url": "https://tavily34-10d85be072--abr4bs5.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io/sse"},
    {"id": "mcpserver2", "desc": "MCPServer2 Data Tool", "url": "http://mcpserver2.eastus.azurecontainer.io:8000/sse"},
]
MCP_TOOL_CONFIGS = ALL_TOOLS

# Track tool health and instances
mcp_tool_status = {tool["id"]: False for tool in MCP_TOOL_CONFIGS}
mcp_tool_clients = {tool["id"]: None for tool in MCP_TOOL_CONFIGS}

async def check_tool_health(tool_id, url):
    old_client = mcp_tool_clients.get(tool_id)
    client = MultiServerMCPClient({tool_id: {"url": url, "transport": "sse"}})
    try:
        await client.__aenter__()
        mcp_tool_status[tool_id] = True
        mcp_tool_clients[tool_id] = client
        logging.info(f"Tool {tool_id} is available.")
        if old_client and old_client is not client:
            try:
                await old_client.__aexit__(None, None, None)
            except Exception as cleanup_err:
                if "cancel scope" in str(cleanup_err):
                    logging.info(f"Suppressing known async cleanup error for tool {tool_id}")
                else:
                    logging.warning(f"Error closing old tool {tool_id}: {cleanup_err}")
    except Exception as e:
        mcp_tool_status[tool_id] = False
        if old_client:
            try:
                await old_client.__aexit__(None, None, None)
            except Exception as cleanup_err:
                if "cancel scope" in str(cleanup_err):
                    logging.info(f"Suppressing known async cleanup error for tool {tool_id}")
                else:
                    logging.warning(f"Error closing tool {tool_id}: {cleanup_err}")
        mcp_tool_clients[tool_id] = None
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

# Helper to build dynamic system prompt
def build_system_prompt(available_tool_ids):
    all_tool_list = ', '.join([f"{tool['id']} ({tool['desc']})" for tool in ALL_TOOLS])
    available_list = ', '.join([tool['id'] for tool in ALL_TOOLS if tool['id'] in available_tool_ids])
    return (
        f"You are a helpful AI agent. You have access to the following tools: {all_tool_list}.\n"
        f"Currently, the following tools are available: {available_list}.\n"
        "If the user asks for a tool that is not available, inform them that the tool is under maintenance and list the available tools."
    )

# Dynamically create the Agent with available tools
async def get_current_agent():
    llm = get_azure_llm()
    available_clients = [mcp_tool_clients[tool['id']] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_clients[tool['id']] is not None]
    available_tool_ids = [tool['id'] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_clients[tool['id']] is not None]
    # Collect all tools from all available clients
    mcp_tools = []
    for client in available_clients:
        try:
            mcp_tools.extend(client.get_tools())
        except Exception as e:
            logging.warning(f"Could not get tools from client: {e}")
    system_prompt = build_system_prompt(available_tool_ids)
    return create_react_agent(llm, mcp_tools, prompt=system_prompt)

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
    #available_clients = [mcp_tool_clients[tool['id']] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_clients[tool['id']] is not None]
    
    try:
        agent = await get_current_agent()
        result = await agent.ainvoke({"messages": final_query})
        # Always extract the content from the last message (the model's response)
        content = ""
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            last_msg = result["messages"][-1]
            if hasattr(last_msg, "content"):
                content = last_msg.content
            elif isinstance(last_msg, dict):
                content = last_msg.get("content", "")
            else:
                content = str(last_msg)
        else:
            content = str(result)
        return {"output": content}
    except Exception as e:
        logging.error(f"Error during agent run: {e}")
        return {"output": "An error occurred while fetching the response. Please try again later and make sure the prompt follows safety guidelines."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
