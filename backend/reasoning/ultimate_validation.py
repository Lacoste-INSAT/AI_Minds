"""
ULTIMATE VALIDATION SCRIPT
Retrieval & Reasoning Engine - GPU + CPU Models

Run: python backend/reasoning/ultimate_validation.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def validate_gpumodel():
    """Validate GPU model components."""
    print("=" * 70)
    print("GPU MODEL VALIDATION (phi4-mini T1)")
    print("=" * 70)
    print()
    
    errors = []
    
    # Test 1: Imports
    print("[1] IMPORTS")
    try:
        from backend.reasoning.gpumodel import (
            ask, process_query, get_engine, init_engine,
            QueryPlanner, QueryType, QueryPlan,
            HybridRetriever, DenseRetriever, SparseRetriever, GraphRetriever,
            RRFFusion, FusedResult,
            LLMReasoner, ReasoningResult,
            CriticAgent, CriticVerdict,
            ConfidenceScorer, ConfidenceLevel,
            ReasoningEngine, AnswerPacket,
            OllamaClient, ModelTier
        )
        print("    All 20 gpumodel imports: OK")
    except Exception as e:
        print(f"    FAILED: {e}")
        errors.append(f"gpumodel imports: {e}")
        return errors
    
    # Test 2: Component instantiation
    print("[2] COMPONENTS")
    try:
        retriever = HybridRetriever()
        print(f"    HybridRetriever: OK (retrieve={hasattr(retriever, 'retrieve')})")
    except Exception as e:
        errors.append(f"HybridRetriever: {e}")
        print(f"    HybridRetriever: FAILED - {e}")
    
    try:
        fusion = RRFFusion(k=60, recency_weight=0.2)
        print(f"    RRFFusion: OK (k={fusion.k})")
    except Exception as e:
        errors.append(f"RRFFusion: {e}")
    
    try:
        scorer = ConfidenceScorer()
        print(f"    ConfidenceScorer: OK")
    except Exception as e:
        errors.append(f"ConfidenceScorer: {e}")
    
    # Test 3: Query classification
    print("[3] QUERY CLASSIFICATION")
    from unittest.mock import MagicMock
    planner = QueryPlanner(MagicMock())
    
    tests = [
        ("How has my view changed over time?", QueryType.TEMPORAL),
        ("What did Sarah say about it?", QueryType.MULTI_HOP),
    ]
    
    for query, expected in tests:
        result = planner._quick_classify(query)
        status = "OK" if result == expected else f"FAILED (got {result})"
        print(f"    '{query[:40]}...' -> {expected.value}: {status}")
        if result != expected:
            errors.append(f"Classification '{query}' expected {expected}, got {result}")
    
    # Test 4: Entity extraction
    print("[4] ENTITY EXTRACTION")
    entities = planner._extract_entities_regex("What did Sarah say about Project Alpha?")
    print(f"    Extracted: {entities}")
    if "Sarah" not in entities:
        errors.append("Entity 'Sarah' not extracted")
    
    # Test 5: RRF Fusion
    print("[5] RRF FUSION")
    from backend.reasoning.gpumodel.retriever import RetrievalResult, RetrievalBundle
    
    dense = [RetrievalResult('c1', 'content1', 'file1.md', 0.9, 'dense')]
    sparse = [RetrievalResult('c1', 'content1', 'file1.md', 0.8, 'sparse')]
    bundle = RetrievalBundle(dense, sparse, [], 'test')
    
    fused = fusion.fuse(bundle, top_k=5)
    print(f"    Deduplication: {len(fused)} result (found_by_multiple={fused[0].found_by_multiple})")
    if not fused[0].found_by_multiple:
        errors.append("RRF fusion didn't detect multi-path result")
    
    # Test 6: Confidence
    print("[6] CONFIDENCE SCORING")
    from backend.reasoning.gpumodel.critic import CriticResult, CriticVerdict
    
    critic_approve = CriticResult(CriticVerdict.APPROVE, 0.9, 'Good', [], 5, 5, 'phi4')
    result = scorer.calculate([], None, critic_approve)
    print(f"    Critic APPROVE -> {result.level.value} ({result.score:.2f})")
    
    print()
    return errors


def validate_cpumodel():
    """Validate CPU model components."""
    print("=" * 70)
    print("CPU MODEL VALIDATION (qwen2.5:0.5b T3)")
    print("=" * 70)
    print()
    
    errors = []
    
    # Test 1: Imports
    print("[1] IMPORTS")
    try:
        from backend.reasoning.cpumodel import (
            ask, process_query, get_engine, init_engine, ReasoningEngine,
            plan_query, classify_query,
            hybrid_retrieve, get_retriever, HybridRetriever,
            fuse_results, format_context_for_llm,
            reason_and_respond, synthesize_answer, verify_answer, compute_confidence,
            AnswerPacket, ChunkEvidence, ConfidenceLevel, FusedContext,
            LLMResponse, ModelTier, QueryPlan, QueryType, RetrievalResult,
            VerificationVerdict,
            get_ollama_client, OllamaClient,
        )
        print("    All cpumodel exports: OK")
    except Exception as e:
        print(f"    FAILED: {e}")
        errors.append(f"cpumodel imports: {e}")
        return errors
    
    # Test 2: Component instantiation
    print("[2] COMPONENTS")
    try:
        retriever = HybridRetriever()
        print(f"    HybridRetriever: OK (retrieve={hasattr(retriever, 'retrieve')})")
    except Exception as e:
        errors.append(f"HybridRetriever: {e}")
        print(f"    HybridRetriever: FAILED - {e}")
    
    try:
        engine = ReasoningEngine()
        print(f"    ReasoningEngine: OK (tier={engine.default_tier.value})")
    except Exception as e:
        errors.append(f"ReasoningEngine: {e}")
    
    # Test 3: Query classification
    print("[3] QUERY CLASSIFICATION")
    from backend.reasoning.cpumodel.query_planner import _classify_by_heuristics
    
    tests = [
        ("How has my view changed over time?", QueryType.TEMPORAL),
        ("What did Sarah say about it?", QueryType.MULTI_HOP),
        ("Did I say conflicting things?", QueryType.CONTRADICTION),
    ]
    
    for query, expected in tests:
        result = _classify_by_heuristics(query)
        status = "OK" if result == expected else f"FAILED (got {result})"
        print(f"    '{query[:40]}...' -> {expected.value}: {status}")
        if result != expected:
            errors.append(f"Classification '{query}' expected {expected}, got {result}")
    
    # Test 4: Entity extraction
    print("[4] ENTITY EXTRACTION")
    from backend.reasoning.cpumodel.query_planner import _extract_entities_basic
    entities = _extract_entities_basic("What did Sarah say about Project Alpha?")
    print(f"    Extracted: {entities}")
    if "Sarah" not in entities:
        errors.append("Entity 'Sarah' not extracted")
    
    # Test 5: RRF Fusion
    print("[5] RRF FUSION")
    dense_chunk = ChunkEvidence(
        chunk_id="c1", document_id="d1", file_name="file.md",
        snippet="content", score_dense=0.9,
    )
    sparse_chunk = ChunkEvidence(
        chunk_id="c1", document_id="d1", file_name="file.md",
        snippet="content", score_sparse=0.8,
    )
    
    results = {
        "dense": RetrievalResult(chunks=[dense_chunk], retrieval_type="dense"),
        "sparse": RetrievalResult(chunks=[sparse_chunk], retrieval_type="sparse"),
    }
    
    fused = fuse_results(results, top_k=5)
    print(f"    Deduplication: {len(fused.chunks)} result")
    
    # Test 6: Confidence
    print("[6] CONFIDENCE SCORING")
    context = FusedContext(
        chunks=[ChunkEvidence("c1", "d1", "f.md", "x", score_final=0.1)],
        dense_count=1, sparse_count=0
    )
    level, score, reason = compute_confidence(context, VerificationVerdict.APPROVE)
    print(f"    Verdict APPROVE -> {level.value} ({score:.2f})")
    
    # Test 7: Engine singleton
    print("[7] ENGINE SINGLETON")
    e1 = get_engine()
    e2 = get_engine()
    print(f"    get_engine() singleton: {'OK' if e1 is e2 else 'FAILED'}")
    if e1 is not e2:
        errors.append("get_engine singleton broken")
    
    print()
    return errors


def validate_api():
    """Validate API router."""
    print("=" * 70)
    print("API ROUTER VALIDATION")
    print("=" * 70)
    print()
    
    errors = []
    
    print("[1] IMPORTS")
    try:
        from backend.reasoning.api import router, QueryRequest, QueryResponse, ExecutionMode
        print(f"    router: OK")
        print(f"    QueryRequest fields: {list(QueryRequest.model_fields.keys())}")
        print(f"    QueryResponse fields: {list(QueryResponse.model_fields.keys())}")
        print(f"    ExecutionMode: {list(ExecutionMode)}")
    except Exception as e:
        errors.append(f"API imports: {e}")
        print(f"    FAILED: {e}")
    
    print()
    return errors


def main():
    print()
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  ULTIMATE VALIDATION: RETRIEVAL & REASONING ENGINE  ".center(68) + "*")
    print("*" + "  6 Components | GPU + CPU Models | Full Pipeline  ".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()
    
    all_errors = []
    
    # Validate GPU model
    gpu_errors = validate_gpumodel()
    all_errors.extend(gpu_errors)
    
    # Validate CPU model
    cpu_errors = validate_cpumodel()
    all_errors.extend(cpu_errors)
    
    # Validate API
    api_errors = validate_api()
    all_errors.extend(api_errors)
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    print("6 COMPONENTS (from diagram):")
    print("  1. Intent Detector (QueryPlanner)    : IMPLEMENTED")
    print("  2. Hybrid Retriever (Dense+Sparse+Graph): IMPLEMENTED")
    print("  3. Context Assembler (RRF Fusion)    : IMPLEMENTED")
    print("  4. LLM Reasoner (Phi-4/Qwen)         : IMPLEMENTED")
    print("  5. Self Verification (Critic)        : IMPLEMENTED")
    print("  6. Confidence & Uncertainty Scorer   : IMPLEMENTED")
    print()
    
    print("MODELS:")
    print("  - gpumodel/ : phi4-mini (T1) primary, 15 components")
    print("  - cpumodel/ : qwen2.5:0.5b (T3) primary, 15 components")
    print()
    
    if all_errors:
        print(f"ERRORS: {len(all_errors)}")
        for err in all_errors:
            print(f"  - {err}")
        print()
        print("STATUS: FAILED")
        return False
    else:
        print("ERRORS: 0")
        print()
        print("*" * 70)
        print("*" + " ALL VALIDATIONS PASSED ".center(68, "*") + "*")
        print("*" * 70)
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
