import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio

load_dotenv()

app = FastAPI()

def get_azure_llm():
    return AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"]
    )

class ChatRequest(BaseModel):
    input: str

@app.on_event("startup")
async def startup_event():
    global agent, mcp_client
    llm = get_azure_llm()
    mcp_client = MultiServerMCPClient({
        "my_mcp": {
            "url": os.environ["MCP_SERVER_URL"],
            "transport": "sse",
        }
    })
    await mcp_client.__aenter__()
    mcp_tools = mcp_client.get_tools()
    prompt = "You are a helpful AI agent with access to tools."
    agent = create_react_agent(llm, mcp_tools, prompt=prompt)

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await agent.ainvoke({"messages": request.input})
        # Always extract the content from the last message (the model's response)
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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
