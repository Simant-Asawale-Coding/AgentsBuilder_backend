# Tool registry service (static for now, pluggable for future)
# deployed tools.
tools = [
    {
        "name": "Tavily",
        "description": "Web search tool for retrieving up-to-date information from the internet.",
        "url": "https://tavily34-10d85be072--abr4bs5.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io/sse",
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
