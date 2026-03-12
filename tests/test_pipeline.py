"""Tests for the E-Commerce Pipeline."""

import pytest
from fastapi.testclient import TestClient
from lead_pipeline.agent import (
    get_customer_profile, get_order_history, get_product_catalog,
    check_cart_abandonment, generate_discount_code, send_engagement,
    update_crm_segment, root_agent, profiling_agent,
    recommendation_agent, engagement_agent,
)


# ============================================================
# TOOL TESTS — Magento API integrations
# ============================================================

class TestCustomerProfile:
    def test_returns_customer_data(self):
        result = get_customer_profile("12345")
        assert result["status"] == "success"
        assert result["customer"]["id"] == "12345"
    
    def test_includes_purchase_metrics(self):
        result = get_customer_profile("12345")
        c = result["customer"]
        assert "total_orders" in c
        assert "lifetime_value" in c
        assert "avg_order_value" in c
        assert c["lifetime_value"] > 0


class TestOrderHistory:
    def test_returns_orders(self):
        result = get_order_history("12345")
        assert result["status"] == "success"
        assert len(result["orders"]) > 0
    
    def test_orders_have_items(self):
        result = get_order_history("12345")
        order = result["orders"][0]
        assert "items" in order
        assert len(order["items"]) > 0
        assert "sku" in order["items"][0]
        assert "price" in order["items"][0]


class TestProductCatalog:
    def test_skincare_catalog(self):
        result = get_product_catalog("skincare")
        assert result["status"] == "success"
        assert len(result["products"]) > 0
    
    def test_makeup_catalog(self):
        result = get_product_catalog("makeup")
        assert result["category"] == "makeup"
        assert any(p["new"] for p in result["products"])
    
    def test_products_have_required_fields(self):
        result = get_product_catalog("skincare")
        product = result["products"][0]
        for field in ["sku", "name", "price", "stock", "rating"]:
            assert field in product


class TestCartAbandonment:
    def test_detects_abandoned_cart(self):
        result = check_cart_abandonment("12345")
        assert result["has_abandoned_cart"] == True
        assert result["cart"]["total"] > 0


class TestDiscountCode:
    def test_generates_valid_code(self):
        result = generate_discount_code("12345", "15", "abandonment")
        assert result["status"] == "success"
        assert result["coupon"]["discount_percent"] == 15
        assert result["coupon"]["single_use"] == True
    
    def test_code_format(self):
        result = generate_discount_code("12345", "10", "loyalty")
        assert "VIP-" in result["coupon"]["code"]


class TestSendEngagement:
    def test_email_delivery(self):
        result = send_engagement("email", "test@test.com", "Subject", "Body")
        assert result["status"] == "delivered"
        assert result["channel"] == "email"
        assert result["open_tracking"] == True


class TestCrmSegment:
    def test_segment_update(self):
        result = update_crm_segment("12345", "vip_active", "skincare_lover, high_ltv")
        assert result["status"] == "updated"
        assert "skincare_lover" in result["tags_added"]


# ============================================================
# AGENT STRUCTURE TESTS
# ============================================================

class TestAgentStructure:
    def test_root_is_sequential(self):
        from google.adk.agents import SequentialAgent
        assert isinstance(root_agent, SequentialAgent)
    
    def test_pipeline_order(self):
        names = [a.name for a in root_agent.sub_agents]
        assert names == ["profiling_agent", "recommendation_agent", "engagement_agent"]
    
    def test_profiling_has_3_tools(self):
        assert len(profiling_agent.tools) == 3
    
    def test_recommendation_has_2_tools(self):
        assert len(recommendation_agent.tools) == 2
    
    def test_engagement_has_2_tools(self):
        assert len(engagement_agent.tools) == 2


# ============================================================
# API TESTS
# ============================================================

class TestAPI:
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
    
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert len(data["agents"]) == 3
    
    def test_process_validation(self, client):
        response = client.post("/process", json={})
        assert response.status_code == 422
