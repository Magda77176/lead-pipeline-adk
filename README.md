# Lead Pipeline — Google ADK Multi-Agent System

A production-ready multi-agent pipeline built with **Google ADK** (Agent Development Kit) that processes leads through enrichment, qualification, and notification stages.

## Architecture

```
                    ┌─────────────────┐
                    │  SequentialAgent │
                    │  (Orchestrator)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Enrichment │  │Qualification│  │Notification│
     │   Agent    │  │   Agent    │  │   Agent    │
     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
           │               │               │
     ┌─────┴─────┐    ┌────┴────┐    ┌─────┴─────┐
     │ CRM Check │    │ Qualify │    │  Notify   │
     │ Enrich    │    │  (ICP)  │    │ Slack/CRM │
     │ Contacts  │    └─────────┘    └───────────┘
     └───────────┘
```

## Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | Google ADK (SequentialAgent, FunctionTools) |
| **LLM** | Gemini 2.5 Flash (via Google GenAI API) |
| **API** | FastAPI + Pydantic v2 |
| **Runtime** | Cloud Run (serverless, scale-to-zero) |
| **CI/CD** | GitHub Actions → Artifact Registry → Cloud Run |
| **Tests** | pytest (20 tests — tools, agents, API) |

## Quick Start

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set API key
echo "GOOGLE_API_KEY=your_key" > lead_pipeline/.env

# Run locally
python main.py

# Run tests
pytest tests/ -v
```

## API Endpoints

### `POST /process` — Process a lead

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"company_name": "L'\''Oréal Paris", "website": "loreal.com"}'
```

Response includes full pipeline trace: tool calls, results, and agent reasoning.

### `GET /health` — Health check

```bash
curl http://localhost:8080/health
```

### `GET /docs` — Swagger UI (auto-generated)

## Key Design Decisions

- **SequentialAgent over ParallelAgent**: Lead processing is inherently sequential — you can't qualify before enriching
- **FunctionTools over MCP**: Simpler for internal tools; MCP reserved for cross-service integrations
- **InMemorySession**: Sufficient for stateless Cloud Run; swap to Firestore for persistent sessions
- **Pydantic validation**: Every input/output is typed — catches bad data before it hits the LLM

## Deploy to Cloud Run

```bash
# Build & deploy
gcloud builds submit --tag europe-west1-docker.pkg.dev/PROJECT_ID/cloud-run/lead-pipeline-adk
gcloud run deploy lead-pipeline-adk \
  --image europe-west1-docker.pkg.dev/PROJECT_ID/cloud-run/lead-pipeline-adk \
  --region europe-west1 \
  --set-env-vars "GOOGLE_API_KEY=your_key"
```

## Author

**Sullivan Magdaleon** — AI Systems Engineer
- Multi-agent systems in production (15+ agents)
- RAG, LLM orchestration, tool calling
- [LinkedIn](https://linkedin.com/in/sullivan-magdaleon-980203130)
