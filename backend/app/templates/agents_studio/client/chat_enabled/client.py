from python_a2a import A2AClient
from python_a2a.models.message import Message, MessageRole
from python_a2a.models.content import TextContent, Metadata
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging
from python_a2a.models.message import Metadata

logging.basicConfig(level=logging.INFO, force=True)

class A2AAgnoClient(A2AClient):
    def __init__(self, url):
        super().__init__(url)

    def send_message(self, message: Message, user_id: int, agent_id: str, conversation_id: str):
        # Ensure message has metadata and custom_fields
        
        if not hasattr(message, "metadata") or message.metadata is None:
            message.metadata = Metadata(custom_fields={})
        if not hasattr(message.metadata, "custom_fields") or message.metadata.custom_fields is None:
            message.metadata.custom_fields = {}
        # Inject/overwrite the custom_fields
        message.metadata.custom_fields.update({
            "user_id": user_id,
            "agent_id": agent_id,
            "conversation_id": conversation_id
        })
        return super().send_message(message)

client = A2AAgnoClient("http://127.0.0.1:8081")
logging.info(client.get_agent_card())
app = FastAPI()

class AgentRequest(BaseModel):
    query: str
    conversation_id: str
    user_id: int
    agent_id: str

@app.post("/agent")
async def agent_endpoint(request: AgentRequest):
    # Build the message object with metadata
    logging.info(f"Received request: {request}")
    message = Message(
        content=TextContent(text=request.query),
        role=MessageRole.USER
    )
    logging.info(f"Sending message: {message}")
    # Send message to the agent (run in threadpool for async)
    import asyncio
    loop = asyncio.get_running_loop()
    try:
        # Call our overridden send_message that injects metadata
        task = await loop.run_in_executor(
            None,
            client.send_message,
            message,
            request.user_id,
            request.agent_id,
            request.conversation_id
        )
    except Exception as e:
        logging.exception("Error sending message:")
        return f"Error: {str(e)}"
    logging.info(f"Task: {task}")
    # Directly return the agent answer from content.text (server returns a Message now)
    return {"text": task.content.text}

# For local testing
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8085)
