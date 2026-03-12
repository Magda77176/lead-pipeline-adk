"""
Lead Pipeline API — FastAPI + Google ADK
Exposes the multi-agent pipeline as a REST API on Cloud Run.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from lead_pipeline.agent import root_agent


# ============================================================
# MODELS — Pydantic schemas for request/response validation
# ============================================================

class LeadRequest(BaseModel):
    """Incoming lead to process through the pipeline."""
    company_name: str = Field(..., description="Name of the company", min_length=1)
    website: Optional[str] = Field(None, description="Company website URL")
    source: Optional[str] = Field("api", description="Lead source (api, form, import)")


class AgentStep(BaseModel):
    """A single step in the pipeline execution."""
    agent: str
    action: str  # "tool_call", "tool_result", "response"
    detail: str


class PipelineResponse(BaseModel):
    """Full pipeline execution response."""
    lead: str
    status: str
    steps: list[AgentStep]
    session_id: str


class HealthResponse(BaseModel):
    status: str
    agents: list[str]
    version: str


# ============================================================
# APP — FastAPI application
# ============================================================

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="lead_pipeline",
    session_service=session_service,
)

app = FastAPI(
    title="Lead Pipeline API",
    description="Multi-agent pipeline for lead enrichment, qualification, and notification. Built with Google ADK.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — returns agent configuration."""
    return HealthResponse(
        status="healthy",
        agents=[a.name for a in root_agent.sub_agents],
        version="1.0.0",
    )


@app.post("/process", response_model=PipelineResponse)
async def process_lead(lead: LeadRequest):
    """Process a lead through the full pipeline: enrich → qualify → notify."""
    
    # Create session for this lead
    session = await session_service.create_session(
        app_name="lead_pipeline",
        user_id=lead.source,
    )
    
    # Build the message
    prompt = f"Process this new lead: {lead.company_name}"
    if lead.website:
        prompt += f", website: {lead.website}"
    
    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )
    
    # Run the pipeline and collect steps
    steps = []
    try:
        async for event in runner.run_async(
            user_id=lead.source,
            session_id=session.id,
            new_message=message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        steps.append(AgentStep(
                            agent=event.author,
                            action="tool_call",
                            detail=f"{part.function_call.name}({dict(part.function_call.args)})",
                        ))
                    elif part.function_response:
                        resp_str = str(part.function_response.response)[:300]
                        steps.append(AgentStep(
                            agent=event.author,
                            action="tool_result",
                            detail=resp_str,
                        ))
                    elif part.text:
                        steps.append(AgentStep(
                            agent=event.author,
                            action="response",
                            detail=part.text[:500],
                        ))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    
    return PipelineResponse(
        lead=lead.company_name,
        status="completed",
        steps=steps,
        session_id=session.id,
    )


@app.get("/")
async def root():
    """API info."""
    return {
        "name": "Lead Pipeline API",
        "description": "Multi-agent pipeline built with Google ADK + FastAPI",
        "endpoints": {
            "POST /process": "Process a lead through enrichment → qualification → notification",
            "GET /health": "Health check and agent configuration",
            "GET /docs": "Swagger UI (auto-generated)",
        },
        "architecture": {
            "framework": "Google ADK (Agent Development Kit)",
            "agents": ["enrichment_agent", "qualification_agent", "notification_agent"],
            "orchestration": "SequentialAgent",
            "model": "Gemini 2.5 Flash",
            "runtime": "Cloud Run (serverless)",
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
