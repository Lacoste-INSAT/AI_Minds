"""
Confidence Calculators - Compute confidence scores for agent outputs.
"""


def calculate_planner_confidence(subgraph_dict: dict) -> float:
    """Calculate confidence based on subgraph quality metrics."""
    if not isinstance(subgraph_dict, dict):
        return 0.3
    edges = subgraph_dict.get("edges", [])
    if not isinstance(edges, list):
        edges = []
    if not edges:
        return 0.3

    # Average edge confidence - filter to dicts only
    confidences = [e.get("strength", 0.5) for e in edges if isinstance(e, dict)]
    if not confidences:
        return 0.3
    avg_confidence = sum(confidences) / len(confidences)

    # Boost for multiple paths
    paths = subgraph_dict.get("paths", [])
    num_paths = len(paths) if isinstance(paths, list) else 0
    path_bonus = min(0.1 * num_paths, 0.2)

    # Boost for diverse node types
    nodes = subgraph_dict.get("nodes", [])
    if isinstance(nodes, list):
        node_types = set(n.get("type") for n in nodes if isinstance(n, dict))
    else:
        node_types = set()
    diversity_bonus = min(0.05 * len(node_types), 0.15)

    return min(avg_confidence + path_bonus + diversity_bonus, 0.95)


def calculate_scientist_confidence(hypothesis: dict, subgraph: dict) -> float:
    """Calculate confidence based on evidence grounding quality."""
    if not isinstance(hypothesis, dict):
        return 0.5
    if not isinstance(subgraph, dict):
        subgraph = {}
    
    base = 0.5

    # Mechanism completeness
    mechanisms = hypothesis.get("mechanisms", {})
    if isinstance(mechanisms, dict):
        steps = mechanisms.get("step_by_step", [])
        if isinstance(steps, list) and steps:
            base += 0.1
            if len(steps) >= 3:
                base += 0.05

    # Citation coverage
    citations = hypothesis.get("citations", {})
    if isinstance(citations, dict):
        nodes_used = citations.get("graph_nodes_used", [])
        if not isinstance(nodes_used, list):
            nodes_used = []
    else:
        nodes_used = []
    nodes_list = subgraph.get("nodes", [])
    total_nodes = len(nodes_list) if isinstance(nodes_list, list) else 0
    if total_nodes > 0:
        coverage = len(nodes_used) / total_nodes
        base += coverage * 0.15

    # Novelty score
    novelty = hypothesis.get("novelty", {})
    if isinstance(novelty, dict):
        try:
            raw_score = novelty.get("score", 5)
            score = float(raw_score) if raw_score is not None else 5.0
            base += (score / 10) * 0.1
        except (ValueError, TypeError):
            pass

    # Validation completeness
    val = hypothesis.get("validation", {})
    if isinstance(val, dict) and val:
        if val.get("computational"):
            base += 0.05
        if val.get("experimental"):
            base += 0.05

    return min(base, 0.95)


def calculate_critic_confidence(evaluation: dict) -> float:
    """Calculate confidence in evaluation quality."""
    if not isinstance(evaluation, dict):
        return 0.5
    
    conf = 0.5

    # Comprehensive scores
    scores = evaluation.get("scores", {})
    if isinstance(scores, dict) and scores:
        categories = ["logical_consistency", "evidence_grounding",
                      "mechanistic_plausibility", "novelty", "feasibility"]
        scored = sum(1 for c in categories if c in scores)
        conf += (scored / len(categories)) * 0.2

    # Actionable feedback
    if evaluation.get("strengths"):
        conf += 0.05
    if evaluation.get("weaknesses"):
        conf += 0.05
    if evaluation.get("required_revisions"):
        conf += 0.1
    if evaluation.get("improvement_suggestions"):
        conf += 0.05
    if evaluation.get("scientific_questions"):
        conf += 0.05

    return min(conf, 0.95)
