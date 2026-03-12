# E-Commerce Customer Pipeline — Google ADK

Multi-agent system that automates customer re-engagement on **Magento 2** stores. Profiles customers, generates personalized product recommendations, and executes targeted outreach — all orchestrated by **Google ADK**.

## How It Works

```
Customer hasn't ordered in 12 days
        │
        ▼
┌──────────────────┐
│  Profiling Agent │ ← Magento REST API
│                  │   • Customer data (orders, LTV, segments)
│                  │   • Purchase history & patterns
│                  │   • Abandoned cart detection
└────────┬─────────┘
         │  customer brief
         ▼
┌──────────────────┐
│ Recommendation   │ ← Product Catalog API
│      Agent       │   • Cross-sell (complementary products)
│                  │   • Upsell (premium alternatives)
│                  │   • Discount code generation
└────────┬─────────┘
         │  personalized offers
         ▼
┌──────────────────┐
│  Engagement      │ ← Email / Push / SMS
│      Agent       │   • Personalized message
│                  │   • Channel selection (email, push, SMS)
│                  │   • CRM segment update
└──────────────────┘
```

## Example Run

**Input:** `Customer 12345 hasn't ordered in 12 days.`

**What happens:**
1. **Profiling** → Marie Dupont, VIP, €847 lifetime value, 12 orders, prefers skincare + makeup. Abandoned cart detected: Hyaluron Serum + Revitalift Eye Cream (€47.80)
2. **Recommendation** → Recover abandoned cart items + cross-sell Telescopic Mascara (matches her makeup preferences). Generates coupon `VIP-2345-15` (15% off, single-use)
3. **Engagement** → Personalized email sent, CRM updated (segment: `vip_active`, tags: `re-engaged, abandoned_cart_recovery`)

## Stack

| Layer | Technology |
|-------|-----------|
| Agent orchestration | Google ADK — `SequentialAgent` |
| LLM | Gemini 2.5 Flash |
| API | FastAPI + Pydantic v2 |
| E-commerce | Magento 2 REST API (`/rest/V1/`) |
| Runtime | Cloud Run (serverless) |
| CI/CD | GitHub Actions → Artifact Registry → Cloud Run |
| Tests | pytest — 20 tests |

## Magento API Tools

| Tool | Magento Endpoint | Purpose |
|------|-----------------|---------|
| `get_customer_profile` | `GET /rest/V1/customers/{id}` | Demographics, LTV, segments |
| `get_order_history` | `GET /rest/V1/orders` | Recent purchases, items, amounts |
| `check_cart_abandonment` | `GET /rest/V1/carts/search` | Active abandoned carts |
| `get_product_catalog` | `GET /rest/V1/products` | Category browsing, stock, ratings |
| `generate_discount_code` | `POST /rest/V1/salesRules` | Personalized coupon codes |
| `send_engagement` | SendGrid / Brevo API | Email, push, SMS delivery |
| `update_crm_segment` | `PUT /rest/V1/customers/{id}` | Segment + tag updates |

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# API key
echo "GOOGLE_API_KEY=your_key" > lead_pipeline/.env

# Run
python main.py          # API on :8080
pytest tests/ -v        # 20 tests
```

## API

```bash
# Process a customer
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Customer 12345"}'

# Health check
curl http://localhost:8080/health

# Swagger docs
open http://localhost:8080/docs
```

## Design Decisions

| Decision | Why |
|----------|-----|
| **SequentialAgent** over Parallel | Can't recommend before profiling — order matters |
| **FunctionTools** over MCP | Internal tools don't need cross-service protocol overhead |
| **InMemorySession** | Stateless Cloud Run; swap to Firestore for persistence |
| **Mock tools** with real signatures | Swap `return {...}` for actual Magento API calls — zero refactor |
| **Pydantic v2 validation** | Type-safe API — bad data caught before LLM |

## Deploy

```bash
# Cloud Run (one command)
gcloud run deploy ecommerce-pipeline \
  --source . \
  --region europe-west1 \
  --set-env-vars "GOOGLE_API_KEY=your_key" \
  --allow-unauthenticated
```

## Production Roadmap

- [ ] Replace mock tools with live Magento 2 API calls
- [ ] Add Firestore session persistence for multi-turn conversations
- [ ] A/B test engagement channels (email vs push vs SMS)
- [ ] Add OpenTelemetry tracing per agent step
- [ ] Rate limiting on Magento API calls

## Author

**Sullivan Magdaleon** — AI & Automation Engineer  
Multi-agent systems in production (15+ agents) · RAG · LLM orchestration  
[LinkedIn](https://linkedin.com/in/sullivan-magdaleon-980203130)
