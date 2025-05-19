# Database Schema Documentation

## 1. Users Table

```sql
CREATE TABLE users (
    user_id NVARCHAR(64) PRIMARY KEY,
    username NVARCHAR(255) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL
);
```

### Example Insert
```sql
INSERT INTO users (user_id, username, password_hash)
VALUES ('user-001', 'alice', 'hashed_pw1');
```

## 2. Marketplace Tools Table

```sql
CREATE TABLE marketplace_tools (
    tool_id NVARCHAR(64) PRIMARY KEY,
    admin_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    file_path NVARCHAR(1024) NOT NULL,
    sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0
);
```

### Example Insert
```sql
INSERT INTO marketplace_tools (
    tool_id, admin_id, name, description, file_path, sha, run_id, status, endpoint, error, soft_delete
) VALUES (
    'market-tavily-001', 'admin-001', 'Tavily', 'Web search tool for real-time answers.',
    'tools/marketplace/tavily/tavily.py', 'sha1', 'run1', 'active',
    'http://tavily.eastus.azurecontainer.io:8000/sse', NULL, 0
);
```

### Soft Delete Example
```sql
UPDATE marketplace_tools
SET soft_delete = 1
WHERE tool_id = 'market-tavily-001';
```

## 3. Custom Tools Table

```sql
CREATE TABLE custom_tools (
    user_id NVARCHAR(64) NOT NULL,
    tool_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    file_path NVARCHAR(1024) NOT NULL,
    sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, tool_id)
);
```

### Example Insert
```sql
INSERT INTO custom_tools (
    user_id, tool_id, name, description, file_path, sha, run_id, status, endpoint, error, soft_delete
) VALUES (
    'user-001', 'custom-tool-001', 'Custom Extractor', 'Extracts data from PDFs.',
    'tools/custom/user-001/extractor.py', 'sha3', 'run3', 'active',
    'http://custom1.eastus.azurecontainer.io:8000/sse', NULL, 0
);
```

### Soft Delete Example
```sql
UPDATE custom_tools
SET soft_delete = 1
WHERE user_id = 'user-001' AND tool_id = 'custom-tool-001';
```

## 4. User Tools Table

```sql
CREATE TABLE user_tools (
    user_id NVARCHAR(64) NOT NULL,
    tool_id NVARCHAR(64) NOT NULL,
    type NVARCHAR(20) NOT NULL,
    status NVARCHAR(20),
    PRIMARY KEY (user_id, tool_id)
);
```

### Example Insert
```sql
INSERT INTO user_tools (user_id, tool_id, type, status)
VALUES ('user-001', 'market-tavily-001', 'marketplace', 'active');
```

## 5. User Agents Table

```sql
CREATE TABLE user_agents (
    user_id NVARCHAR(64) NOT NULL,
    agent_id NVARCHAR(64) NOT NULL,
    status NVARCHAR(20),
    PRIMARY KEY (user_id, agent_id)
);
```

### Example Insert
```sql
INSERT INTO user_agents (user_id, agent_id, status)
VALUES ('user-001', 'market-agent-001', 'active');
```

## 6. Marketplace Agents Table

```sql
CREATE TABLE marketplace_agents (
    agent_id NVARCHAR(64) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    file_path NVARCHAR(1024) NOT NULL,
    commit_sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    tools NVARCHAR(MAX) NOT NULL,
    framework NVARCHAR(100) NOT NULL,
    prompt NVARCHAR(MAX) NOT NULL,
    error NVARCHAR(MAX) NULL
);
```

### Example Insert
```sql
INSERT INTO marketplace_agents (
    agent_id, name, description, status, endpoint, file_path, commit_sha, run_id, tools, framework, prompt, error
) VALUES (
    'market-agent-001', 'Agent One', 'Marketplace agent for demo.', 'active',
    'http://agent1.eastus.azurecontainer.io:8000', 'agents/market/agent1.py', 'sha5', 'run5',
    '[{"tool_id":"market-tavily-001"}]', 'pydantic_ai', 'Demo prompt', NULL
);
```

