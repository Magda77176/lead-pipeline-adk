#!/bin/bash
# ============================================================
# Secret Manager Setup — E-Commerce Pipeline
# NEVER hardcode API keys. Store them in Secret Manager.
# ============================================================

PROJECT_ID="jarvis-v2-488311"

# 1. Create secrets (one per key/credential)
echo -n "your-gemini-api-key" | \
  gcloud secrets create GOOGLE_API_KEY \
    --data-file=- \
    --replication-policy="automatic" \
    --project=$PROJECT_ID \
    --labels="app=ecommerce-pipeline,env=production"

echo -n "your-emarsys-api-secret" | \
  gcloud secrets create EMARSYS_API_SECRET \
    --data-file=- \
    --replication-policy="automatic" \
    --project=$PROJECT_ID \
    --labels="app=ecommerce-pipeline,env=production"

echo -n "your-magento-token" | \
  gcloud secrets create MAGENTO_API_TOKEN \
    --data-file=- \
    --replication-policy="automatic" \
    --project=$PROJECT_ID \
    --labels="app=ecommerce-pipeline,env=production"

# 2. Version management — rotate a key without downtime
echo -n "new-rotated-key" | \
  gcloud secrets versions add GOOGLE_API_KEY --data-file=-
# → Old version still works until you disable it
gcloud secrets versions disable 1 --secret=GOOGLE_API_KEY
# → Now only version 2 is active

# 3. Deploy Cloud Run with secrets injected as env vars
gcloud run deploy ecommerce-pipeline \
  --source . \
  --region europe-west1 \
  --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest,EMARSYS_API_SECRET=EMARSYS_API_SECRET:latest,MAGENTO_API_TOKEN=MAGENTO_API_TOKEN:latest"
  # ↑ Cloud Run reads from Secret Manager at startup
  # The app sees them as normal env vars: os.environ["GOOGLE_API_KEY"]

echo "✅ Secrets configured"
echo ""
echo "How it works in the app:"
echo '  api_key = os.environ["GOOGLE_API_KEY"]  # Injected by Cloud Run'
echo ""
echo "Key rotation:"
echo "  1. gcloud secrets versions add GOOGLE_API_KEY --data-file=-"
echo "  2. gcloud run deploy ... (redeploy picks up latest)"
echo "  3. gcloud secrets versions disable OLD_VERSION"
