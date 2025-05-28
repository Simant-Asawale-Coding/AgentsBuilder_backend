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

app = FastAPI()

from typing import List, Optional, Dict, Any
from azure.appconfiguration import AzureAppConfigurationClient
from pydantic_settings import BaseSettings
import pyodbc
import datetime

class ChatRequest(BaseModel):
    input: str
    conversation_id: str
    user_id: int
    agent_id: str

# Azure App Configuration
connection_string = "Endpoint=https://agents-builder-app-config.azconfig.io;Id=HTIL;Secret=CqSfSRB6toHJYmWozz0XAet8tqSFUyLPw66osOnxdQ5be9YDtiE6JQQJ99BEACYeBjFdkwbiAAACAZAC337W"
client = AzureAppConfigurationClient.from_connection_string(connection_string)

def get_config_value(key, label=None):
    azure_key = key.replace("_", ":")
    try:
        setting = client.get_configuration_setting(key=azure_key, label=label)
        if setting is None or setting.value is None:
            raise ValueError(f"Configuration key '{azure_key}' with label '{label}' not found in Azure App Configuration.")
        return setting.value
    except Exception as e:
        raise ValueError(f"Error retrieving key '{azure_key}' with label '{label}': {str(e)}")

class AppSettings(BaseSettings):
    agentsbuilder_mssqlconnectionstring: str = get_config_value("agentsbuilder:dbconnectionstring", label="mssql")
    agentsbuilder_chathistorytable: str = get_config_value("agentsbuilder:chathistorytable", label="mssql-table")

CONN_STR = AppSettings().agentsbuilder_mssqlconnectionstring

def get_connection():
    return pyodbc.connect(CONN_STR,timeout=60)

def fetch_chat_history(conversation_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    table_name = AppSettings().agentsbuilder_chathistorytable
    try:
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE conversation_id = ? AND (soft_delete = 0 OR soft_delete IS NULL) ORDER BY created_at",
            (conversation_id,)
        )
    except Exception:
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        )
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def insert_chat_message(data: Dict[str, Any]):
    """
    Robustly insert a chat message into the chat_history table, handling both auto-increment and non-auto-increment message_id schemas.
    If message_id is required, automatically generates the next available id.
    """
    import logging
    conn = get_connection()
    cursor = conn.cursor()
    table_name = AppSettings().agentsbuilder_chathistorytable
    try:
        # Try insert without message_id (auto-increment case)
        cursor.execute(
            f"INSERT INTO {table_name} (conversation_id, user_id, agent_id, sender, message_text, created_at, attachments) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data['conversation_id'], data['user_id'], data['agent_id'], data['sender'],
                data.get('message_text'), data.get('created_at'), data.get('attachments')
            )
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        # Check if error is due to missing message_id
        if hasattr(e, 'args') and any('message_id' in str(arg) for arg in e.args):
            logging.warning("message_id required in insert; falling back to manual id generation.")
            # Use a UUID for message_id to guarantee uniqueness
            import uuid
            next_id = str(uuid.uuid4())
            cursor.execute(
                f"INSERT INTO {table_name} (message_id, conversation_id, user_id, agent_id, sender, message_text, created_at, attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    next_id, data['conversation_id'], data['user_id'], data['agent_id'], data['sender'],
                    data.get('message_text'), data.get('created_at'), data.get('attachments')
                )
            )
            conn.commit()
            return next_id
        else:
            logging.error(f"Failed to insert chat message: {e}")
            raise

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
    # Fetch chat history from DB
    chat_history = fetch_chat_history(request.conversation_id)

    # Remove the last message (if any)
    if chat_history:
        chat_history_for_prompt = chat_history[:-1]
    else:
        chat_history_for_prompt = []

    # Format chat history for prompt
    history_lines = []
    for msg in chat_history_for_prompt:
        sender = msg.get('sender', 'user')
        text = msg.get('message_text', '')
        if sender.lower() == 'user':
            history_lines.append(f"User: {text}")
        else:
            history_lines.append(f"Assistant: {text}")

    # Build the final query prompt
    final_query = f"current_user_query: {request.input}\n\nchat_history: {'\n'.join(history_lines)}"
    try:
        agent = await get_current_agent()
        result = await Runner.run(
            starting_agent=agent,
            input=final_query
        )
        # Insert agent's answer into chat_history
        insert_chat_message({
            'conversation_id': request.conversation_id,
            'user_id': request.user_id,
            'agent_id': request.agent_id,
            'sender': 'agent',
            'message_text': result.final_output,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'attachments': None
        })
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