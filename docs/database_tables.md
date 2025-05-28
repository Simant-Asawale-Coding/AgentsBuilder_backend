# Database Schema Documentation

## Entity Relationship Diagram (ERD)

```mermaid
    CHAT_HISTORY {
        INT message_id PK
        INT conversation_id
        INT user_id FK
        INT agent_id FK
        NVARCHAR sender
        NVARCHAR message_text
        DATETIME created_at
        NVARCHAR attachments
        BIT soft_delete
    }
erDiagram
    USERS ||--o{ MARKETPLACE_TOOLS_DEPLOYED : "has"
    USERS ||--o{ CUSTOM_TOOLS : "has"
    USERS ||--o{ AGENTS_DEPLOYED : "has"
    MARKETPLACE_TOOLS ||--o{ MARKETPLACE_TOOLS_DEPLOYED : "is deployed in"
    MARKETPLACE_AGENTS ||--o{ AGENTS_DEPLOYED : "is deployed as"
    MARKETPLACE_TOOLS {
        NVARCHAR tool_id PK
        INT admin_id
        NVARCHAR name
        NVARCHAR description
        NVARCHAR creds_schema
        NVARCHAR sha
        NVARCHAR tool_details
        BIT soft_delete
    }
    MARKETPLACE_TOOLS_DEPLOYED {
        INT user_id FK
        NVARCHAR deployment_id
        NVARCHAR description
        NVARCHAR details
        NVARCHAR tool_id FK
        NVARCHAR sha
        NVARCHAR run_id
        NVARCHAR url
        NVARCHAR status
        NVARCHAR error
        BIT soft_delete
    }
    CUSTOM_TOOLS {
        INT user_id FK
        NVARCHAR tool_id PK
        NVARCHAR name
        NVARCHAR description
        NVARCHAR details
        NVARCHAR sha
        NVARCHAR status
        NVARCHAR url
        NVARCHAR type
        NVARCHAR error
        BIT soft_delete
    }
    MARKETPLACE_AGENTS {
        NVARCHAR agent_id PK
        NVARCHAR name
        NVARCHAR description
        NVARCHAR details
        NVARCHAR system_prompt
        NVARCHAR tools
        NVARCHAR creds_schema
        NVARCHAR framework
        BIT soft_delete
    }
    AGENTS_DEPLOYED {
        INT user_id FK
        NVARCHAR deployed_agent_url
        NVARCHAR description
        NVARCHAR details
        NVARCHAR system_prompt
        NVARCHAR type
        NVARCHAR tools
        NVARCHAR sha
        NVARCHAR run_id
        NVARCHAR agent_url
        NVARCHAR server_url
        NVARCHAR client_url
        NVARCHAR status
        NVARCHAR framework
        NVARCHAR error
        BIT soft_delete
    }
    USERS {
        INT user_id PK
        NVARCHAR username
        NVARCHAR password_hash
    }
    CHAT_HISTORY {
        NVARCHAR message_id PK
        NVARCHAR conversation_id
        INT user_id FK
        NVARCHAR agent_id FK
        NVARCHAR sender
        NVARCHAR message_text
        DATETIME created_at
        NVARCHAR attachments
        BIT soft_delete
    }
```

---

## 1. USERS Table

```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username NVARCHAR(255) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL
);
```

---

## 2. MARKETPLACE_TOOLS Table

```sql
CREATE TABLE marketplace_tools (
    tool_id NVARCHAR(64) PRIMARY KEY,
    admin_id INT NOT NULL,
    name NVARCHAR(255) NULL,
    description NVARCHAR(MAX) NULL,
    creds_schema NVARCHAR(MAX) NULL,
    sha NVARCHAR(255) NULL,
    tool_details NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0
);
```

---

## 3. MARKETPLACE_TOOLS_DEPLOYED Table

```sql
CREATE TABLE marketplace_tools_deployed (
    user_id INT NOT NULL,
    deployment_id NVARCHAR(64) NOT NULL,
    description NVARCHAR(MAX) NULL,
    details NVARCHAR(MAX) NULL,
    tool_id NVARCHAR(64) NULL,
    sha NVARCHAR(255) NULL,
    run_id NVARCHAR(255) NULL,
    url NVARCHAR(255) NULL,
    status NVARCHAR(50) NULL, -- allowed: added/running/in progress/paused/down
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, deployment_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (tool_id) REFERENCES marketplace_tools(tool_id)
);
```

---

## 4. CUSTOM_TOOLS Table

