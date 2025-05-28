import os
from python_a2a import A2AServer, agent,skill, run_server, TaskStatus, TaskState
import asyncio
import logging


@agent(
    name="LangGraphA2AAgent",
    description="A helpful AI agent with access to LangGraph tools via MCP.",
    version="1.0.0",
    url="http://127.0.0.1:8081/"
)
class LangGraphA2AAgent(A2AServer):
    def __init__(self):
        super().__init__()

    @skill(
        name="LangGraph Web Search Agent",
        description="An AI agent that forwards queries to an external agent container.",
        tags=["langgraph web search agent", "web search agent"],
        examples=["Get the latest price of bitcoin","search the web for azure cloud services","what is the latest news about AI"]
    )
    def langgraph_web_search_agent(self, message):
        """Forward the message to the external agent at http://127.0.0.1:80/chat and return its response."""
        import httpx
        import logging
        try:
            resp = httpx.post("http://127.0.0.1:80/chat", json={"input": message}, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            return result.get("output", "No output from agent.")
        except Exception as e:
            logging.exception("Error contacting external agent:")
            return f"Error: {str(e)}"

    async def handle_task_async(self, task):
        import asyncio
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""

        if text:
            # Call your Agno agent's response function asynchronously
            response = await asyncio.get_running_loop().run_in_executor(None, self.langgraph_web_search_agent, text)
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
        import asyncio
        return asyncio.run(self.handle_task_async(task))

if __name__ == "__main__":
    agent = LangGraphA2AAgent()
    run_server(agent, port=8081)
