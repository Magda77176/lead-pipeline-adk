"""
E-Commerce Agent Pipeline — Google ADK
Multi-agent system for customer profiling, product recommendation, and engagement.
Integrates with Magento 2 REST API.
"""

from google.adk.agents import Agent, SequentialAgent
from typing import Optional


# ============================================================
# TOOLS — Magento 2 API integrations
# ============================================================

def get_customer_profile(customer_id: str) -> dict:
    """Retrieves customer profile and purchase history from Magento.
    
    Args:
        customer_id: Magento customer ID.
    
    Returns:
        dict: Customer data including demographics and purchase history.
    """
    # Production: GET /rest/V1/customers/{id} + /rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=customer_id
    return {
        "status": "success",
        "customer": {
            "id": customer_id,
            "email": "marie.dupont@email.com",
            "firstname": "Marie",
            "lastname": "Dupont",
            "group": "VIP",
            "created_at": "2024-03-15",
            "total_orders": 12,
            "lifetime_value": 847.50,
            "avg_order_value": 70.63,
            "last_order_date": "2026-02-28",
            "days_since_last_order": 12,
            "preferred_categories": ["skincare", "makeup"],
            "preferred_brands": ["True Match", "Revitalift"],
            "payment_method": "card",
            "shipping_preference": "express"
        }
    }


def get_order_history(customer_id: str, limit: str = "5") -> dict:
    """Retrieves recent orders for a customer from Magento.
    
    Args:
        customer_id: Magento customer ID.
        limit: Number of recent orders to retrieve.
    
    Returns:
        dict: List of recent orders with items and amounts.
    """
    # Production: GET /rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=customer_id&searchCriteria[sortOrders][0][field]=created_at&searchCriteria[sortOrders][0][direction]=DESC
    return {
        "status": "success",
        "orders": [
            {
                "order_id": "100004892",
                "date": "2026-02-28",
                "total": 89.90,
                "items": [
                    {"sku": "TRUMATCH-FDT-03", "name": "True Match Foundation - 03 Beige", "qty": 1, "price": 14.90},
                    {"sku": "REVI-SERUM-50", "name": "Revitalift Serum 50ml", "qty": 1, "price": 32.00},
                    {"sku": "LASH-PARA-BLK", "name": "Lash Paradise Mascara Black", "qty": 2, "price": 21.50}
                ],
                "status": "complete"
            },
            {
                "order_id": "100004567",
                "date": "2026-01-15",
                "total": 54.80,
                "items": [
                    {"sku": "TRUMATCH-PWD-03", "name": "True Match Powder - 03 Beige", "qty": 1, "price": 12.90},
                    {"sku": "COLOR-RICHE-235", "name": "Color Riche Lipstick - 235 Nude", "qty": 1, "price": 11.90},
                    {"sku": "MICEL-WATER-400", "name": "Micellar Water 400ml", "qty": 1, "price": 9.90},
                    {"sku": "REVI-CREAM-50", "name": "Revitalift Day Cream 50ml", "qty": 1, "price": 20.10}
                ],
                "status": "complete"
            },
            {
                "order_id": "100004201",
                "date": "2025-12-02",
                "total": 125.70,
                "items": [
                    {"sku": "GIFT-SET-REVI", "name": "Revitalift Gift Set Premium", "qty": 1, "price": 79.90},
                    {"sku": "TRUMATCH-FDT-03", "name": "True Match Foundation - 03 Beige", "qty": 1, "price": 14.90},
                    {"sku": "BROW-ART-MICRO", "name": "Brow Artist Micro Pen", "qty": 1, "price": 10.90},
                    {"sku": "MICEL-WATER-400", "name": "Micellar Water 400ml", "qty": 1, "price": 9.90}
                ],
                "status": "complete"
            }
        ]
    }


def get_product_catalog(category: str, limit: str = "10") -> dict:
    """Searches the Magento product catalog for recommendations.
    
    Args:
        category: Product category to search (skincare, makeup, haircare).
        limit: Maximum number of products to return.
    
    Returns:
        dict: Available products with stock and pricing.
    """
    # Production: GET /rest/V1/products?searchCriteria[filter_groups][0][filters][0][field]=category_id
    catalogs = {
        "skincare": [
            {"sku": "REVI-NIGHT-50", "name": "Revitalift Night Cream 50ml", "price": 22.90, "stock": 145, "rating": 4.6, "new": False},
            {"sku": "REVI-EYE-15", "name": "Revitalift Eye Cream 15ml", "price": 18.90, "stock": 89, "rating": 4.4, "new": False},
            {"sku": "HYAL-SERUM-30", "name": "Hyaluron Expert Serum 30ml", "price": 28.90, "stock": 230, "rating": 4.8, "new": True},
            {"sku": "PURE-CLAY-MASK", "name": "Pure Clay Mask Detox", "price": 9.90, "stock": 340, "rating": 4.2, "new": False},
        ],
        "makeup": [
            {"sku": "INFALL-24H-FDT", "name": "Infallible 24H Foundation", "price": 17.90, "stock": 200, "rating": 4.5, "new": True},
            {"sku": "TELESCOPIC-MSC", "name": "Telescopic Mascara Lift", "price": 15.90, "stock": 180, "rating": 4.7, "new": True},
            {"sku": "COLOR-RICHE-NEW", "name": "Color Riche Satin Collection", "price": 13.90, "stock": 150, "rating": 4.3, "new": True},
            {"sku": "TRUMATCH-CONC", "name": "True Match Concealer", "price": 11.90, "stock": 95, "rating": 4.4, "new": False},
        ],
    }
    products = catalogs.get(category, catalogs["skincare"])
    return {"status": "success", "category": category, "products": products}


