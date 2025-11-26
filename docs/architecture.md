# Architecture Overview

## OpenSOAR Playbooks Architecture

OpenSOAR Playbooks is a modular SOAR (Security Orchestration, Automation and Response) platform designed for automating incident response workflows.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        External World                            │
│  (SIEM, EDR, Firewalls, Ticketing, Chat, Email, etc.)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │         FastAPI REST API              │
         │  (Playbooks, Incidents, Runs, Auth)   │
         └───────────┬───────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │ Playbook │          │ Incident │
    │  CRUD    │          │  CRUD    │
    └──────────┘          └──────────┘
          │                     │
          └──────────┬──────────┘
                     ▼
         ┌───────────────────────┐
         │  Playbook Engine      │
         │  (Orchestration)      │
         └───────────┬───────────┘
                     │
          ┌──────────┴──────────────────┐
          ▼                             ▼
    ┌──────────┐               ┌────────────────┐
    │   DSL    │               │   Execution    │
    │  Parser  │               │    Context     │
    └──────────┘               └────────────────┘
          │                             │
          ▼                             ▼
    ┌──────────────────────────────────────┐
    │      Connector Framework             │
    │  (Firewall, Ticketing, Identity...)  │
    └──────────────────────────────────────┘
          │
          ▼
    ┌──────────────┐
    │  PostgreSQL  │
    │  (Storage)   │
    └──────────────┘
```

---

## Core Components

### 1. FastAPI REST API

**Purpose**: Provides HTTP endpoints for playbook management, incident handling, and execution control.

**Endpoints**:
- `/playbooks` - CRUD operations for playbooks
- `/incidents` - CRUD operations for incidents
- `/playbooks/{id}/run` - Start playbook execution
- `/runs` - Query execution status
- `/runs/{id}/resume` - Resume paused runs

**Authentication**: Simple API key authentication (stub for v0.1)

### 2. Playbook Engine

**Purpose**: Orchestrates playbook execution, manages state, and coordinates connector invocations.

**Responsibilities**:
- Parse and validate playbook YAML
- Execute steps in correct order
- Handle branching (conditions)
- Pause on manual approval steps
- Resume execution after approval
- Maintain execution context
- Log all actions

**Flow**:
```
API Request → Engine.run_playbook()
   ↓
Parse YAML → Validate → Create Run
   ↓
Execute Loop:
   Get Step → Route by Type → Execute → Update Context → Next Step
   ↓
Complete or Pause (manual step)
```

### 3. DSL Parser

**Purpose**: Parse and validate YAML playbook definitions.

**Features**:
- YAML parsing
- Semantic validation
- Circular reference detection
- Jinja2 template validation
- Type checking

**Validation Rules**:
- Required fields: name, version, steps
- Step types: action, condition, manual, wait
- Reference integrity (next steps exist)
- No cycles in step graph

### 4. Execution Context

**Purpose**: Maintain runtime state during playbook execution.

**Data Stored**:
- Incident/event data
- Playbook variables
- Step outputs (for referencing in templates)
- Manual step input

**Template Rendering**:
- `{{ incident.* }}` - Incident fields
- `{{ event.* }}` - Event fields
- `{{ vars.* }}` - Playbook variables
- `{{ steps.step_id.output.* }}` - Previous step outputs
- `{{ manual.* }}` - Manual input data

### 5. Connector Framework

**Purpose**: Abstraction layer for integrating with external systems.

**Architecture**:
```python
BaseConnector (ABC)
   ↓
   execute(operation, params, context) → result
```

**Registry**: Singleton pattern for connector discovery and invocation.

**v0.1 Connectors** (all mocked):
- `dummy_firewall` - Block/unblock IPs
- `dummy_ticketing` - Create/update tickets
- `dummy_identity` - Manage user accounts
- `dummy_slack` - Send messages
- `dummy_reputation` - IP/URL reputation lookup
- `http` - HTTP requests

### 6. Data Layer

**Database**: PostgreSQL with SQLModel ORM

**Core Tables**:
- `events` - Raw security events
- `incidents` - Aggregated events requiring response
- `playbooks` - Workflow definitions
- `playbook_runs` - Execution instances

**Relationships**:
- Events → Incident (many-to-one)
- PlaybookRun → Playbook (many-to-one)
- PlaybookRun → Incident (many-to-one, optional)

---

## Request Flow Example

### Scenario: Execute IP blocking playbook

```
1. Client: POST /playbooks/1/run {"incident_id": 42}
             ↓
2. API: Create PlaybookRun (status: pending)
             ↓
3. Engine: Load Playbook YAML + Incident data
             ↓
4. Engine: Initialize ExecutionContext
             ↓
5. Engine: Execute step 1 (check_reputation)
             ↓
6. Connector: DummyReputationConnector.lookup_ip()
             ↓
7. Engine: Store output in context
             ↓
8. Engine: Execute step 2 (condition: score < 30?)
             ↓
9. Engine: Branch to block_ip step (true branch)
             ↓
10. Connector: DummyFirewallConnector.block_ip()
             ↓
11. Engine: Execute step 3 (create_ticket)
             ↓
12. Connector: DummyTicketingConnector.create_ticket()
             ↓
13. Engine: Mark run as completed
             ↓
14. API: Return PlaybookRun response
```

---

## Scaling and Production Considerations

### v0.1 (Current)
- In-process execution
- Single server deployment
- SQLite/PostgreSQL storage

### Future Enhancements
- **Message Queue**: Celery + Redis for async playbook execution
- **Multi-tenancy**: Tenant isolation in database and API
- **Real Connectors**: Actual integrations with external systems
- **Horizontal Scaling**: Multiple worker processes
- **UI/Visual Editor**: Drag-and-drop playbook designer
- **Analytics**: Execution metrics, performance monitoring
- **Advanced Features**: Parallel execution, loops, subplaybooks

---

## Security Model

### v0.1
- API key authentication (header-based)
- No secrets in playbooks (use environment variables)
- Audit logging of all actions

### Production Requirements
- OAuth2/JWT authentication
- Role-based access control (RBAC)
- Tenant isolation
- Secrets management (Vault, AWS Secrets Manager)
- Encrypted storage for sensitive data
- TLS/HTTPS for all communications

---

## Design Principles

1. **Modularity**: Clean separation between DSL, engine, connectors, and API
2. **Extensibility**: Easy to add new connectors and step types
3. **Testability**: Comprehensive unit tests for all components
4. **Production-Ready**: Structured logging, error handling, database migrations
5. **Developer-Friendly**: Clear APIs, good documentation, realistic examples
