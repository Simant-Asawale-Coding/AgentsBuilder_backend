import pyodbc
import json
from typing import List, Dict, Any, Optional
from app.utils.configuration.appsettings import AppSettings

# Connection string should be set via environment/config in production
CONN_STR = AppSettings().agentsbuilder_mssqlconnectionstring

def get_connection():
    return pyodbc.connect(CONN_STR,timeout=30)

# 1. Marketplace Tools CRUD

def fetch_all_marketplace_tools() -> List[Dict[str, Any]]:
    """
    Fetch all marketplace tools.
    Example:
        tools = fetch_all_marketplace_tools()
        # Returns: List of dicts, each dict is a tool row
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM marketplace_tools WHERE soft_delete = 0')
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def insert_marketplace_tool(data: Dict[str, Any]):
    """
    Insert a new marketplace tool.
    Example:
        insert_marketplace_tool({
            'admin_id': 1,
            'name': 'ToolName',
            'description': 'desc',
            'creds_schema': '{}',
            'sha': 'sha1',
            'tool_details': 'details'
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO marketplace_tools (admin_id, name, description, creds_schema, sha, tool_details)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['admin_id'], data.get('name'), data.get('description'), data.get('creds_schema'), data.get('sha'), data.get('tool_details')))
    conn.commit()
    return cursor.lastrowid

