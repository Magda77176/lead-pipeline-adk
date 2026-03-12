"""
Configuration module — reads secrets from environment or Secret Manager.
Shows both approaches for interview discussion.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """App configuration — populated from env vars (injected by Cloud Run from Secret Manager)."""
    
    # Secrets (injected by Cloud Run --set-secrets)
    google_api_key: str = ""
    emarsys_api_secret: str = ""
    magento_api_token: str = ""
    
    # Config (injected by Cloud Run --set-env-vars)
    magento_base_url: str = "https://store.example.com/rest/V1"
    emarsys_api_url: str = "https://api.emarsys.net/api/v2"
    environment: str = "production"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"  # For local development


@lru_cache()
def get_settings() -> Settings:
    """Singleton — loaded once, cached forever."""
    return Settings()


# ============================================================
# Alternative: Read directly from Secret Manager (for non-Cloud Run)
# ============================================================

def get_secret_from_gcp(secret_id: str, project_id: str = "jarvis-v2-488311") -> str:
    """Read a secret directly from Secret Manager.
    
    Use this when NOT on Cloud Run (e.g., local dev, GCE, GKE).
    On Cloud Run, prefer --set-secrets (zero code needed).
    """
    from google.cloud import secretmanager
    
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


# ============================================================
# Interview talking points:
# ============================================================
#
# Q: "Why not just use environment variables directly?"
# A: "Secret Manager adds versioning, rotation, audit logs, and 
#     IAM-based access control. If a key leaks, I disable the 
#     version instantly without redeploying."
#
# Q: "Why --set-secrets instead of reading from SDK?"
# A: "Cloud Run injects secrets at startup — zero latency, zero 
#     SDK dependency. The app doesn't even know it's using Secret 
#     Manager. For non-Cloud Run (GKE, local), I fall back to the SDK."
#
# Q: "How do you handle key rotation?"
# A: "Add new version → redeploy (picks up :latest) → disable old 
#     version. Zero downtime. If the new key is broken, re-enable 
#     the old version in 10 seconds."
#
# Q: "Who can access the secrets?"
# A: "Only the pipeline's Service Account has secretAccessor role.
#     Not editor, not admin — just read. I can't even create or 
#     delete secrets from the running service."
