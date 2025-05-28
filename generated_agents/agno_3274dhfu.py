import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.tools.mcp import MCPTools
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI()

from typing import List, Optional

class ChatRequest(BaseModel):
    input: str
    chat_history: Optional[List[str]] = None  # List of previous messages (user/assistant turns)

# --- MCP Tool Config ---
ALL_TOOLS = [
    {"id": "tavily", "desc": "Tavily Search Tool", "url": "https://tavily34-10d85be072.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io/sse"},
    {"id": "mcpserver2", "desc": "MCPServer2 Data Tool", "url": "http://mcpserver2.eastus.azurecontainer.io:8000/sse"},
]
MCP_TOOL_CONFIGS = ALL_TOOLS

# Track tool health and instances
mcp_tool_status = {tool["id"]: False for tool in MCP_TOOL_CONFIGS}
mcp_tool_instances = {tool["id"]: None for tool in MCP_TOOL_CONFIGS}

async def check_tool_health(tool_id, url):
    old_tool = mcp_tool_instances.get(tool_id)
    tool = MCPTools(url=url, transport="sse")
    try:
        await tool.__aenter__()
        mcp_tool_status[tool_id] = True
        mcp_tool_instances[tool_id] = tool
        logging.info(f"Tool {tool_id} is available.")
        if old_tool and old_tool is not tool:
            try:
                await old_tool.__aexit__(None, None, None)
            except Exception as cleanup_err:
                logging.warning(f"Error closing old tool {tool_id}: {cleanup_err}")
    except Exception as e:
        mcp_tool_status[tool_id] = False
        if old_tool:
            try:
                await old_tool.__aexit__(None, None, None)
            except Exception as cleanup_err:
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
"If the user asks for a tool that is not available, inform them that the tool is under maintenance and list the available tools.\n Please always try to use your tool to find the answer of a question"
"\n"
"You are part of a dynamic multi-agent system using the Agent2Agent (A2A) protocol. In this environment, agents collaborate to solve complex queries by passing structured request and response cards between each other, coordinated by a client workflow. You may be called upon to answer a user query directly, or to contribute partial information and recommend another agent for further processing.\n"
"\nIf u are asked a question in a normal format and not in a card format, then u are not part of a multi-agent system and u should answer the question directly by using ur available tools and without responding in a response card format.\n"
"\n"
"When you receive a task, it will be in the form of a REQUEST CARD with the following structure:\n"
"-Original_User_Question: The user's original query.\n"
"-Current_Answer_Context: A list of previous agents' answers and reasoning steps, e.g. [[1- agent_name, question asked, answer], ...]\n"
"-Available_Agents: A list of available agents in the network, with their skills and descriptions.\n"
"-Question_for_you: The specific question you are being asked to answer in this step.\n"
"\n"
"IMPORTANT: When responding, you MUST strictly follow this RESPONSE CARD format:\n\n------------------------------------------------------"
"-$$ Current_Answer_Context: [[1- agent_name, question asked, answer], [2- agent_name, question_asked, answer],[3-your_name, question_asked_to_you, your answer]]\n"
"-Answer_Context_Relevancy_Block: STRICTLY YES% / NO%\n"
"- ##Question_for_other_Agent:\n"
"**Agent_name:\n"
"**Question_for_agent:\n\n"
"----------------------------------------------------------------\n"
"\n Whenever u recieve a question in the request card format, always first understand what tools u have available, then how much part of the question can u actually find the answer '100%' using the available tools."
"\n If any part of the question can't be answered '100%' using the available tools, then u should check the avaible agents, analyse if they can answer the question, and then formulate the question to be sent to the next agent in the response card format. "
"Only respond in this format. If the answer is final and complete, set Answer_Context_Relevancy_Block to 'YES%'. Otherwise, set it to 'NO%' and specify the next agent and question in the required format. Always use the information in the request card and the current environment to answer as accurately and helpfully as possible."
    )

# Dynamically create the Agent with available tools
async def get_current_agent():
    llm = get_azure_llm()
    available_tools = [mcp_tool_instances[tool['id']] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_instances[tool['id']] is not None]
    available_tool_ids = [tool['id'] for tool in MCP_TOOL_CONFIGS if mcp_tool_status[tool['id']] and mcp_tool_instances[tool['id']] is not None]
    system_message = build_system_message(available_tool_ids)
    return Agent(model=llm, tools=available_tools, system_message=system_message)

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
        result = await agent.arun(final_query)
        output = result.content
        return {"output": output}
    except Exception as e:
        logging.error(f"Error during agent run: {e}")
        return {"output": "An error occurred while fetching the response. Please try again later and make sure the prompt follows safety guidelines."}


def get_azure_llm():
    return AzureOpenAI(
        id="gpt-4o",
        api_key="09d5dfbba3474a18b2f65f8f9ca19bab",
        azure_endpoint="https://aressgenaisvc.openai.azure.com/",
        api_version="2024-10-21",
        azure_deployment="gpt4o"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