## 7. Custom Agents Table

```sql
CREATE TABLE custom_agents (
    agent_id NVARCHAR(64) PRIMARY KEY,
    user_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    file_path NVARCHAR(1024) NOT NULL,
    commit_sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    tools NVARCHAR(MAX) NOT NULL,
    framework NVARCHAR(100) NOT NULL,
    prompt NVARCHAR(MAX) NOT NULL,
    error NVARCHAR(MAX) NULL
);
```

### Example Insert
```sql
INSERT INTO custom_agents (
    agent_id, user_id, name, description, status, endpoint, file_path, commit_sha, run_id, tools, framework, prompt, error
) VALUES (
    'custom-agent-001', 'user-001', 'Custom Agent', 'User-specific agent.', 'active',
    'http://customagent.eastus.azurecontainer.io:8000', 'agents/custom/agent1.py', 'sha6', 'run6',
    '[{"tool_id":"custom-tool-001"}]', 'pydantic_ai', 'Custom prompt', NULL
);
```

## Example Deletion Queries

```sql
-- Delete a user
DELETE FROM users WHERE user_id = 'user-001';

-- Delete a custom tool
DELETE FROM custom_tools WHERE user_id = 'user-001' AND tool_id = 'custom-tool-001';
```

## Notes
- All `status` columns are now free-form (no constraints)
- All soft deletes are handled with a `soft_delete` BIT column (0 = active, 1 = deleted)
- Composite primary key is used in `custom_tools` (`user_id`, `tool_id`)
- You may add foreign key constraints as needed, depending on your application logic


--------------------------------------------------------------------------------------

Here is a comprehensive documentation of all the tables you have created, including their schemas and example queries for insertion, update, and deletion. This documentation is suitable for sharing with your manager or team.

Database Tables Documentation
1. users
Schema:

sql
CopyInsert
CREATE TABLE users (
    user_id NVARCHAR(64) PRIMARY KEY,
    username NVARCHAR(255) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL
);
Example Insert:

sql
CopyInsert
INSERT INTO users (user_id, username, password_hash)
VALUES ('user-001', 'alice', 'hashed_pw1');
2. marketplace_tools
Schema:

sql
CopyInsert
CREATE TABLE marketplace_tools (
    tool_id NVARCHAR(64) PRIMARY KEY,
    admin_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    file_path NVARCHAR(1024) NOT NULL,
    sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0
);
Example Insert:

sql
CopyInsert
INSERT INTO marketplace_tools (
    tool_id, admin_id, name, description, file_path, sha, run_id, status, endpoint, error, soft_delete
) VALUES (
    'market-tavily-001', 'admin-001', 'Tavily', 'Web search tool for real-time answers.',
    'tools/marketplace/tavily/tavily.py', 'sha1', 'run1', 'active',
    'http://tavily.eastus.azurecontainer.io:8000/sse', NULL, 0
);
Soft Delete Example:

sql
CopyInsert
UPDATE marketplace_tools
SET soft_delete = 1
WHERE tool_id = 'market-tavily-001';
3. custom_tools
Schema:

sql
CopyInsert
CREATE TABLE custom_tools (
    user_id NVARCHAR(64) NOT NULL,
    tool_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    file_path NVARCHAR(1024) NOT NULL,
    sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, tool_id)
);
Example Insert:

sql
CopyInsert
INSERT INTO custom_tools (
    user_id, tool_id, name, description, file_path, sha, run_id, status, endpoint, error, soft_delete
) VALUES (
    'user-001', 'custom-tool-001', 'Custom Extractor', 'Extracts data from PDFs.',
    'tools/custom/user-001/extractor.py', 'sha3', 'run3', 'active',
    'http://custom1.eastus.azurecontainer.io:8000/sse', NULL, 0
);
Soft Delete Example:

