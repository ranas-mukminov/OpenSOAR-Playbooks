# Playbook DSL Reference

Complete reference for the OpenSOAR Playbooks YAML-based Domain-Specific Language (DSL).

---

## Playbook Structure

```yaml
name: string              # Required: Unique playbook identifier
version: string           # Required: Semantic version (e.g., "1.0.0")
description: string       # Optional: Human-readable description
tags: [string]            # Optional: Categorization tags
author: string            # Optional: Author or team name

triggers:                 # Optional: Auto-execution conditions
  - type: string          # incident_created, incident_updated, event_received
    conditions:
      severity: [string]  # Severity filter
      tags: [string]      # Tag filter

vars:                     # Optional: Default variables
  key: value              # Variable definitions

steps:                    # Required: Workflow steps (dictionary)
  step_id:                # Unique step identifier
    type: string          # Required: action | condition | manual | wait
    # ... type-specific fields
```

---

## Step Types

### 1. Action Step

Executes a connector operation (e.g., block IP, create ticket).

```yaml
step_id:
  type: action
  connector: string       # Required: Connector name
  operation: string       # Required: Operation name
  input:                  # Optional: Operation parameters
    param1: value
    param2: "{{ template }}"
  next: string | null     # Next step ID (null = end)
```

**Example**:
```yaml
block_malicious_ip:
  type: action
  connector: dummy_firewall
  operation: block_ip
  input:
    ip: "{{ incident.payload.src_ip }}"
    duration: 3600
    reason: "Malicious activity on incident {{ incident.id }}"
  next: create_incident_ticket
```

---

### 2. Condition Step

Branching based on expression evaluation.

```yaml
step_id:
  type: condition
  expression: string      # Required: Jinja2 boolean expression
  on_true: string | null  # Step ID if true
  on_false: string | null # Step ID if false
```

**Example**:
```yaml
check_severity:
  type: condition
  expression: "{{ incident.severity == 'critical' }}"
  on_true: escalate_immediately
  on_false: normal_workflow
```

**Expression Examples**:
- `"{{ incident.severity == 'high' }}"`
- `"{{ steps.reputation_check.output.score < 30 }}"`
- `"{{ vars.threshold > 100 }}"`
- `"{{ 'phishing' in incident.tags }}"`

---

### 3. Manual Step

Pauses execution for human approval/input.

```yaml
step_id:
  type: manual
  prompt: string          # Required: Approval prompt
  input_fields:           # Optional: User input fields
    - name: string
      type: text | number | select
      required: boolean
  on_approved: string | null  # Step ID if approved
  on_rejected: string | null  # Step ID if rejected
```

**Example**:
```yaml
request_account_suspension:
  type: manual
  prompt: "Suspend user account {{ incident.payload.username }}?"
  input_fields:
    - name: justification
      type: text
      required: true
    - name: duration_days
      type: number
      required: false
  on_approved: suspend_user_account
  on_rejected: log_rejection
```

**Resuming**: Use `POST /runs/{id}/resume` with:
```json
{
  "decision": "approved",
  "manual_input": {
    "justification": "Account showed suspicious activity",
    "duration_days": 7
  }
}
```

---

### 4. Wait Step

Delays execution (simulated in v0.1).

```yaml
step_id:
  type: wait
  duration: number        # Required: Seconds to wait
  next: string | null     # Next step ID
```

**Example**:
```yaml
wait_for_propagation:
  type: wait
  duration: 300           # 5 minutes
  next: verify_block
```

---

## Template Expressions (Jinja2)

Access runtime data in step parameters using Jinja2 syntax.

### Available Context

**Incident Data** (`{{ incident.* }}`):
- `incident.id` - Incident ID
- `incident.title` - Title
- `incident.status` - Status (new, triaged, in_progress, contained, closed)
- `incident.severity` - Severity (low, medium, high, critical)
- `incident.owner` - Owner username
- `incident.payload` - Custom JSON data
- `incident.tags` - List of tags
- `incident.created_at` - Creation timestamp

**Event Data** (`{{ event.* }}`):
- `event.id` - Event ID
- `event.source` - Source system
- `event.payload` - Custom JSON data
- `event.severity` - Severity
- `event.tags` - List of tags
- `event.timestamp` - Event timestamp

