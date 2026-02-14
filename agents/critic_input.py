"""
Critic Input Preparation - Prepare input for Critic LLM prompt.
"""


def prepare_critic_input(
    hypothesis: dict,
    subgraph: dict,
    kg_metadata: dict,
    iteration: int
) -> dict:
    """Prepare comprehensive input for the Critic LLM prompt."""
    # Ensure inputs are dicts
    if not isinstance(hypothesis, dict):
        hypothesis = {}
    if not isinstance(subgraph, dict):
        subgraph = {}
    if not isinstance(kg_metadata, dict):
        kg_metadata = {}
    
    edges = subgraph.get("edges", [])
    if not isinstance(edges, list):
        edges = []
    # Filter edges to only dicts
    edges = [e for e in edges if isinstance(e, dict)]
    
    high_conf = [e for e in edges if e.get("strength", 0) >= 0.9]
    low_conf = [e for e in edges if e.get("strength", 0) < 0.5]

    title, statement = _extract_hypothesis_text(hypothesis)
    mechanism_steps = _extract_mechanism_steps(hypothesis)
    citations = hypothesis.get("citations", {})
    if not isinstance(citations, dict):
        citations = {}

    return {
        "iteration": iteration,
        "main_objective": kg_metadata.get("main_objective", ""),
        "hypothesis_title": title,
        "hypothesis_statement": statement,
        "full_hypothesis": hypothesis,
        "mechanism_steps": mechanism_steps,
        "num_mechanism_steps": len(mechanism_steps),
        "subgraph_nodes": subgraph.get("nodes", []),
        "subgraph_edges": edges,
        "nodes_cited_in_hypothesis": citations.get("graph_nodes_used", []),
        "edges_cited_in_hypothesis": citations.get("graph_edges_used", []),
        "edge_confidence_distribution": _build_confidence_dist(edges, high_conf, low_conf),
        "proposed_validation": hypothesis.get("validation", {}),
        "novelty_claims": hypothesis.get("novelty", {}),
        "comparison_claims": hypothesis.get("comparison", {})
    }


def _extract_hypothesis_text(hypothesis: dict) -> tuple[str, str]:
    """Extract title and statement from hypothesis."""
    if not isinstance(hypothesis, dict):
        return "", ""
    h = hypothesis.get("hypothesis", {})
    if isinstance(h, dict):
        return h.get("title", ""), h.get("statement", "")
    return "", ""


def _extract_mechanism_steps(hypothesis: dict) -> list:
    """Extract mechanism steps from hypothesis."""
    if not isinstance(hypothesis, dict):
        return []
    mechanisms = hypothesis.get("mechanisms", {})
    if isinstance(mechanisms, dict):
        steps = mechanisms.get("step_by_step", [])
        if isinstance(steps, list):
            return steps
    return []


def _build_confidence_dist(edges: list, high_conf: list, low_conf: list) -> dict:
    """Build edge confidence distribution summary."""
    return {
        "total_edges": len(edges),
        "high_confidence": len(high_conf),
        "low_confidence": len(low_conf),
        "high_conf_edges": [
            {"source": e.get("source"), "target": e.get("target"), "strength": e.get("strength")}
            for e in high_conf[:5] if isinstance(e, dict)
        ],
        "low_conf_edges": [
            {"source": e.get("source"), "target": e.get("target"), "strength": e.get("strength")}
            for e in low_conf[:5] if isinstance(e, dict)
        ]
    }
