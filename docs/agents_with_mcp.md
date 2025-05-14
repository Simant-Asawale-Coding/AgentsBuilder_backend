# Agents with MCP Server Tool Integration

This document details how major Python agent frameworks can bind to MCP server URLs as tools, including code-backed examples and the required Python packages for each framework.

---

## 1. OpenAI Agents SDK (with MCP tools, 100% working async SSE)

**Required Packages:**
- `openai-agents` (install via `pip install openai-agents`)
- `openai` (install via `pip install openai`)
- `python-dotenv` (for .env loading)

**Example:**
```python
import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled
from agents.models import openai_chatcompletions
from agents.mcp import MCPServerSse

load_dotenv()

async def main():
    openai_client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"]
    )
    set_default_openai_client(openai_client)
    set_tracing_disabled(True)

    mcp_server = MCPServerSse(
        params={"url": os.environ["MCP_SERVER_URL"]},
        cache_tools_list=True
    )
    await mcp_server.connect()

    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the user's question.",
        model=openai_chatcompletions.OpenAIChatCompletionsModel(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            openai_client=openai_client,
        ),
        mcp_servers=[mcp_server],
    )

    result = await Runner.run(
        starting_agent=agent,
        input="can you perform a web search and find the latest value of bitcoin? Also tell me the tool you called for the same."
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

**.env example:**
```
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
MCP_SERVER_URL=http://your-mcp-server/sse
```

- Make sure your Azure OpenAI deployment name, endpoint, and API key are correct.
- No quotes around values in the `.env` file.
- This pattern ensures full Azure compatibility and is tested to work with OpenAI Agents SDK MCP tool binding (async SSE transport).

---

## Integrating OpenAI Agents with MCP Tools and Azure OpenAI

## Overview

This guide demonstrates how to bind MCP tools (via Model Context Protocol) with an OpenAI Agent using Azure OpenAI as the LLM provider, leveraging the OpenAI Agents SDK. It includes best practices for environment setup, agent construction, and running a robust chatbot interface.

---

## Prerequisites

- Python 3.10+
- `openai` Python package (with Azure support)
- `agents` (OpenAI Agents SDK)
- MCP server running and accessible
- `.env` file with correct Azure and MCP credentials

### Example `.env` file
```
AZURE_OPENAI_API_KEY='your-azure-openai-key'
AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'
AZURE_OPENAI_DEPLOYMENT='your-deployment-name'
AZURE_OPENAI_API_VERSION='2024-02-15-preview'
MCP_SERVER_URL='http://your-mcp-server:8001/sse'
```

---

## Working Example: `agent_with_mcp.py`

```python
import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled
from agents.models import openai_chatcompletions
from agents.mcp import MCPServerSse

load_dotenv()

async def main():
    openai_client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"]
    )
    set_default_openai_client(openai_client)
    set_tracing_disabled(True)

    mcp_server = MCPServerSse(
        params={"url": os.environ["MCP_SERVER_URL"]},
        cache_tools_list=True
    )
    await mcp_server.connect()

    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the user's question.",
        model=openai_chatcompletions.OpenAIChatCompletionsModel(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            openai_client=openai_client,
        ),
        mcp_servers=[mcp_server],
    )

    print("\n--- Chatbot interface (type 'exit' or 'quit' to stop) ---")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Exiting chatbot.")
            break
        try:
            result = await Runner.run(
                starting_agent=agent,
                input=user_input
            )
            print(f"Agent: {result.final_output}")
        except Exception as e:
            print(f"[Error] {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (RuntimeError, asyncio.CancelledError) as e:
        # Suppress known shutdown errors from MCP SSE client
        if "Attempted to exit cancel scope" in str(e) or isinstance(e, asyncio.CancelledError):
            pass
        else:
            raise
```

---

## Key Points

- **Use `AsyncAzureOpenAI` and set it as the default client for the SDK.**
- **Use `openai_chatcompletions.OpenAIChatCompletionsModel` for the agent's model.**
- **Call `await mcp_server.connect()` before agent creation.**
- **Use `Runner.run` for each user input to drive the agent.**
- **Type `exit` or `quit` to end the chatbot session.**
- **Shutdown errors from the MCP SSE client are suppressed for a clean exit.**

## Troubleshooting

- If you see `RuntimeError: Attempted to exit cancel scope in a different task than it was entered in`, this is a known issue with the MCP Python SDK's async shutdown and is safely suppressed by the provided code.
- If you get `401 Unauthorized` or `invalid_api_key`, double-check your Azure OpenAI credentials in the `.env` file.
- If you get import errors for `OpenAIChatCompletionsModel`, use `from agents.models import openai_chatcompletions` and reference `openai_chatcompletions.OpenAIChatCompletionsModel`.

## References
- [OpenAI Agents SDK GitHub](https://github.com/openai/openai-agents-python)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk/issues/521)

---

**This pattern is robust and recommended for Azure OpenAI + MCP tool integration with the OpenAI Agents SDK.**

---

## 2. LangGraph (with MCP tools, 100% working async SSE)

**Required Packages:**
- `langgraph` (install via `pip install langgraph`)
- `langchain-mcp-adapters` (install via `pip install langchain-mcp-adapters`)
- `langchain-openai` (for Azure OpenAI LLMs)

**Example:**
```python
import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

def get_azure_llm():
    return AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"]
    )