```sql
CREATE TABLE custom_tools (
    user_id INT NOT NULL,
    tool_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NULL,
    description NVARCHAR(MAX) NULL,
    details NVARCHAR(MAX) NULL,
    sha NVARCHAR(255) NULL,
    status NVARCHAR(50) NULL,
    url NVARCHAR(255) NULL,
    type NVARCHAR(50) NULL,
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, tool_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## 5. MARKETPLACE_AGENTS Table

```sql
CREATE TABLE marketplace_agents (
    agent_id NVARCHAR(64) PRIMARY KEY,
    name NVARCHAR(255) NULL,
    description NVARCHAR(MAX) NULL,
    details NVARCHAR(MAX) NULL,
    system_prompt NVARCHAR(MAX) NULL,
    tools NVARCHAR(MAX) NULL, -- store as JSON or comma-separated list
    creds_schema NVARCHAR(MAX) NULL,
    framework NVARCHAR(50) NULL,
    soft_delete BIT NOT NULL DEFAULT 0
);
```

---

## 6. AGENTS_DEPLOYED Table

```sql
CREATE TABLE agents_deployed (
    user_id INT NOT NULL,
    deployed_agent_url NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    details NVARCHAR(MAX) NULL,
    system_prompt NVARCHAR(MAX) NULL,
    type NVARCHAR(50) NULL,
    tools NVARCHAR(MAX) NULL,
    sha NVARCHAR(255) NULL,
    run_id NVARCHAR(255) NULL,
    agent_url NVARCHAR(255) NULL,
    server_url NVARCHAR(255) NULL,
    client_url NVARCHAR(255) NULL,
    status NVARCHAR(50) NULL,
    framework NVARCHAR(50) NULL,
    error NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## 7. CHAT_HISTORY Table

```sql
CREATE TABLE chat_history (
    message_id NVARCHAR(64) PRIMARY KEY,
    conversation_id NVARCHAR(64) NOT NULL,
    user_id INT NOT NULL,
    agent_id NVARCHAR(64) NOT NULL,
    sender NVARCHAR(10) NOT NULL CHECK (sender IN ('user', 'agent')),
    message_text NVARCHAR(MAX) NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    attachments NVARCHAR(MAX) NULL,
    soft_delete BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (agent_id) REFERENCES marketplace_agents(agent_id)
);
```

### Example CRUD Operations with pyodbc

#### 1. Fetch Chat History
```python
import pyodbc

def fetch_chat_history(conversation_id):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message_id, sender, message_text, created_at, attachments
        FROM chat_history
        WHERE conversation_id = ? AND soft_delete = 0
        ORDER BY created_at ASC
    """, (conversation_id,))
    return cursor.fetchall()
```

#### 2. Add a New Message
```python
import pyodbc
from datetime import datetime

def add_message(conversation_id, user_id, agent_id, sender, message_text, attachments=None):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (conversation_id, user_id, agent_id, sender, message_text, created_at, attachments)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (conversation_id, user_id, agent_id, sender, message_text, datetime.now(), attachments))
    conn.commit()
```

#### 3. Soft Delete a Message
```python
import pyodbc

def soft_delete_message(message_id):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE chat_history SET soft_delete = 1 WHERE message_id = ?
    """, (message_id,))
    conn.commit()
```

#### 4. Update a Message
```python
import pyodbc

def update_message(message_id, new_text):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE chat_history SET message_text = ? WHERE message_id = ?
    """, (new_text, message_id))
    conn.commit()
```

---

## Notes

- **framework**: Indicates the software framework used by the agent (e.g., 'fastapi', 'flask', etc.).
- **agent_url/server_url/client_url**: URLs for different endpoints related to the deployed agent. 'agent_url' is the main endpoint, 'server_url' is the backend/server endpoint, and 'client_url' is the frontend/client endpoint.

- All `soft_delete` columns are BIT with a default of 0.
- All columns are nullable except the specified primary/secondary keys.
- Adjust data types as needed for your data.
- For `tools` fields, consider normalization if you want strict relational integrity.
- Foreign keys are clearly marked for reference integrity.

---

## Example Insert

```sql
INSERT INTO users (user_id, username, password_hash)
VALUES (1, 'alice', 'hashed_pw1');

INSERT INTO Marketplace_tools (admin_id, name, description, creds_schema, sha, tool_details)
VALUES (1, 'Tavily', 'Web search tool', NULL, 'sha1', NULL);

INSERT INTO Marketplace_tools_deployed (user_id, deployment_id, tool_id)
VALUES (1, 1001, 1);

INSERT INTO custom_tools (user_id, name)
VALUES (1, 'Custom Extractor');

INSERT INTO marketplace_agents (name, description)
VALUES ('Agent One', 'Marketplace agent for demo.');

INSERT INTO agents_deployed (user_id, deployed_agent_url)
VALUES (1, 'http://agent1.eastus.azurecontainer.io:8000');
```

---

## Example Soft Delete

```sql
UPDATE Marketplace_tools SET soft_delete = 1 WHERE tool_id = 1;
```