def check_cart_abandonment(customer_id: str) -> dict:
    """Checks if the customer has an abandoned cart in Magento.
    
    Args:
        customer_id: Magento customer ID.
    
    Returns:
        dict: Abandoned cart details if any.
    """
    # Production: GET /rest/V1/carts/search?searchCriteria[filter_groups][0][filters][0][field]=customer_id&is_active=1
    return {
        "status": "success",
        "has_abandoned_cart": True,
        "cart": {
            "cart_id": "quote_78234",
            "created_at": "2026-03-10",
            "items": [
                {"sku": "HYAL-SERUM-30", "name": "Hyaluron Expert Serum 30ml", "qty": 1, "price": 28.90},
                {"sku": "REVI-EYE-15", "name": "Revitalift Eye Cream 15ml", "qty": 1, "price": 18.90}
            ],
            "total": 47.80,
            "coupon_applied": False
        }
    }


def generate_discount_code(customer_id: str, discount_percent: str, reason: str) -> dict:
    """Generates a personalized discount code via Magento Cart Price Rules.
    
    Args:
        customer_id: Customer to generate the code for.
        discount_percent: Discount percentage (e.g. "10", "15", "20").
        reason: Reason for the discount (abandonment, loyalty, winback).
    
    Returns:
        dict: Generated coupon code and details.
    """
    # Production: POST /rest/V1/salesRules + POST /rest/V1/coupons
    code = f"VIP-{customer_id[-4:]}-{discount_percent}"
    return {
        "status": "success",
        "coupon": {
            "code": code,
            "discount_percent": int(discount_percent),
            "valid_until": "2026-03-19",
            "min_order": 30.00,
            "single_use": True,
            "reason": reason
        }
    }


def emarsys_get_contact(customer_email: str) -> dict:
    """Retrieves contact data and interaction history from Emarsys CRM.
    
    Args:
        customer_email: Customer email to look up in Emarsys.
    
    Returns:
        dict: Emarsys contact profile with segments, scores, and campaign history.
    """
    # Production: POST /api/v2/contact/getdata (Emarsys API)
    # Auth: X-WSSE header (username + secret + nonce + timestamp)
    return {
        "status": "success",
        "contact": {
            "id": "emarsys_892341",
            "email": customer_email,
            "engagement_score": 72,
            "rfm_segment": "champions",  # Emarsys RFM: champions, loyal, at_risk, lost
            "opted_in": True,
            "preferred_channel": "email",
            "last_email_opened": "2026-03-08",
            "last_email_clicked": "2026-03-01",
            "open_rate": 0.45,
            "click_rate": 0.12,
            "campaigns_received_30d": 4,
            "lifecycle_stage": "active",
            "smart_insight": "High probability of repeat purchase within 7 days"
        }
    }


def emarsys_trigger_automation(program_id: str, customer_email: str, event_data: str) -> dict:
    """Triggers an Emarsys Automation Center program for a specific contact.
    
    Args:
        program_id: Emarsys automation program ID (e.g. 'cart_recovery_v2', 'vip_winback').
        customer_email: Contact email to enroll.
        event_data: JSON string with event context (product names, discount code, etc.).
    
    Returns:
        dict: Automation enrollment confirmation.
    """
    # Production: POST /api/v2/event/{event_id}/trigger (Emarsys External Events API)
    return {
        "status": "enrolled",
        "program_id": program_id,
        "contact": customer_email,
        "automation_steps": [
            {"step": 1, "action": "email", "delay": "0h", "template": "personalized_reco"},
            {"step": 2, "action": "wait", "delay": "48h", "condition": "not_purchased"},
            {"step": 3, "action": "push_notification", "delay": "0h", "template": "reminder_with_coupon"},
            {"step": 4, "action": "wait", "delay": "72h", "condition": "not_purchased"},
            {"step": 5, "action": "email", "delay": "0h", "template": "last_chance_offer"}
        ],
        "estimated_completion": "2026-03-19"
    }


