"""
Observability — OpenTelemetry integration for the pipeline.
Traces every agent step, tool call, and LLM invocation.
"""

import os
import time
import logging
from functools import wraps
from contextlib import contextmanager

# ============================================================
# OpenTelemetry Setup — sends traces to Cloud Trace
# ============================================================

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Resource = metadata attached to every trace
resource = Resource.create({
    "service.name": "ecommerce-pipeline",
    "service.version": "1.0.0",
    "deployment.environment": os.environ.get("ENVIRONMENT", "production"),
})

# Provider + Exporter → Cloud Trace
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(CloudTraceSpanExporter())  # Sends to GCP Cloud Trace
)
trace.set_tracer_provider(provider)

# Get a tracer for our pipeline
tracer = trace.get_tracer("ecommerce-pipeline")


# ============================================================
# DECORATORS — Add tracing to any function
# ============================================================

def trace_tool(tool_name: str):
    """Decorator to trace a tool call with timing and result."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(f"tool.{tool_name}") as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("tool.args", str(kwargs or args))
                
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("tool.status", result.get("status", "unknown"))
                    span.set_attribute("tool.duration_ms", int((time.time() - start) * 1000))
                    return result
                except Exception as e:
                    span.set_attribute("tool.error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator


def trace_agent(agent_name: str):
    """Context manager to trace an agent's execution."""
    @contextmanager
    def _trace():
        with tracer.start_as_current_span(f"agent.{agent_name}") as span:
            span.set_attribute("agent.name", agent_name)
            start = time.time()
            try:
                yield span
                span.set_attribute("agent.duration_ms", int((time.time() - start) * 1000))
            except Exception as e:
                span.set_attribute("agent.error", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    return _trace()


def trace_llm_call(model: str, prompt_tokens: int = 0, completion_tokens: int = 0):
    """Trace an LLM API call with token counts and cost estimation."""
    @contextmanager
    def _trace():
        with tracer.start_as_current_span("llm.generate") as span:
            span.set_attribute("llm.model", model)
            start = time.time()
            try:
                yield span
                duration = time.time() - start
                span.set_attribute("llm.duration_ms", int(duration * 1000))
                span.set_attribute("llm.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.completion_tokens", completion_tokens)
                # Cost estimation (Gemini 2.5 Flash pricing)
                cost = (prompt_tokens * 0.075 + completion_tokens * 0.30) / 1_000_000
                span.set_attribute("llm.estimated_cost_usd", round(cost, 6))
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    return _trace()


# ============================================================
# METRICS — Custom counters for business KPIs
# ============================================================

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter

meter_provider = MeterProvider(resource=resource)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("ecommerce-pipeline")

# Business metrics
leads_processed = meter.create_counter(
    "pipeline.leads_processed",
    description="Total leads processed through the pipeline",
)

lead_score_histogram = meter.create_histogram(
    "pipeline.lead_score",
    description="Distribution of lead qualification scores",
)

engagement_sent = meter.create_counter(
    "pipeline.engagements_sent",
    description="Total engagement messages sent",
)

pipeline_duration = meter.create_histogram(
    "pipeline.duration_ms",
    description="End-to-end pipeline execution time",
)

pipeline_errors = meter.create_counter(
    "pipeline.errors",
    description="Pipeline execution errors",
)


# ============================================================
# Usage example in main.py:
# ============================================================
#
# from infra.observability import tracer, trace_tool, leads_processed
#
# @trace_tool("get_customer_profile")
# def get_customer_profile(customer_id: str) -> dict:
#     ...
#
# @app.post("/process")
# async def process_lead(lead: LeadRequest):
#     with tracer.start_as_current_span("pipeline.full") as span:
#         span.set_attribute("lead.company", lead.company_name)
#         result = await run_pipeline(lead)
#         leads_processed.add(1, {"source": lead.source})
#         lead_score_histogram.record(result.score, {"qualification": result.status})
#         return result
#
# # Auto-instrument FastAPI (all HTTP requests traced)
# FastAPIInstrumentor.instrument_app(app)


# ============================================================
# What you see in Cloud Trace:
# ============================================================
#
# pipeline.full (4.2s)
# ├── agent.profiling_agent (1.8s)
# │   ├── tool.get_customer_profile (120ms)
# │   ├── tool.get_order_history (95ms)
# │   ├── tool.check_cart_abandonment (80ms)
# │   ├── tool.emarsys_get_contact (150ms)
# │   └── llm.generate (1.2s) — gemini-2.5-flash, 1200 tokens, $0.0004
# ├── agent.recommendation_agent (1.5s)
# │   ├── tool.get_product_catalog (60ms) x2
# │   ├── tool.generate_discount_code (40ms)
# │   └── llm.generate (1.1s) — gemini-2.5-flash, 900 tokens, $0.0003
# └── agent.engagement_agent (0.9s)
#     ├── tool.emarsys_trigger_automation (200ms)
#     ├── tool.emarsys_update_segment (80ms)
#     └── llm.generate (0.5s) — gemini-2.5-flash, 600 tokens, $0.0002
#
# Total: 4.2s | 3 agents | 9 tool calls | 3 LLM calls | $0.0009