async def main():
    llm = get_azure_llm()
    async with MultiServerMCPClient({
        "my_mcp": {
            "url": os.environ["MCP_SERVER_URL"],
            "transport": "sse",
        }
    }) as client:
        mcp_tools = client.get_tools()
        agent = create_react_agent(llm, mcp_tools)
        result = await agent.ainvoke({"messages": "can u perform a web search and find the latest value of bitcoin. also tell me the tool u called for the same"})
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

**.env example:**
```
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
MCP_SERVER_URL=http://your-mcp-server/sse
```

- Make sure your Azure OpenAI deployment name, endpoint, and API key are correct.
- No quotes around values in the `.env` file.
- This pattern ensures full Azure compatibility and is tested to work with LangGraph MCP tool binding (async SSE transport).

---

## 2. Agno (with MCP tools, 100% working async SSE)

**Required Packages:**
- `agno` (install via `pip install agno`)
- `azure-ai-inference` (for Azure OpenAI)
- `aiohttp`

**Example:**
```python
import os
import asyncio
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.tools.mcp import MCPTools

load_dotenv()

def get_azure_llm():
    return AzureOpenAI(
        id="gpt-4o",
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    )

async def main():
    llm = get_azure_llm()
    async with MCPTools(url=os.environ["MCP_SERVER_URL"], transport="sse") as mcp_tool:
        print(mcp_tool)  # Should show loaded functions
        agent = Agent(
            model=llm,
            tools=[mcp_tool]
        )
        result = await agent.arun("can u perform a web search and find the latest value of bitcoin. also tell me the tool u called for the same")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

**.env example:**
```
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
MCP_SERVER_URL=http://your-mcp-server/sse
```

- Make sure your Azure OpenAI deployment name, endpoint, and API key are correct.
- No quotes around values in the `.env` file.
- This pattern ensures full Azure compatibility and is tested to work with Agno MCP tool binding (async SSE transport).

---

## 3. lastmile-ai/mcp-agent

**Required Packages:**
- `mcp-agent` (install via `pip install mcp-agent`)

**Example:**
```python
from mcp_agent.agent import Agent
from mcp_agent.mcp import MCPServerHTTP

mcp_server = MCPServerHTTP(url="http://localhost:8000/sse")
agent = Agent(
    llm="openai:gpt-4o",
    mcp_servers=[mcp_server]
)
result = agent.run("Use the tool to add 10 and 15.")
print(result)
```

---

## 4. OpenAI Agents SDK

**Required Packages:**
- `openai-agents` (install via `pip install openai-agents`)

**Example:**
```python
from openai_agents import Agent
from openai_agents.mcp import MCPServerHTTP