sql
CopyInsert
UPDATE custom_tools
SET soft_delete = 1
WHERE user_id = 'user-001' AND tool_id = 'custom-tool-001';
4. user_tools
Schema:

sql
CopyInsert
CREATE TABLE user_tools (
    user_id NVARCHAR(64) NOT NULL,
    tool_id NVARCHAR(64) NOT NULL,
    type NVARCHAR(20) NOT NULL,
    status NVARCHAR(20),
    PRIMARY KEY (user_id, tool_id)
);
Example Insert:

sql
CopyInsert
INSERT INTO user_tools (user_id, tool_id, type, status)
VALUES ('user-001', 'market-tavily-001', 'marketplace', 'active');
5. user_agents
Schema:

sql
CopyInsert
CREATE TABLE user_agents (
    user_id NVARCHAR(64) NOT NULL,
    agent_id NVARCHAR(64) NOT NULL,
    status NVARCHAR(20),
    PRIMARY KEY (user_id, agent_id)
);
Example Insert:

sql
CopyInsert
INSERT INTO user_agents (user_id, agent_id, status)
VALUES ('user-001', 'market-agent-001', 'active');
6. marketplace_agents
Schema:

sql
CopyInsert
CREATE TABLE marketplace_agents (
    agent_id NVARCHAR(64) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    file_path NVARCHAR(1024) NOT NULL,
    commit_sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    tools NVARCHAR(MAX) NOT NULL,
    framework NVARCHAR(100) NOT NULL,
    prompt NVARCHAR(MAX) NOT NULL,
    error NVARCHAR(MAX) NULL
);
Example Insert:

sql
CopyInsert
INSERT INTO marketplace_agents (
    agent_id, name, description, status, endpoint, file_path, commit_sha, run_id, tools, framework, prompt, error
) VALUES (
    'market-agent-001', 'Agent One', 'Marketplace agent for demo.', 'active',
    'http://agent1.eastus.azurecontainer.io:8000', 'agents/market/agent1.py', 'sha5', 'run5',
    '[{"tool_id":"market-tavily-001"}]', 'pydantic_ai', 'Demo prompt', NULL
);
7. custom_agents
Schema:

sql
CopyInsert
CREATE TABLE custom_agents (
    agent_id NVARCHAR(64) PRIMARY KEY,
    user_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(20),
    endpoint NVARCHAR(2048) NOT NULL,
    file_path NVARCHAR(1024) NOT NULL,
    commit_sha NVARCHAR(64) NOT NULL,
    run_id NVARCHAR(255) NOT NULL,
    tools NVARCHAR(MAX) NOT NULL,
    framework NVARCHAR(100) NOT NULL,
    prompt NVARCHAR(MAX) NOT NULL,
    error NVARCHAR(MAX) NULL
);
Example Insert:

sql
CopyInsert
INSERT INTO custom_agents (
    agent_id, user_id, name, description, status, endpoint, file_path, commit_sha, run_id, tools, framework, prompt, error
) VALUES (
    'custom-agent-001', 'user-001', 'Custom Agent', 'User-specific agent.', 'active',
    'http://customagent.eastus.azurecontainer.io:8000', 'agents/custom/agent1.py', 'sha6', 'run6',
    '[{"tool_id":"custom-tool-001"}]', 'pydantic_ai', 'Custom prompt', NULL
);
Example Deletion Query
Delete a user from users table:

sql
CopyInsert
DELETE FROM users WHERE user_id = 'user-001';
Delete a custom tool:

sql
CopyInsert
DELETE FROM custom_tools WHERE user_id = 'user-001' AND tool_id = 'custom-tool-001';
Notes
All status columns are now free-form (no constraints).
All soft deletes are handled with a soft_delete BIT column (0 = active, 1 = deleted).
Composite primary key is used in custom_tools (user_id, tool_id).
You may add foreign key constraints as needed, depending on your application logic.
Let me know if you want this as a Markdown file or need further details (like foreign key relationships or more query examples)!