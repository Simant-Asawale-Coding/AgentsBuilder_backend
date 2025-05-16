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
        api_version="2024-02-15-preview",
        azure_deployment="gpt4o"
    )

from typing import List, Optional

class ChatRequest(BaseModel):
    input: str
    chat_history: Optional[List[str]] = None  # List of previous messages (user/assistant turns)

import logging
logging.basicConfig(level=logging.INFO)

# --- MCP Tool Config ---
ALL_TOOLS = [
    
    {"name": "Tavily", "url": "https://tavily34-10d85be072.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io/sse", "transport": "sse"},
    
    {"name": "SOQL", "url": "http://mcpserver2.eastus.azurecontainer.io:8000/sse", "transport": "sse"},
    
]
MCP_TOOL_CONFIGS = ALL_TOOLS

mcp_tool_status = {tool["name"]: False for tool in MCP_TOOL_CONFIGS}
mcp_tool_instances = {tool["name"]: None for tool in MCP_TOOL_CONFIGS}

async def check_tool_health(tool_name, url):
    try:
        client = MultiServerMCPClient({tool_name: {"url": url, "transport": "sse"}})
        await client.__aenter__()
        mcp_tool_status[tool_name] = True
        mcp_tool_instances[tool_name] = client
    except Exception as e:
        mcp_tool_status[tool_name] = False
        mcp_tool_instances[tool_name] = None
        logging.warning(f"Tool {tool_name} unavailable: {e}")

async def background_health_checker():
    while True:
        try:
            tasks = [check_tool_health(tool["name"], tool["url"]) for tool in MCP_TOOL_CONFIGS]
            await asyncio.gather(*tasks)
        except Exception as loop_err:
            logging.error(f"Health checker loop error: {loop_err}")
        await asyncio.sleep(30)

def build_system_message(available_tool_names, user_system_message):
    all_tool_list = ', '.join([f"{tool['name']} ({tool['url']})" for tool in ALL_TOOLS])
    available_list = ', '.join([tool['name'] for tool in ALL_TOOLS if tool['name'] in available_tool_names])
    return (
        (user_system_message.strip() + "\n\n") +
        f"You are a helpful AI agent. You were assigned the given tools: {all_tool_list}.\n"
        f"Currently, the following tools are available: {available_list}.\n"
        "If the user asks for a tool that is not available, inform them that the tool is down and might be under maintenance and list the available tools."
    )

@app.on_event("startup")
async def startup_event():
    global agent
    llm = get_azure_llm()
    asyncio.create_task(background_health_checker())
    await asyncio.sleep(1)  # Give checker a moment to run on startup
    # Gather all available tools from healthy MCP clients
    available_tools = []
    available_tool_names = []
    for tool in MCP_TOOL_CONFIGS:
        name = tool['name']
        if mcp_tool_status[name] and mcp_tool_instances[name] is not None:
            client = mcp_tool_instances[name]
            # Get tools from the MCP client (should be a list)
            try:
                tools = client.get_tools()
                available_tools.extend(tools)
                available_tool_names.append(name)
            except Exception as e:
                logging.warning(f"Failed to get tools from {name}: {e}")
    user_system_message = "You are a helpful AI agent."
    system_message = build_system_message(available_tool_names, user_system_message)
    agent = create_react_agent(llm, available_tools, prompt=system_message)

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
        # Always re-instantiate agent with up-to-date tools and system message
        # Gather all available tools from healthy MCP clients
        available_tools = []
        available_tool_names = []
        for tool in MCP_TOOL_CONFIGS:
            name = tool['name']
            if mcp_tool_status[name] and mcp_tool_instances[name] is not None:
                client = mcp_tool_instances[name]
                try:
                    tools = client.get_tools()
                    available_tools.extend(tools)
                    available_tool_names.append(name)
                except Exception as e:
                    logging.warning(f"Failed to get tools from {name}: {e}")
        user_system_message = "You are a helpful AI agent."
        system_message = build_system_message(available_tool_names, user_system_message)
        agent = create_react_agent(get_azure_llm(), available_tools, prompt=system_message)
        result = await agent.ainvoke({"messages": final_query})
        content = ""
        if (
            isinstance(result, dict) and "messages" in result 
            and isinstance(result["messages"], list) and result["messages"]
        ):
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
        logging.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)