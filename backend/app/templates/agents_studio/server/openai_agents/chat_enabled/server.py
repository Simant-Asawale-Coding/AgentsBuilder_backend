from python_a2a import A2AServer, run_server, skill,agent, AgentCard, AgentSkill, TaskStatus, TaskState
import logging
logging.basicConfig(level=logging.INFO)
from python_a2a.models.message import Message, TextContent, MessageRole
# If you need async support for tools, you can use asyncio in skills
import asyncio



@agent(
    name="OpenaiA2AAgent",
    description="A helpful Openai agent with access to crypto investment tools",
    version="1.0.0",
    url="http://127.0.0.1:8081/"
)
class OpenaiA2AAgent(A2AServer):
    def __init__(self):
        super().__init__()

    @skill(
        name="Openai Agent",
        description="An AI agent that invests in crypto currency",
        tags=["Openai Agent", "crypto"],
        examples=["Invest in bitcoin for me", "Invest in ethereum for me", "Invest in dogecoin for me"]
    )
    def openai_agent(self, message, conversation_id, user_id, agent_id):
        """Forward the message to the external agent at http://127.0.0.1:80/chat and return its response."""
        import httpx
        import logging
        try:
            resp = httpx.post("http://127.0.0.1:80/chat", json={"input": message, "conversation_id": conversation_id, "user_id": user_id, "agent_id": agent_id}, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            return result.get("output", "No output from agent.")
        except Exception as e:
            logging.exception("Error contacting external agent:")
            return f"Error: {str(e)}"
        
    async def handle_message_async(self, message):
        

        # Defensive extraction of content and metadata/custom_fields
        message_data = message or {}
        if isinstance(message_data, dict):
            content = message_data.get("content", {})
            if isinstance(content, dict):
                text = content.get("text", "")
            elif hasattr(content, "text"):
                text = content.text
            else:
                text = ""
        else:
            content = getattr(message_data, "content", None)
            if isinstance(content, dict):
                text = content.get("text", "")
            elif hasattr(content, "text"):
                text = content.text
            else:
                text = ""
        logging.info(f"[A2A Server] Extracted message text: {text}")

        # Extract metadata/custom_fields
        def get_custom_fields(msg):
            if isinstance(msg, dict):
                metadata = msg.get("metadata", {})
                return metadata.get("custom_fields", {})
            else:
                metadata = getattr(msg, "metadata", None)
                if metadata:
                    return getattr(metadata, "custom_fields", {})
            return {}

        custom_fields = get_custom_fields(message)
        conversation_id = custom_fields.get("conversation_id")
        user_id = custom_fields.get("user_id")
        agent_id = custom_fields.get("agent_id")

        logging.info(f"Extracted fields: conversation_id={conversation_id}, user_id={user_id}, agent_id={agent_id}")
        logging.info(f"Received message text: {text}")

        if text:
            # Call your Agno agent's response function asynchronously
            response = await asyncio.get_running_loop().run_in_executor(
                None, self.openai_agent, text, conversation_id, user_id, agent_id
            )
            logging.info(f"Response from Openai agent @#$#: {response}")
            agent_message = Message(
                content=TextContent(text=response),
                role=MessageRole.AGENT
            )
            return agent_message
        else:
            agent_message = Message(
                content=TextContent(text="Please provide a query for the agent."),
                role=MessageRole.AGENT
            )
            return agent_message

    def handle_message(self, message):
        import asyncio
        return asyncio.run(self.handle_message_async(message))

if __name__ == "__main__":
    agent = OpenaiA2AAgent()
    run_server(agent, port=8081)