def emarsys_update_segment(customer_email: str, segment: str, tags: str) -> dict:
    """Updates contact segment and tags in Emarsys.
    
    Args:
        customer_email: Contact email to update.
        segment: New segment (champions, loyal, at_risk, hibernating, lost).
        tags: Comma-separated tags to add to the contact.
    
    Returns:
        dict: Update confirmation with segment details.
    """
    # Production: PUT /api/v2/contact (Emarsys Contact API)
    return {
        "status": "updated",
        "email": customer_email,
        "segment": segment,
        "tags_added": [t.strip() for t in tags.split(",")],
        "rfm_updated": True,
        "updated_at": "2026-03-12T12:00:00Z"
    }


def send_engagement(channel: str, customer_email: str, subject: str, content: str) -> dict:
    """Sends a one-shot personalized message (used when Emarsys automation is not needed).
    
    Args:
        channel: Delivery channel (email, push, sms).
        customer_email: Customer email address.
        subject: Message subject line.
        content: Message body content.
    
    Returns:
        dict: Delivery status and tracking info.
    """
    # Production: Emarsys POST /api/v2/email/send or transactional API
    return {
        "status": "delivered",
        "channel": channel,
        "to": customer_email,
        "subject": subject,
        "tracking_id": f"msg_{channel}_20260312_001",
        "open_tracking": True,
        "click_tracking": True
    }


# ============================================================
# AGENTS
# ============================================================

# Agent 1: Customer Profiling — who is this customer?
profiling_agent = Agent(
    name="profiling_agent",
    model="gemini-2.5-flash",
    description="Analyzes customer profile, purchase history, and behavior patterns from Magento.",
    instruction="""You are a customer intelligence analyst. Given a customer ID:
    1. Get the customer profile from Magento using get_customer_profile
    2. Get their recent order history using get_order_history
    3. Check for abandoned carts using check_cart_abandonment
    4. Get their Emarsys CRM profile using emarsys_get_contact (engagement score, RFM segment, campaign history)
    5. Cross-reference Magento purchase data with Emarsys engagement signals
    6. Identify the customer's lifecycle stage combining both data sources
    
    Key Emarsys metrics to highlight:
    - RFM segment (champions/loyal/at_risk/lost)
    - Engagement score and email open/click rates
    - Smart Insight prediction
    
    Produce a clear customer brief merging Magento + Emarsys insights.""",
    tools=[get_customer_profile, get_order_history, check_cart_abandonment, emarsys_get_contact],
)

# Agent 2: Product Recommendation — what should we recommend?
recommendation_agent = Agent(
    name="recommendation_agent",
    model="gemini-2.5-flash",
    description="Generates personalized product recommendations based on customer profile and catalog.",
    instruction="""You are a product recommendation engine. Based on the customer profile:
    1. Search the product catalog for relevant categories using get_product_catalog
    2. Identify cross-sell opportunities (complementary products to past purchases)
    3. Identify upsell opportunities (premium versions of products they buy)
    4. Prioritize NEW products that match their preferences
    5. If there's an abandoned cart, factor those items into recommendations
    6. Consider generating a discount code if the customer is at-risk or has an abandoned cart
    
    Output: Top 3-5 personalized recommendations with reasoning for each.
    Never recommend products they've already purchased recently.""",
    tools=[get_product_catalog, generate_discount_code],
)

# Agent 3: Customer Engagement — how do we reach them?
engagement_agent = Agent(
    name="engagement_agent",
    model="gemini-2.5-flash",
    description="Executes personalized customer engagement across channels.",
    instruction="""You are a customer engagement specialist using Emarsys as CRM. Based on the recommendations:
    1. Check the Emarsys engagement score and preferred channel from the customer brief
    2. For multi-step re-engagement → use emarsys_trigger_automation to enroll in an automation program:
       - 'cart_recovery_v2' for abandoned carts
       - 'vip_winback' for VIP at-risk customers
       - 'cross_sell_flow' for active customers with new recommendations
    3. For one-shot messages → use send_engagement (only if automation is overkill)
    4. Always update the Emarsys segment using emarsys_update_segment
    
    Channel selection (based on Emarsys data):
    - High open rate (>30%) → email first
    - Low open rate + opted in → push notification
    - SMS only for time-sensitive offers (flash sales, expiring coupons)
    
    Include event_data with: product names, discount code, customer name.""",
    tools=[emarsys_trigger_automation, send_engagement, emarsys_update_segment],
)

# ============================================================
# ORCHESTRATOR — Sequential pipeline
# ============================================================

root_agent = SequentialAgent(
    name="ecommerce_pipeline",
    description="E-commerce customer engagement pipeline: profile → recommend → engage.",
    sub_agents=[profiling_agent, recommendation_agent, engagement_agent],
)
