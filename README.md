# OpenSOAR Playbooks

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![run-as-daemon.ru](https://img.shields.io/badge/by-run--as--daemon.ru-orange)](https://run-as-daemon.ru)

**Open-source SOAR playbook engine for incident response automation**

OpenSOAR Playbooks is a production-grade Security Orchestration, Automation and Response (SOAR) platform that helps SOC teams automate incident response workflows using YAML-based playbooks.

🔗 **Website**: [run-as-daemon.ru](https://run-as-daemon.ru)  
👤 **Author**: [@ranas-mukminov](https://github.com/ranas-mukminov)

---

## Features

✅ **YAML-based Playbook DSL** - Define complex workflows without coding  
✅ **Execution Engine** - Async playbook execution with pause/resume  
✅ **Connector Framework** - Pluggable integrations (firewall, ticketing, email, Slack, etc.)  
✅ **Human-in-the-Loop** - Manual approval steps in automated workflows  
✅ **Conditional Logic** - Branch based on incident data or previous step outputs  
✅ **REST API** - Complete FastAPI backend for playbook and incident management  
✅ **Jinja2 Templating** - Dynamic data access with `{{ incident.severity }}`  
✅ **Production Ready** - PostgreSQL storage, structured logging, comprehensive tests  

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Virtual environment tool (venv, virtualenv)

### Installation

```bash
# Clone the repository
git clone https://github.com/ranas-mukminov/OpenSOAR-Playbooks.git
cd OpenSOAR-Playbooks

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
alembic upgrade head

# Run the API server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

### Running Tests

```bash
pytest
```

---

## Example Usage

### 1. Upload a Playbook

```bash
curl -X POST http://localhost:8000/playbooks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-this" \
  -d @examples/playbooks/block_ip_and_ticket.yaml
```

### 2. Create an Incident

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-this" \
  -d '{
    "title": "Malicious IP detected",
    "severity": "high",
    "payload": {
      "src_ip": "192.0.2.1",
      "dest_port": 22
    },
    "tags": ["malicious_ip", "ssh_bruteforce"]
  }'
```

### 3. Run a Playbook

```bash
curl -X POST http://localhost:8000/playbooks/1/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-this" \
  -d '{"incident_id": 1}'
```

### 4. Check Execution Status

```bash
curl http://localhost:8000/runs/1 \
  -H "X-API-Key: your-secret-api-key-change-this"
```

---

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Playbook DSL Reference](docs/playbook_dsl.md)
- [Connector Development Guide](docs/connector_development.md)

---

## Example Playbooks

See [examples/playbooks/](examples/playbooks/) for complete examples:

- **block_ip_and_ticket.yaml** - Block malicious IP and create ticket
- **suspend_user_with_approval.yaml** - User suspension with manual approval
- **phishing_email_response.yaml** - Automated phishing email containment

---

## Commercial Support

**Professional services available from [run-as-daemon.ru](https://run-as-daemon.ru):**

- ✅ SOAR platform implementation and customization
- ✅ Custom connector development for proprietary systems
- ✅ Infrastructure audit and security automation consulting
- ✅ DevOps / SRE support and monitoring setup
- ✅ Backup and disaster recovery planning

**Contact**: [run-as-daemon.ru](https://run-as-daemon.ru)

---

## Project Structure

```
opensoar-playbooks/
├── app/
│   ├── api/              # FastAPI routes
│   ├── core/             # Business logic, engine, connectors
│   └── db/               # Database models and migrations
├── tests/                # Unit and integration tests
├── examples/playbooks/   # Sample YAML playbooks
└── docs/                 # Documentation
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) file

---

## Privacy & Compliance

This tool does not collect any telemetry or personal data by default. All data processed remains within your infrastructure.

For production deployments handling personal data, ensure compliance with:
- GDPR (EU General Data Protection Regulation)
- 152-ФЗ (Russian Federal Law on Personal Data)
- Other applicable local data protection regulations

---

**Built with ❤️ by [@ranas-mukminov](https://github.com/ranas-mukminov) | [run-as-daemon.ru](https://run-as-daemon.ru)**
