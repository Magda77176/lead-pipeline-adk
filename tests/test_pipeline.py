"""Tests for the Lead Pipeline API."""

import pytest
from fastapi.testclient import TestClient
from lead_pipeline.agent import (
    enrich_lead, search_contacts, qualify_lead,
    send_notification, check_crm_duplicate,
    root_agent, enrichment_agent, qualification_agent, notification_agent,
)


# ============================================================
# TOOL TESTS — Verify each tool works independently
# ============================================================

class TestEnrichLead:
    def test_enrich_returns_success(self):
        result = enrich_lead("Test Corp", "testcorp.com")
        assert result["status"] == "success"
        assert result["data"]["company_name"] == "Test Corp"
    
    def test_enrich_detects_beauty_industry(self):
        result = enrich_lead("L'Oréal")
        assert result["data"]["industry"] == "beauty_and_cosmetics"
    
    def test_enrich_default_industry(self):
        result = enrich_lead("Random Tech")
        assert result["data"]["industry"] == "technology"


class TestSearchContacts:
    def test_search_returns_contacts(self):
        result = search_contacts("Test Corp", "CTO")
        assert result["status"] == "success"
        assert len(result["contacts"]) > 0
    
    def test_contact_has_required_fields(self):
        result = search_contacts("Test Corp")
        contact = result["contacts"][0]
        assert "name" in contact
        assert "email" in contact
        assert "title" in contact


class TestQualifyLead:
    def test_hot_lead_beauty_enterprise(self):
        result = qualify_lead(
            company_name="L'Oréal",
            industry="beauty_and_cosmetics",
            employee_count="10000+",
            tech_stack="Python, GCP, Vertex AI"
        )
        assert result["qualification"] == "hot"
        assert result["score"] >= 70
    
    def test_cold_lead_small_unknown(self):
        result = qualify_lead(
            company_name="Small Co",
            industry="unknown",
            employee_count="5",
            tech_stack="WordPress"
        )
        assert result["qualification"] == "cold"
        assert result["score"] < 50
    
    def test_score_never_exceeds_100(self):
        result = qualify_lead(
            company_name="Perfect Corp",
            industry="beauty_and_cosmetics",
            employee_count="10000+",
            tech_stack="Python, GCP, Vertex AI, Kubernetes, TensorFlow, PyTorch"
        )
        assert result["score"] <= 100


class TestSendNotification:
    def test_notification_delivered(self):
        result = send_notification("slack", "Test message", "Test Corp", 85)
        assert result["status"] == "delivered"
        assert result["channel"] == "slack"
    
    def test_notification_includes_score(self):
        result = send_notification("crm", "Hot lead!", "L'Oréal", 90)
        assert result["score"] == 90


class TestCrmDuplicate:
    def test_no_duplicate_found(self):
        result = check_crm_duplicate("New Company")
        assert result["exists"] == False


# ============================================================
# AGENT STRUCTURE TESTS — Verify ADK agent configuration
# ============================================================

class TestAgentStructure:
    def test_root_agent_is_sequential(self):
        from google.adk.agents import SequentialAgent
        assert isinstance(root_agent, SequentialAgent)
    
    def test_root_has_three_sub_agents(self):
        assert len(root_agent.sub_agents) == 3
    
    def test_sub_agent_names(self):
        names = [a.name for a in root_agent.sub_agents]
        assert "enrichment_agent" in names
        assert "qualification_agent" in names
        assert "notification_agent" in names
    
    def test_enrichment_agent_has_tools(self):
        assert len(enrichment_agent.tools) == 3  # enrich, contacts, crm_check
    
    def test_qualification_agent_has_tools(self):
        assert len(qualification_agent.tools) == 1  # qualify
    
    def test_notification_agent_has_tools(self):
        assert len(notification_agent.tools) == 1  # notify


# ============================================================
# API TESTS — Verify FastAPI endpoints
# ============================================================

class TestAPI:
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "architecture" in data
        assert data["architecture"]["framework"] == "Google ADK (Agent Development Kit)"
    
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert len(data["agents"]) == 3
    
    def test_process_requires_company_name(self, client):
        response = client.post("/process", json={})
        assert response.status_code == 422  # Validation error
