# ADK vs LangGraph — Comparison

## What is LangGraph?

LangGraph (by LangChain) builds agent workflows as **directed graphs with state**.
Each node is a function or agent, edges define the flow, and a shared state object
passes between nodes.

## Key Difference

| | Google ADK | LangGraph |
|---|---|---|
| **Mental model** | Agents with tools | Graph with nodes and edges |
| **Orchestration** | SequentialAgent, ParallelAgent | StateGraph with conditional edges |
| **State** | Session (InMemorySession, Firestore) | TypedDict shared state |
| **Branching** | Agent decides via LLM | Explicit conditional edges |
| **Best for** | LLM-driven decisions | Deterministic workflows with LLM steps |

## Same Pipeline in LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

# 1. Define shared state (like a message passed between agents)
class PipelineState(TypedDict):
    customer_id: str
    profile: Optional[dict]
    orders: Optional[list]
    abandoned_cart: Optional[dict]
    emarsys_data: Optional[dict]
    recommendations: Optional[list]
    discount_code: Optional[str]
    engagement_result: Optional[dict]
    score: Optional[int]

# 2. Define nodes (each node = one step)
def profile_customer(state: PipelineState) -> PipelineState:
    """Node 1: Get customer data from Magento + Emarsys."""
    state["profile"] = get_customer_profile(state["customer_id"])
    state["orders"] = get_order_history(state["customer_id"])
    state["abandoned_cart"] = check_cart_abandonment(state["customer_id"])
    state["emarsys_data"] = emarsys_get_contact(state["profile"]["email"])
    return state

def recommend_products(state: PipelineState) -> PipelineState:
    """Node 2: Generate recommendations based on profile."""
    # LLM call here to analyze and recommend
    state["recommendations"] = call_gemini_for_recommendations(state)
    if state["emarsys_data"]["rfm_segment"] == "at_risk":
        state["discount_code"] = generate_discount_code(...)
    return state

def engage_customer(state: PipelineState) -> PipelineState:
    """Node 3: Send personalized engagement."""
    state["engagement_result"] = emarsys_trigger_automation(...)
    return state

# 3. Define conditional routing (LangGraph's superpower)
def should_engage(state: PipelineState) -> str:
    """Decide next step based on score."""
    if state["score"] >= 70:
        return "engage"      # Hot lead → engage immediately
    elif state["score"] >= 40:
        return "nurture"     # Warm → add to nurture sequence
    else:
        return "skip"        # Cold → don't waste resources

# 4. Build the graph
graph = StateGraph(PipelineState)

# Add nodes
graph.add_node("profile", profile_customer)
graph.add_node("recommend", recommend_products)
graph.add_node("engage", engage_customer)
graph.add_node("nurture", add_to_nurture_sequence)

# Add edges (the flow)
graph.set_entry_point("profile")
graph.add_edge("profile", "recommend")

# Conditional edge: recommend → engage OR nurture OR end
graph.add_conditional_edges(
    "recommend",
    should_engage,
    {
        "engage": "engage",
        "nurture": "nurture",
        "skip": END,
    }
)

graph.add_edge("engage", END)
graph.add_edge("nurture", END)

# 5. Compile and run
pipeline = graph.compile()
result = pipeline.invoke({"customer_id": "12345"})
```

## When to Use Which

### Use ADK when:
- You want the **LLM to decide** what to do next (agentic behavior)
- Tight integration with GCP (Vertex AI, Cloud Run, Firestore)
- You need built-in session management
- Google is your cloud provider

### Use LangGraph when:
- You need **deterministic routing** (if score > 70 → path A, else → path B)
- Complex branching with loops (retry, human-in-the-loop)
- You want to visualize the workflow as a graph
- You're already using LangChain

### Use both together:
- LangGraph for the **workflow structure** (deterministic routing)
- ADK agents as **nodes** within the graph (LLM-driven decisions)
- This is actually what L'Oréal likely does at scale

## Interview Answer

> "I've built with both. ADK is great when the LLM should decide the flow — 
> the agent reasons about which tools to call. LangGraph is better when the 
> workflow is deterministic — you know the steps, but some steps use LLMs.
> 
> In practice, I'd use LangGraph for the overall pipeline orchestration 
> (profile → qualify → route by score → engage) and ADK agents inside nodes 
> where I need LLM reasoning (like generating personalized recommendations).
> 
> The key difference: ADK is agent-first (LLM decides), LangGraph is 
> graph-first (you decide the structure, LLM fills in the blanks)."
```
