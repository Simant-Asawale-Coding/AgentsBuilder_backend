from python_a2a import A2AClient
from python_a2a.models.message import Message, MessageRole
from python_a2a.models.content import TextContent
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)

client = A2AClient("http://127.0.0.1:8081")
logging.info(client.get_agent_card())
app = FastAPI()

class AgentRequest(BaseModel):
    query: str


@app.post("/agent")
async def agent_endpoint(request: AgentRequest):
    # Build the message object with metadata
    logging.info(f"Received request: {request}")
    message = Message(
        content=TextContent(text=request.query),
        role=MessageRole.USER,
    )
    logging.info(f"Sending message: {message}")
    # Send message to the agent (run in threadpool for async)
    import asyncio
    loop = asyncio.get_running_loop()
    task = await loop.run_in_executor(None, client.send_message, message)
    logging.info(f"Task: {task}")
    # Optionally fetch the agent card as well (not returned here)
    return task.content.text

# For local testing
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8085)
