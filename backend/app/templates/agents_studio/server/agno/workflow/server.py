from python_a2a import A2AServer, run_server, skill,agent, AgentCard, AgentSkill, TaskStatus, TaskState
import logging
logging.basicConfig(level=logging.INFO)
import httpx
import asyncio

@agent(
    name="AgnoA2AAgent",
    description="A helpful AI agent with access to web search tools",
    version="1.0.0",
    url="https://agent-id.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io"
)

class A2AAgnoAgent(A2AServer):
    def __init__(self):
        super().__init__()

    @skill(
        name="Agno Web Search Agent",
        description="An AI agent that forwards queries to an external agent container.",
        tags=["agno web search agent", "web search agent"],
        examples=["Get the latest price of bitcoin","search the web for azure cloud services","what is the latest news about AI"]
    )
    def agno_web_search_agent(self, message):
        """Forward the message to the external agent at http://127.0.0.1:80/chat and return its response."""
        
        
        try:
            resp = httpx.post("http://127.0.0.1:80/chat", json={"input": message}, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            return result.get("output", "No output from agent.")
        except Exception as e:
            logging.exception("Error contacting external agent:")
            return f"Error: {str(e)}"

    async def handle_task_async(self, task):
        logging.info(f"Received task: {task}")
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        logging.info(f"Received message: {text}")

        if text:
            # Call your Agno agent's response function asynchronously
            response = await asyncio.get_running_loop().run_in_executor(None, self.agno_web_search_agent, text)
            task.artifacts = [{
                "parts": [{"type": "text", "text": response}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please provide a query for the agent."}}
            )
        return task

    def handle_task(self, task):
        return asyncio.run(self.handle_task_async(task))

if __name__ == "__main__":
    agent = A2AAgnoAgent()
    run_server(agent, port=8080)
