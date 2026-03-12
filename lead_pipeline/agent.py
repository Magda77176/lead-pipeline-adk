"""
Lead Pipeline Agent — Google ADK Demo
Multi-agent system for lead enrichment, qualification, and notification.
Built for L'Oréal interview prep.
"""

from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import FunctionTool
from typing import Optional
import json


# ============================================================
# TOOLS — Les outils que les agents peuvent appeler
# ============================================================

def enrich_lead(company_name: str, website: Optional[str] = None) -> dict:
    """Enriches a lead with company data from external sources.
    
    Args:
        company_name: Name of the company to enrich.
        website: Optional website URL for additional data.
    
    Returns:
        dict: Enriched company data including industry, size, and tech stack.
    """
    # In production: call Clearbit, Hunter.io, LinkedIn API
    enrichment = {
        "company_name": company_name,
        "industry": "beauty_and_cosmetics" if "oreal" in company_name.lower() or "oréal" in company_name.lower() else "technology",
        "employee_count": "10000+",
        "tech_stack": ["Python", "GCP", "Kubernetes", "Vertex AI"],
        "headquarters": "Paris, France",
        "website": website or f"https://www.{company_name.lower().replace(' ', '')}.com",
        "enrichment_source": "clearbit_api",
        "enrichment_confidence": 0.92
    }
    return {"status": "success", "data": enrichment}


def search_contacts(company_name: str, role: str = "CTO") -> dict:
    """Searches for key contacts at a company.
    
    Args:
        company_name: Company to search contacts for.
        role: Target role/title to search for.
    
    Returns:
        dict: List of matching contacts.
    """
    # In production: call Hunter.io, Apollo, LinkedIn Sales Nav
    return {
        "status": "success",
        "contacts": [
            {
                "name": "Marie Dupont",
                "title": f"VP {role}",
                "email": f"m.dupont@{company_name.lower().replace(' ', '')}.com",
                "linkedin": f"linkedin.com/in/marie-dupont",
                "confidence": 0.88
            }
        ]
    }


def qualify_lead(company_name: str, industry: str, employee_count: str, tech_stack: str) -> dict:
    """Qualifies a lead based on ICP (Ideal Customer Profile) criteria.
    
    Args:
        company_name: Name of the company.
        industry: Industry sector.
        employee_count: Size of the company.
        tech_stack: Technologies used by the company.
    
    Returns:
        dict: Qualification score and reasoning.
    """
    score = 0
    reasons = []
    
    # Industry fit
    if industry in ["beauty_and_cosmetics", "luxury", "retail", "fmcg"]:
        score += 30
        reasons.append("Industry match: beauty/luxury/retail")
    elif industry in ["technology", "saas"]:
        score += 20
        reasons.append("Tech company - potential fit")
    
    # Size fit
    if "1000" in employee_count or "10000" in employee_count:
        score += 25
        reasons.append("Enterprise size - high value")
    elif "500" in employee_count:
        score += 15
        reasons.append("Mid-market - good fit")
    
    # Tech stack fit (parse comma-separated string)
    stack_list = [t.strip() for t in tech_stack.split(",")] if isinstance(tech_stack, str) else tech_stack
    ai_tech = [t for t in stack_list if t.lower() in ["python", "gcp", "vertex ai", "kubernetes", "tensorflow", "pytorch"]]
    if len(ai_tech) >= 2:
        score += 25
        reasons.append(f"Strong AI/ML stack: {', '.join(ai_tech)}")
    
    # Budget indicator
    if score >= 60:
        score += 20
        reasons.append("High likelihood of AI budget")
    
    qualification = "hot" if score >= 70 else "warm" if score >= 50 else "cold"
    
    return {
        "status": "success",
        "score": score,
        "max_score": 100,
        "qualification": qualification,
        "reasons": reasons,
        "recommended_action": "immediate_outreach" if qualification == "hot" else "nurture_sequence"
    }


def send_notification(channel: str, message: str, lead_name: str, score: int) -> dict:
    """Sends a notification about a qualified lead.
    
    Args:
        channel: Notification channel (slack, email, crm).
        message: Notification message body.
        lead_name: Name of the lead company.
        score: Qualification score.
    
    Returns:
        dict: Notification delivery status.
    """
    # In production: call Slack API, SendGrid, or CRM webhook
    return {
        "status": "delivered",
        "channel": channel,
        "lead": lead_name,
        "score": score,
        "message": message,
        "timestamp": "2026-03-12T11:30:00Z"
    }


def check_crm_duplicate(company_name: str) -> dict:
    """Checks if a lead already exists in the CRM.
    
    Args:
        company_name: Company name to check for duplicates.
    
    Returns:
        dict: Whether the lead exists and its current status.
    """
    # In production: query Salesforce/HubSpot API
    return {
        "status": "success",
        "exists": False,
        "message": f"No existing record found for {company_name}"
    }


# ============================================================
# AGENTS — Architecture multi-agents
# ============================================================

# Agent 1: Enrichissement (recherche info entreprise + contacts)
enrichment_agent = Agent(
    name="enrichment_agent",
    model="gemini-2.5-flash",
    description="Enriches leads with company data and contact information.",
    instruction="""You are a lead enrichment specialist. When given a company name:
    1. First check if the lead already exists in the CRM using check_crm_duplicate
    2. Use enrich_lead to get company data (industry, size, tech stack)
    3. Use search_contacts to find key decision makers
    4. Return a structured summary of all enriched data
    
    Always verify data quality and flag low-confidence results.""",
    tools=[enrich_lead, search_contacts, check_crm_duplicate],
)

# Agent 2: Qualification (scoring basé sur ICP)
qualification_agent = Agent(
    name="qualification_agent",
    model="gemini-2.5-flash",
    description="Qualifies leads based on Ideal Customer Profile criteria.",
    instruction="""You are a lead qualification expert. Given enriched lead data:
    1. Use qualify_lead with the enrichment data
    2. Analyze the qualification score and reasons
    3. Provide a clear recommendation: immediate outreach, nurture, or disqualify
    4. Suggest the best approach based on the lead's profile
    
    Be precise with scores. Never inflate qualification to seem productive.""",
    tools=[qualify_lead],
)

# Agent 3: Notification (alertes sur leads qualifiés)
notification_agent = Agent(
    name="notification_agent",
    model="gemini-2.5-flash",
    description="Sends notifications for qualified leads to the sales team.",
    instruction="""You are a notification dispatcher. Given a qualified lead:
    1. If score >= 70 (hot): send to both 'slack' and 'crm' channels
    2. If score >= 50 (warm): send to 'crm' channel only
    3. If score < 50 (cold): send to 'crm' with low priority
    4. Include the score, qualification level, and recommended action
    
    Format messages clearly for sales team consumption.""",
    tools=[send_notification],
)

# ============================================================
# ORCHESTRATOR — Pipeline séquentiel
# ============================================================

root_agent = SequentialAgent(
    name="lead_pipeline",
    description="Multi-agent pipeline that enriches, qualifies, and routes leads.",
    sub_agents=[enrichment_agent, qualification_agent, notification_agent],
)
