# Dynamic Agent Builder – In-Depth Architecture Documentation

## 1. High-Level Overview
- **Goal:** Enable users to visually assemble and deploy custom AI agents with MCP tools and Azure OpenAI, supporting multiple frameworks, via a user-friendly web interface and robust backend.
- **Core Components:**
  - Frontend (UI)
  - Backend (API)
  - Templates & Credential Schemas
  - Agent Deployment & Lifecycle Management

---

## 2. Component Breakdown

### 2.1 Frontend (UI)
- **Tool Palette:**
  - Fetches available tools from backend (`GET /tools`).
  - Displays tool name, description, metadata.
  - Drag-and-drop to agent builder area.
- **Agent Builder:**
  - Drag-and-drop interface for assembling agents with tools.
  - “Proceed” button to configure agent.
- **Agent Configuration Modal:**
  - System prompt input (defaulted, editable).
  - Framework selector (radio buttons).
  - Dynamic credential input fields (driven by backend `creds_schema.json`).
  - “Proceed” button to create agent.
- **Deployment & Chat:**
  - Deployment status indicator.
  - Chat interface unlocked on success.
  - Visual display of connected tools (tiles/icons).
  - “Get API” button for endpoint retrieval.
- **Other Features:**
  - Tool search/filter.
  - Tool details popover/modal.
  - Agent status indicators.
  - Error/success notifications.
  - Copy-to-clipboard for API endpoint.

### 2.2 Backend (API)
- **Endpoints:**
  - `GET /tools`: List available tools.
  - `GET /frameworks`: List supported frameworks and credential schemas.
  - `POST /agents`: Create and deploy agent (with tools, prompt, framework, credentials).
  - `GET /agents/{id}/status`: Get deployment status.
  - `GET /agents/{id}/endpoint`: Get agent endpoint.
  - `POST /agents/{id}/query`: Proxy chat to deployed agent.
  - `GET /agents/{id}/tools`: List tools bound to agent.
- **Credential Validation:**
  - Validates credentials against selected framework’s schema.
- **Template Rendering:**
  - Uses Jinja2 to generate agent code per user selection.
- **Deployment:**
  - Local (dev): Subprocess or Docker.
  - Production: Azure App Service/Container App.
- **Agent Registry:**
  - Stores agent config, status, endpoint, and metadata.

### 2.3 Templates & Schemas
- **Structure:**
  - `agents_templates/<framework>/{template, creds_schema}.json`
  - Jinja2 templates for each framework.
  - JSON schemas for credential validation and dynamic UI rendering.

### 2.4 Agent Deployment & Lifecycle
- **Create:** Generate, deploy, and register agent.
- **Query:** Proxy chat to agent endpoint.
- **Status:** Poll for deployment/running status.
- **Delete/Stop:** Remove agent and clean up resources.

---

## 3. Data Flow & Relationships

- **Tool Discovery:**
  - UI → Backend (`GET /tools`) → Returns tools → UI renders palette.
- **Agent Creation:**
  - UI collects tools, prompt, framework, credentials → Backend validates → Renders template → Deploys agent → Registers agent.
- **Chat:**
  - UI sends message → Backend proxies to agent endpoint → Returns response.
- **Agent Management:**
  - UI can poll status, get endpoint, or delete agent via API.

---

## 4. Security & Best Practices
- **Credentials:**
  - Collected only in UI, sent securely to backend, never exposed after entry.
  - Use env vars or secret management for deployments.
- **API Security:**
  - Auth required for agent creation, chat, and management.
  - CORS restricted to frontend domains.
- **Template Safety:**
  - Only fill in well-defined slots in Jinja2 templates.
- **Error Handling:**
  - All endpoints return clear error messages for invalid input, deployment failures, etc.

---

## 5. Extensibility
- **Add new frameworks:** Drop in new template and schema.
- **Add new tools:** Register new MCP servers in backend/tool registry.
- **UI/Backend decoupled:** API-driven, so either can evolve independently.

---

## 6. DevOps & Documentation
- **CI/CD:** Automated tests for backend, template rendering, and agent deployment.
- **Documentation:**
  - API contracts, template usage, deployment instructions.
  - User and developer guides.
- **Monitoring:**
  - Logs, error tracking, and usage analytics for agents and platform.

---

## 7. Architecture Diagram

```
[UI] <--REST--> [Backend API] <---> [Templates/Schema]
                                      |
                                  [Deployment Manager]
                                      |
                                [Running Agent Endpoints]
```

---

## 8. Relationships & Avoiding Duplicacy
- **Templates & Schemas:** One per framework, referenced by both backend (for codegen/validation) and UI (for dynamic fields).
- **Tool Registry:** Centralized, used by both UI and backend.
- **Agent Registry:** Single source of truth for all deployed agents.
- **Credential Handling:** Unified schema per framework, used by both UI and backend for validation and rendering.
- **API endpoints:** Each endpoint serves a unique purpose; no overlapping responsibilities.

---

## 9. Open Questions & Next Steps
- How to handle agent versioning/updates?
- Should agent logs be accessible from UI?
- How to manage agent resource limits (CPU, memory, etc.)?

---

# End of Architecture Doc
