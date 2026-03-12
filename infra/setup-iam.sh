#!/bin/bash
# ============================================================
# IAM Setup — E-Commerce Pipeline
# Principle of Least Privilege: each service gets ONLY what it needs
# ============================================================

PROJECT_ID="jarvis-v2-488311"
REGION="europe-west1"
SERVICE_NAME="ecommerce-pipeline"

# 1. Create a dedicated Service Account for the pipeline
#    → NOT the default compute SA (too many permissions)
gcloud iam service-accounts create ${SERVICE_NAME}-sa \
  --display-name="E-Commerce Pipeline Agent" \
  --description="Runs the ADK multi-agent pipeline on Cloud Run" \
  --project=$PROJECT_ID

SA_EMAIL="${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# 2. Grant ONLY the roles this service needs
#    → "Least privilege" = minimum permissions to function

# Vertex AI User — call Gemini models
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/aiplatform.user"

# Secret Manager Accessor — read API keys (not create/delete!)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# Firestore User — read/write customer sessions (if using persistent sessions)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/datastore.user"

# Cloud Trace Agent — send traces for observability
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudtrace.agent"

# 3. Deploy Cloud Run WITH this specific SA
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --service-account $SA_EMAIL \
  --no-allow-unauthenticated  # ← Requires auth! Not open to the world

# 4. Allow only specific users/services to invoke the API
#    → Example: only the frontend service can call the pipeline
FRONTEND_SA="frontend-app@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region $REGION \
  --member="serviceAccount:$FRONTEND_SA" \
  --role="roles/run.invoker"

# Or allow Sullivan to call it directly (for testing)
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region $REGION \
  --member="user:sullivan.magdaleone@gmail.com" \
  --role="roles/run.invoker"

echo "✅ IAM configured with least privilege"
echo ""
echo "Service Account: $SA_EMAIL"
echo "Roles granted:"
echo "  - aiplatform.user (Gemini)"
echo "  - secretmanager.secretAccessor (API keys)"
echo "  - datastore.user (Firestore sessions)"
echo "  - cloudtrace.agent (observability)"
echo ""
echo "⚠️  NOT granted (on purpose):"
echo "  - roles/owner or roles/editor (too broad)"
echo "  - secretmanager.admin (can't create/delete secrets)"
echo "  - aiplatform.admin (can't deploy/delete models)"