mcp_server = MCPServerHTTP(url="http://localhost:8000/sse")
agent = Agent(
    model="gpt-4o",
    mcp_servers=[mcp_server]
)
result = agent.run("Add 4 and 6 using the tool.")
print(result)
```

---

## 5. PydanticAI (with MCP tools)

**Required Packages:**
- `pydantic_ai` (install via `pip install pydantic_ai`)

**Example:**
```python
import os
from dotenv import load_dotenv
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.mcp import MCPServerHTTP

load_dotenv()

def get_azure_llm():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_base = os.getenv("OPENAI_API_BASE")
    openai_api_version = os.getenv("OPENAI_API_VERSION")
    openai_deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
    return OpenAIModel(
        openai_deployment_name,
        provider=AzureProvider(
            azure_endpoint=openai_api_base,
            api_version=openai_api_version,
            api_key=openai_api_key,
        ),
    )

async def main():
    llm = get_azure_llm()
    mcp_server = MCPServerHTTP(url=os.environ["MCP_SERVER_URL"])
    agent = Agent(llm, mcp_servers=[mcp_server])
    async with agent.run_mcp_servers():
        result = await agent.run("can u perform a web search and find the latest value of bitcoin. also tell me the tool u called for the same")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

**.env example:**
```
OPENAI_API_KEY=your-azure-openai-key
OPENAI_API_BASE=https://your-resource-name.openai.azure.com/
OPENAI_API_VERSION=2024-02-15-preview
OPENAI_DEPLOYMENT_NAME=your-deployment-name
MCP_SERVER_URL=http://your-mcp-server/sse
```

- Make sure your Azure OpenAI deployment name, endpoint, and API key are correct.
- No quotes around values in the `.env` file.
- This pattern ensures full Azure compatibility and is tested to work with PydanticAI MCP tool binding.

---

## 6. fast-agent

**Required Packages:**
- `fast-agent-mcp` (install via `pip install fast-agent-mcp`)

**Example:**

Define your agent and MCP server in a YAML file:

**agents.yaml**
```yaml
agents:
  - name: my_agent
    llm: openai:gpt-4o
    tools:
      - type: mcp
        url: http://localhost:8000/sse
```

Run via CLI:
```bash
fast-agent run agents.yaml --message "Add 8 and 12 using the tool."
```

---

## 6. Crew-ai

**Note:** Crew-ai does not natively support using MCP servers as tools. However, you can expose CrewAI workflows as MCP servers for other agents to use. See [mcp-crew-ai](https://github.com/adam-paterson/mcp-crew-ai) for details.

---

## References & Further Reading

### Langraph
- [LangGraph PyPI](https://pypi.org/project/langgraph/)
- [LangChain MCP Adapters PyPI](https://pypi.org/project/langchain-mcp-adapters/)
- [LangGraph Docs](https://langgraph.readthedocs.io/)
- [Langchain MCP Adapters GitHub](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Example: Model Context Protocol (MCP) With LangGraph Agent](https://hub.athina.ai/blogs/model-context-protocol-mcp-with-langgraph-agent/)

### Agno
- [Agno PyPI](https://pypi.org/project/agno/)
- [Agno MCP Tools Documentation](https://docs.agno.com/tools/mcp)
- [Agno GitHub](https://github.com/agno-agi/agno)

### lastmile-ai/mcp-agent
- [mcp-agent PyPI](https://pypi.org/project/mcp-agent/)
- [mcp-agent GitHub](https://github.com/lastmile-ai/mcp-agent)

### OpenAI Agents SDK
- [openai-agents PyPI](https://pypi.org/project/openai-agents/)
- [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/mcp/)
- [OpenAI Agents GitHub](https://github.com/openai/openai-agents-python)

### fast-agent
- [fast-agent-mcp PyPI](https://pypi.org/project/fast-agent-mcp/)
- [fast-agent Docs](https://fast-agent.ai/mcp/)
- [fast-agent GitHub](https://github.com/evalstate/fast-agent)

### Crew-ai (MCP Exposure)
- [mcp-crew-ai GitHub](https://github.com/adam-paterson/mcp-crew-ai)

---

This completes the documentation for integrating MCP server tools with major Python agent frameworks. For up-to-date usage, always refer to the official documentation and repositories linked above.