def update_marketplace_tool(tool_id: int, data: Dict[str, Any]):
    """
    Update a marketplace tool.
    Example:
        update_marketplace_tool(1, {
            'admin_id': 2,
            'name': 'NewName',
            'description': 'new desc',
            'creds_schema': '{}',
            'sha': 'sha2',
            'tool_details': 'details2'
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE marketplace_tools SET admin_id=?, name=?, description=?, creds_schema=?, sha=?, tool_details=? WHERE tool_id=?
    ''', (data['admin_id'], data.get('name'), data.get('description'), data.get('creds_schema'), data.get('sha'), data.get('tool_details'), tool_id))
    conn.commit()
    return cursor.rowcount

def soft_delete_marketplace_tool(tool_id: int):
    """
    Soft delete a marketplace tool.
    Example:
        soft_delete_marketplace_tool(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE marketplace_tools SET soft_delete=1 WHERE tool_id=?', (tool_id,))
    conn.commit()
    return cursor.rowcount


def delete_marketplace_tool(tool_id: int):
    """
    Permanently delete a marketplace tool.
    Example:
        delete_marketplace_tool(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM marketplace_tools WHERE tool_id=?', (tool_id,))
    conn.commit()
    return cursor.rowcount

# 2. Marketplace Tools Deployed

def fetch_marketplace_tools_deployed_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch all deployed marketplace tools for a user.
    Example:
        fetch_marketplace_tools_deployed_by_user(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM marketplace_tools_deployed WHERE user_id = ? AND soft_delete = 0', (user_id,))
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def insert_marketplace_tools_deployed(data: Dict[str, Any]):
    """
    Insert a deployed marketplace tool.
    Example:
        insert_marketplace_tools_deployed({
            'user_id': 1,
            'deployment_id': 100,
            'description': 'desc',
            'details': 'details',
            'tool_id': 2,
            'sha': 'sha1',
            'run_id': 'run1',
            'url': 'http://...',
            'status': 'running',
            'error': None
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO marketplace_tools_deployed (user_id, deployment_id, description, details, tool_id, sha, run_id, url, status, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['user_id'], data['deployment_id'], data.get('description'), data.get('details'),
        data.get('tool_id'), data.get('sha'), data.get('run_id'), data.get('url'),
        data.get('status'), data.get('error')
    ))
    conn.commit()
    return cursor.rowcount

def update_marketplace_tools_deployed(user_id: int, deployment_id: int, data: Dict[str, Any]):
    """
    Update a deployed marketplace tool.
    Example:
        update_marketplace_tools_deployed(1, 100, {
            'description': 'new desc',
            'details': 'new details',
            'tool_id': 2,
            'sha': 'sha2',
            'run_id': 'run2',
            'url': 'http://...',
            'status': 'paused',
            'error': 'none'
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE marketplace_tools_deployed SET description=?, details=?, tool_id=?, sha=?, run_id=?, url=?, status=?, error=?
        WHERE user_id=? AND deployment_id=?
    ''', (
        data.get('description'), data.get('details'), data.get('tool_id'), data.get('sha'),
        data.get('run_id'), data.get('url'), data.get('status'), data.get('error'),
        user_id, deployment_id
    ))
    conn.commit()
    return cursor.rowcount

def soft_delete_marketplace_tools_deployed(user_id: int, deployment_id: int):
    """
    Soft delete a deployed marketplace tool.
    Example:
        soft_delete_marketplace_tools_deployed(1, 100)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE marketplace_tools_deployed SET soft_delete=1 WHERE user_id=? AND deployment_id=?', (user_id, deployment_id))
    conn.commit()
    return cursor.rowcount


def delete_marketplace_tools_deployed(user_id: int, deployment_id: int):
    """
    Permanently delete a deployed marketplace tool.
    Example:
        delete_marketplace_tools_deployed(1, 100)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM marketplace_tools_deployed WHERE user_id=? AND deployment_id=?', (user_id, deployment_id))
    conn.commit()
    return cursor.rowcount

# 3. Custom Tools

def fetch_custom_tools_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch all custom tools for a user.
    Example:
        fetch_custom_tools_by_user(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM custom_tools WHERE user_id = ? AND soft_delete = 0', (user_id,))
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def fetch_custom_tools_by_type(user_id: int, type_value: str) -> List[Dict[str, Any]]:
    """
    Fetch all custom tools for a user by type ('files' or 'url').
    Example:
        fetch_custom_tools_by_type(1, 'files')
        fetch_custom_tools_by_type(1, 'url')
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM custom_tools WHERE user_id = ? AND type = ? AND soft_delete = 0', (user_id, type_value))
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def insert_custom_tool(data: Dict[str, Any]):
    """
    Insert a custom tool.
    Example:
        insert_custom_tool({
            'user_id': 1,
            'name': 'CustomTool',
            'description': 'desc',
            'details': 'details',
            'sha': 'sha1',
            'status': 'added',
            'url': 'http://...',
            'type': 'files',
            'error': None
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO custom_tools (user_id, name, description, details, sha, status, url, type, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['user_id'], data.get('name'), data.get('description'), data.get('details'),
        data.get('sha'), data.get('status'), data.get('url'), data.get('type'), data.get('error')
    ))
    conn.commit()
    return cursor.rowcount

def update_custom_tool(user_id: int, data: Dict[str, Any]):
    """
    Update a custom tool.
    Example:
        update_custom_tool(1, {
            'name': 'CustomTool2',
            'description': 'desc2',
            'details': 'details2',
            'sha': 'sha2',
            'status': 'running',
            'url': 'http://...',
            'type': 'url',
            'error': 'none'
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE custom_tools SET name=?, description=?, details=?, sha=?, status=?, url=?, type=?, error=?
        WHERE user_id=?
    ''', (
        data.get('name'), data.get('description'), data.get('details'), data.get('sha'),
        data.get('status'), data.get('url'), data.get('type'), data.get('error'), user_id
    ))
    conn.commit()
    return cursor.rowcount

def soft_delete_custom_tool(user_id: int):
    """
    Soft delete a custom tool.
    Example:
        soft_delete_custom_tool(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE custom_tools SET soft_delete=1 WHERE user_id=?', (user_id,))
    conn.commit()
    return cursor.rowcount

def delete_custom_tool(user_id: int):
    """
    Permanently delete a custom tool.
    Example:
        delete_custom_tool(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM custom_tools WHERE user_id=?', (user_id,))
    conn.commit()
    return cursor.rowcount

# 4. Marketplace Agents

def fetch_all_marketplace_agents() -> List[Dict[str, Any]]:
    """
    Fetch all marketplace agents, including resolved tool data.
    Example:
        fetch_all_marketplace_agents()
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM marketplace_agents WHERE soft_delete = 0')
    columns = [column[0] for column in cursor.description]
    agents = [dict(zip(columns, row)) for row in cursor.fetchall()]
    # For each agent, resolve tools
    for agent in agents:
        tool_ids = []
        if agent.get('tools'):
            try:
                tool_ids = json.loads(agent['tools']) if isinstance(agent['tools'], str) else agent['tools']
            except Exception:
                tool_ids = []
        if isinstance(tool_ids, list) and tool_ids:
            placeholders = ','.join(['?']*len(tool_ids))
            tool_cursor = conn.cursor()
            tool_cursor.execute(f'SELECT * FROM marketplace_tools WHERE tool_id IN ({placeholders}) AND soft_delete = 0', tool_ids)
            tool_columns = [column[0] for column in tool_cursor.description]
            agent['tools_data'] = [dict(zip(tool_columns, row)) for row in tool_cursor.fetchall()]
        else:
            agent['tools_data'] = []
        # Ensure chat_enabled and workflow_enabled are returned as bool
        agent['chat_enabled'] = bool(agent.get('chat_enabled', 0))
        agent['workflow_enabled'] = bool(agent.get('workflow_enabled', 0))
    return agents

def insert_marketplace_agent(data: Dict[str, Any]):
    """
    Insert a new marketplace agent.
    Example:
        insert_marketplace_agent({
            'name': 'AgentName',
            'description': 'desc',
            'details': 'details',
            'system_prompt': 'prompt',
            'tools': [1, 2],
            'creds_schema': '{}',
            'framework': 'agno',
            'chat_enabled': True,
            'workflow_enabled': False
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO marketplace_agents (name, description, details, system_prompt, tools, creds_schema, framework, chat_enabled, workflow_enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('name'), data.get('description'), data.get('details'),
        data.get('system_prompt'), json.dumps(data.get('tools', [])),
        data.get('creds_schema'), data.get('framework'),
        int(data.get('chat_enabled', False)), int(data.get('workflow_enabled', False))
    ))
    conn.commit()
    return cursor.lastrowid

def update_marketplace_agent(agent_id: int, data: Dict[str, Any]):
    """
    Update a marketplace agent.
    Example:
        update_marketplace_agent(1, {
            'name': 'AgentName2',
            'description': 'desc2',
            'details': 'details2',
            'system_prompt': 'prompt2',
            'tools': [1, 2],
            'creds_schema': '{}',
            'framework': 'fastapi',
            'chat_enabled': True,
            'workflow_enabled': False
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE marketplace_agents SET name=?, description=?, details=?, system_prompt=?, tools=?, creds_schema=?, framework=?, chat_enabled=?, workflow_enabled=? WHERE agent_id=?
    ''', (
        data.get('name'), data.get('description'), data.get('details'),
        data.get('system_prompt'), json.dumps(data.get('tools', [])),
        data.get('creds_schema'), data.get('framework'),
        int(data.get('chat_enabled', False)), int(data.get('workflow_enabled', False)), agent_id
    ))
    conn.commit()
    return cursor.rowcount

def soft_delete_marketplace_agent(agent_id: int):
    """
    Soft delete a marketplace agent.
    Example:
        soft_delete_marketplace_agent(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE marketplace_agents SET soft_delete=1 WHERE agent_id=?', (agent_id,))
    conn.commit()
    return cursor.rowcount


def delete_marketplace_agent(agent_id: int):
    """
    Permanently delete a marketplace agent.
    Example:
        delete_marketplace_agent(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM marketplace_agents WHERE agent_id=?', (agent_id,))
    conn.commit()
    return cursor.rowcount

# 5. Deployed Agents

def fetch_all_deployed_agents() -> List[Dict[str, Any]]:
    """
    Fetch all deployed agents, including tool data from marketplace_tools_deployed and custom_tools.
    Example:
        fetch_all_deployed_agents()
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents_deployed WHERE soft_delete = 0')
    columns = [column[0] for column in cursor.description]
    agents = [dict(zip(columns, row)) for row in cursor.fetchall()]
    for agent in agents:
        # tools field can be JSON or comma-separated
        tool_ids = []
        if agent.get('tools'):
            try:
                tool_ids = json.loads(agent['tools']) if isinstance(agent['tools'], str) else agent['tools']
            except Exception:
                tool_ids = []
        agent['tools_data'] = []
        if isinstance(tool_ids, list) and tool_ids:
            # Try marketplace_tools_deployed first
            placeholders = ','.join(['?']*len(tool_ids))
            tool_cursor = conn.cursor()
            tool_cursor.execute(f'SELECT * FROM marketplace_tools_deployed WHERE deployment_id IN ({placeholders}) AND user_id = ? AND soft_delete = 0', tool_ids + [agent['user_id']])
            tool_columns = [column[0] for column in tool_cursor.description]
            agent['tools_data'] += [dict(zip(tool_columns, row)) for row in tool_cursor.fetchall()]
            # Then try custom_tools for type match
            tool_cursor.execute(f'SELECT * FROM custom_tools WHERE user_id = ? AND tool_id IN ({placeholders}) AND soft_delete = 0', [agent['user_id']] + tool_ids)
            tool_columns = [column[0] for column in tool_cursor.description]
            agent['tools_data'] += [dict(zip(tool_columns, row)) for row in tool_cursor.fetchall()]
        # Ensure chat_enabled and workflow_enabled are returned as bool
        agent['chat_enabled'] = bool(agent.get('chat_enabled', 0))
        agent['workflow_enabled'] = bool(agent.get('workflow_enabled', 0))
    return agents


def insert_agent_deployed(data: Dict[str, Any]):
    """
    Insert a deployed agent.
    Example:
        insert_agent_deployed({
            'user_id': 1,
            'deployed_agent_url': 'http://...',
            'description': 'desc',
            'details': 'details',
            'system_prompt': 'prompt',
            'type': 'chat',
            'tools': [101, 202],
            'sha': 'sha1',
            'run_id': 'run1',
            'agent_url': 'http://...',
            'server_url': 'http://...',
            'client_url': 'http://...',
            'status': 'running',
            'framework': 'agno',
            'chat_enabled': True,
            'workflow_enabled': False,
            'error': None
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO agents_deployed (user_id, deployed_agent_url, description, details, system_prompt, type, tools, sha, run_id, agent_url, server_url, client_url, status, framework, chat_enabled, workflow_enabled, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['user_id'], data['deployed_agent_url'], data.get('description'), data.get('details'),
        data.get('system_prompt'), data.get('type'), json.dumps(data.get('tools', [])),
        data.get('sha'), data.get('run_id'), data.get('agent_url'), data.get('server_url'), data.get('client_url'),
        data.get('status'), data.get('framework'),
        int(data.get('chat_enabled', False)), int(data.get('workflow_enabled', False)),
        data.get('error')
    ))
    conn.commit()
    return cursor.rowcount

def update_agent_deployed(user_id: int, data: Dict[str, Any]):
    """
    Update a deployed agent.
    Example:
        update_agent_deployed(1, {
            'deployed_agent_url': 'http://...',
            'description': 'desc2',
            'details': 'details2',
            'system_prompt': 'prompt2',
            'type': 'workflow',
            'tools': [101, 202],
            'sha': 'sha2',
            'run_id': 'run2',
            'agent_url': 'http://...',
            'server_url': 'http://...',
            'client_url': 'http://...',
            'status': 'paused',
            'framework': 'agno',
            'chat_enabled': True,
            'workflow_enabled': False,
            'error': 'none'
        })
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE agents_deployed SET deployed_agent_url=?, description=?, details=?, system_prompt=?, type=?, tools=?, sha=?, run_id=?, agent_url=?, server_url=?, client_url=?, status=?, framework=?, chat_enabled=?, workflow_enabled=?, error=?, agent_card=?, skill_card=?
        WHERE user_id=?
    ''', (
        data.get('deployed_agent_url'), data.get('description'), data.get('details'),
        data.get('system_prompt'), data.get('type'), json.dumps(data.get('tools', [])),
        data.get('sha'), data.get('run_id'), data.get('agent_url'), data.get('server_url'), data.get('client_url'),
        data.get('status'), data.get('framework'),
        int(data.get('chat_enabled', False)), int(data.get('workflow_enabled', False)),
        data.get('error'), data.get('agent_card'), data.get('skill_card'), user_id
    ))
    conn.commit()
    return cursor.rowcount

def soft_delete_agent_deployed(user_id: int):
    """
    Soft delete a deployed agent.
    Example:
        soft_delete_agent_deployed(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE agents_deployed SET soft_delete=1 WHERE user_id=?', (user_id,))
    conn.commit()
    return cursor.rowcount

# -------------------
def delete_agent_deployed(user_id: int):
    """
    Permanently delete a deployed agent.
    Example:
        delete_agent_deployed(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM agents_deployed WHERE user_id=?', (user_id,))
    conn.commit()
    return cursor.rowcount

# CRUD for chat_history
# -------------------

def fetch_chat_history(conversation_id: int) -> List[Dict[str, Any]]:
    """
    Fetch chat history for a conversation, ordered by created_at.
    Example:
        fetch_chat_history(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM chat_history WHERE conversation_id = ? AND (soft_delete = 0 OR soft_delete IS NULL) ORDER BY created_at
        ''', (conversation_id,))
    except Exception:
        # If soft_delete column does not exist
        cursor.execute('''
            SELECT * FROM chat_history WHERE conversation_id = ? ORDER BY created_at
        ''', (conversation_id,))
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
def insert_chat_message(data: Dict[str, Any]):
    """
    Robustly insert a chat message into the chat_history table, handling both auto-increment and non-auto-increment message_id schemas.
    If message_id is required, automatically generates the next available id.
    """
    import logging
    conn = get_connection()
    cursor = conn.cursor()
    table_name = AppSettings().agentsbuilder_chathistorytable
    try:
        # Try insert without message_id (auto-increment case)
        cursor.execute(
            f"INSERT INTO {table_name} (conversation_id, user_id, agent_id, sender, message_text, created_at, attachments) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data['conversation_id'], data['user_id'], data['agent_id'], data['sender'],
                data.get('message_text'), data.get('created_at'), data.get('attachments')
            )
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        # Check if error is due to missing message_id
        if hasattr(e, 'args') and any('message_id' in str(arg) for arg in e.args):
            logging.warning("message_id required in insert; falling back to manual id generation.")
            # Get next message_id
            cursor.execute(f"SELECT ISNULL(MAX(message_id), 0) + 1 FROM {table_name}")
            next_id = cursor.fetchone()[0]
            cursor.execute(
                f"INSERT INTO {table_name} (message_id, conversation_id, user_id, agent_id, sender, message_text, created_at, attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    next_id, data['conversation_id'], data['user_id'], data['agent_id'], data['sender'],
                    data.get('message_text'), data.get('created_at'), data.get('attachments')
                )
            )
            conn.commit()
            return next_id
        else:
            logging.error(f"Failed to insert chat message: {e}")
            raise

def update_chat_message(message_id: int, new_text: str):
    """
    Update a chat message.
    Example:
        update_chat_message(1, 'Updated message text')
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE chat_history SET message_text=? WHERE message_id=?', (new_text, message_id))
    conn.commit()
    return cursor.rowcount

def soft_delete_chat_message(message_id: int):
    """
    Soft delete a chat message.
    Example:
        soft_delete_chat_message(1)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE chat_history SET soft_delete=1 WHERE message_id=?', (message_id,))
    conn.commit()
    return cursor.rowcount

