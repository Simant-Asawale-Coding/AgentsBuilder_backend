# Tool registry service (static for now, pluggable for future)
# deployed tools.
tools = [
    {
        "name": "Tavily",
        "description": "Web search tool for retrieving up-to-date information from the internet.",
        "url": "http://tavily.eastus.azurecontainer.io:8000/sse",
        "type": "web_search",
        "transport": "sse"
    },
    {
        "name": "SOQL",
        "description": "Query tool for accessing Salesforce database using SOQL queries.",
        "url": "http://mcpserver2.eastus.azurecontainer.io:8000/sse",
        "type": "salesforce_database_query",
        "transport": "sse"
    }
]

def get_tools():
    return tools
