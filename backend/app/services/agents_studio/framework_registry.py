import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
AGENTS_TEMPLATES_DIR = os.path.join(BASE_DIR, 'agents_templates')

FRAMEWORKS = [
    {
        "name": "openai_agents",
        "label": "OpenAI Agents SDK",
        "schema_path": os.path.join(AGENTS_TEMPLATES_DIR, "openai_agents", "creds_schema.json")
    },
    {
        "name": "pydantic_ai",
        "label": "Pydantic AI",
        "schema_path": os.path.join(AGENTS_TEMPLATES_DIR, "pydantic_ai", "creds_schema.json")
    },
    {
        "name": "langgraph",
        "label": "LangGraph",
        "schema_path": os.path.join(AGENTS_TEMPLATES_DIR, "langgraph", "creds_schema.json")
    },
    {
        "name": "agno",
        "label": "Agno",
        "schema_path": os.path.join(AGENTS_TEMPLATES_DIR, "agno", "creds_schema.json")
    }
]

def get_frameworks():
    frameworks = []
    for fw in FRAMEWORKS:
        frameworks.append({
            "name": fw["name"],
            "label": fw["label"]
        })
    return frameworks

def get_framework_creds_schema(framework_name: str):
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../schemas/{framework_name}_creds_schema.json"))
    if not os.path.isfile(schema_path):
        print(f"[framework_registry] Schema file not found: {schema_path}")
        return {}
    try:
        with open(schema_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[framework_registry] Failed to load schema for {framework_name} at {schema_path}: {e}")
        return {}