**Variables** (`{{ vars.* }}`):
- Access playbook-level variables defined in `vars:` section

**Step Outputs** (`{{ steps.step_id.output.* }}`):
- Access outputs from previous steps
- Example: `{{ steps.reputation_check.output.score }}`

**Manual Input** (`{{ manual.* }}`):
- Access user input from manual approval steps
- Example: `{{ manual.justification }}`

### Template Examples

```yaml
# String interpolation
message: "Alert from {{ incident.title }}"

# Accessing nested JSON
ip_address: "{{ incident.payload.network.src_ip }}"

# Conditional expression
alert_level: "{{ 'HIGH' if incident.severity == 'critical' else 'NORMAL' }}"

# List operations
has_malware_tag: "{{ 'malware' in incident.tags }}"

# Step output chaining
reputation: "{{ steps.lookup_ip.output.category }}"
```

---

## Triggers (Auto-Execution)

Define conditions for automatic playbook execution.

```yaml
triggers:
  - type: incident_created | incident_updated | event_received
    conditions:
      severity:
        - critical
        - high
      tags:
        - malware
        - phishing
```

**Note**: Trigger evaluation is not implemented in v0.1. Playbooks are executed manually via API.

---

## Complete Example

```yaml
name: comprehensive_example
version: 1.0.0
description: Demonstrates all DSL features
tags:
  - example
  - comprehensive
author: Security Team

triggers:
  - type: incident_created
    conditions:
      severity: [critical, high]
      tags: [network_attack]

vars:
  default_timeout: 3600
  notification_channel: "#soc-alerts"

steps:
  # Action step
  gather_threat_intel:
    type: action
    connector: dummy_reputation
    operation: lookup_ip
    input:
      ip: "{{ incident.payload.attacker_ip }}"
    next: evaluate_threat

  # Condition step
  evaluate_threat:
    type: condition
    expression: "{{ steps.gather_threat_intel.output.score < 30 }}"
    on_true: notify_team
    on_false: log_and_close

  # Notification step
  notify_team:
    type: action
    connector: dummy_slack
    operation: send_message
    input:
      channel: "{{ vars.notification_channel }}"
      message: "⚠️ High-threat IP detected: {{ incident.payload.attacker_ip }}"
    next: request_blocking_approval

  # Manual approval step
  request_blocking_approval:
    type: manual
    prompt: "Block IP {{ incident.payload.attacker_ip }}?"
    input_fields:
      - name: block_duration
        type: number
        required: true
    on_approved: execute_block
    on_rejected: create_investigation_ticket

  # Conditional execution after approval
  execute_block:
    type: action
    connector: dummy_firewall
    operation: block_ip
    input:
      ip: "{{ incident.payload.attacker_ip }}"
      duration: "{{ manual.block_duration }}"
      reason: "Approved blocking for incident {{ incident.id }}"
    next: create_block_ticket

  create_block_ticket:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "IP Blocked: {{ incident.payload.attacker_ip }}"
      severity: "high"
      description: "Automated block executed"
    next: null

  create_investigation_ticket:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Manual Investigation: {{ incident.payload.attacker_ip }}"
      severity: "medium"
    next: null

  log_and_close:
    type: action
    connector: http
    operation: request
    input:
      method: POST
      url: "http://logging-service/api/events"
      body:
        event: "low_threat_ip"
        ip: "{{ incident.payload.attacker_ip }}"
    next: null
```

---

## Best Practices

1. **Naming**: Use descriptive step IDs (e.g., `block_malicious_ip` not `step1`)
2. **Variables**: Define constants in `vars` instead of hardcoding
3. **Error Handling**: Always provide both `on_true` and `on_false` branches
4. **Terminal Steps**: Set `next: null` for final steps
5. **Templates**: Test complex expressions before deploying
6. **Documentation**: Add clear `description` and inline comments (YAML comments)

---

## Validation

Playbooks are validated on upload. Common errors:

- **Missing required fields**: `name`, `version`, `steps`
- **Invalid step type**: Must be `action`, `condition`, `manual`, or `wait`
- **Broken references**: `next` points to non-existent step
- **Circular references**: Step graph contains cycles
- **Invalid templates**: Jinja2 syntax errors

Use `POST /playbooks` to validate and upload playbooks.
