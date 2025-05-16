import os
import jinja2
import tempfile
from typing import Dict, Any
import uuid

# Map framework name to template path
TEMPLATE_PATHS = {
    "openai_agents": "openai_agents/openai_agents.py.j2",
    "pydantic_ai": "pydantic_ai/pydantic_ai.py.j2",
    "langgraph": "langgraph/langgraph.py.j2",
    "agno": "agno/agno.py.j2"
}

AGENTS_TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../agents_templates'))

def render_agent_code(framework: str, context: Dict[str, Any]) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(AGENTS_TEMPLATES_DIR),
        autoescape=False
    )
    template_path = TEMPLATE_PATHS.get(framework)
    if not template_path:
        raise ValueError(f"Unsupported framework: {framework}")
    template = env.get_template(template_path)
    return template.render(**context)

def save_agent_code(agent_id: str, code: str) -> str:
    agents_code_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../generated_agents'))
    os.makedirs(agents_code_dir, exist_ok=True)
    file_path = os.path.join(agents_code_dir, f"{agent_id}.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    return file_path

def get_agent_id(agent_info: dict) -> str:
    agent_id = str(uuid.uuid4())
    agent_info['id'] = agent_id
    framework_id = agent_info['framework'].replace('_', '-')
    final_agent_id = framework_id + "-" + agent_id
    return final_agent_id[:25]

if __name__ == "__main__":
    # Simulate rendering and saving agent code for agno
    import uuid
    framework = "agno"
    context = {
        "AZURE_OPENAI_API_KEY": "09d5dfbba3474a18b2f65f8f9ca19bab",
        "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
        "AZURE_OPENAI_ENDPOINT": "https://aressgenaisvc.openai.azure.com/",
        "AZURE_OPENAI_DEPLOYMENT": "gpt4o",
        "mcp_servers": ["http://tavily.eastus.azurecontainer.io:8000/sse"],
        "system_message": "You are a helpful AI agent.",
        "agent_name": f"langgraph_{uuid.uuid4().hex[:8]}",
        "llm_model": "gpt4o"
    }
    # Ensure both mcp_servers and mcp_urls are available for template compatibility
    context["mcp_urls"] = context.get("mcp_servers", [])
    # Ensure all llm_* keys are available for template compatibility
    context["llm_api_key"] = context.get("AZURE_OPENAI_API_KEY", "")
    context["llm_endpoint"] = context.get("AZURE_OPENAI_ENDPOINT", "")
    context["llm_api_version"] = context.get("AZURE_OPENAI_API_VERSION", "")
    code = render_agent_code(framework, context)
    print("Generated code:\n", code)
    agent_id = str(uuid.uuid4())
    path = save_agent_code(agent_id, code)
    print(f"Saved agent code to: {path}")
