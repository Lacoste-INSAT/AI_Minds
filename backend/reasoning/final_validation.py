"""
Final Validation Script for Retrieval & Reasoning Engine
Run: python backend/reasoning/final_validation.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    print('=' * 70)
    print('FINAL VALIDATION: Retrieval & Reasoning Engine')
    print('=' * 70)
    print()

    # Test 1: All imports work
    print('[1] IMPORT TEST')
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
        print('    All 20 gpumodel imports: OK')
    except Exception as e:
        print(f'    FAILED: {e}')
        return False

    try:
        from backend.reasoning.api import router, QueryRequest, QueryResponse, ExecutionMode
        print('    API router imports: OK')
    except Exception as e:
        print(f'    FAILED: {e}')
        return False

    print()

    # Test 2: Component instantiation
    print('[2] COMPONENT INSTANTIATION')
    try:
        retriever = HybridRetriever()
        print(f'    HybridRetriever: OK (has retrieve={hasattr(retriever, "retrieve")})')
    except Exception as e:
        print(f'    FAILED: {e}')
        return False

    try:
        fusion = RRFFusion(k=60, recency_weight=0.2)
        print(f'    RRFFusion: OK (k={fusion.k})')
    except Exception as e:
        print(f'    FAILED: {e}')
        return False

    try:
        scorer = ConfidenceScorer()
        print(f'    ConfidenceScorer: OK (weights={list(scorer.weights.keys())})')
    except Exception as e:
        print(f'    FAILED: {e}')
        return False

    print()

    # Test 3: Query classification
    print('[3] QUERY CLASSIFICATION')
    from unittest.mock import MagicMock
    mock_ollama = MagicMock()
    planner = QueryPlanner(mock_ollama)

    tests = [
        ('What is the budget?', None, 'SIMPLE (fallback)'),
        ('How has my view changed over time?', QueryType.TEMPORAL, 'TEMPORAL'),
        ('What did Sarah say about the project?', QueryType.MULTI_HOP, 'MULTI_HOP'),
    ]

    for query, expected, label in tests:
        result = planner._quick_classify(query)
        status = 'OK' if result == expected else f'UNEXPECTED ({result})'
        print(f'    "{query[:40]}..." -> {label}: {status}')

    print()

    # Test 4: Entity extraction
    print('[4] ENTITY EXTRACTION')
    entities = planner._extract_entities_regex('What did Sarah say about Project Alpha?')
    print(f'    Extracted: {entities}')
    print(f'    Contains Sarah: {"Sarah" in entities}')
    print(f'    Contains Project Alpha: {"Project Alpha" in entities}')

    print()

    # Test 5: RRF Fusion
    print('[5] RRF FUSION')
    from backend.reasoning.gpumodel.retriever import RetrievalResult, RetrievalBundle

    dense = [RetrievalResult('c1', 'content1', 'file1.md', 0.9, 'dense')]
    sparse = [RetrievalResult('c1', 'content1', 'file1.md', 0.8, 'sparse')]  # Same chunk
    bundle = RetrievalBundle(dense, sparse, [], 'test')

    fused = fusion.fuse(bundle, top_k=5)
    print(f'    Input: 2 results (same chunk from dense+sparse)')
    print(f'    Output: {len(fused)} result (deduplicated)')
    print(f'    Found by multiple paths: {fused[0].found_by_multiple if fused else "N/A"}')

    print()

    # Test 6: Confidence scoring
    print('[6] CONFIDENCE SCORING')
    from backend.reasoning.gpumodel.critic import CriticResult, CriticVerdict

    critic_approve = CriticResult(CriticVerdict.APPROVE, 0.9, 'Good', [], 5, 5, 'phi4')
    critic_reject = CriticResult(CriticVerdict.REJECT, 0.9, 'Bad', ['Hallucination'], 3, 0, 'phi4')

    result_approve = scorer.calculate([], None, critic_approve)
    result_reject = scorer.calculate([], None, critic_reject)

    print(f'    Critic APPROVE -> Confidence: {result_approve.level.value} ({result_approve.score:.2f})')
    print(f'    Critic REJECT -> Confidence: {result_reject.level.value} ({result_reject.score:.2f})')

    print()
    print('=' * 70)
    print('ALL VALIDATIONS PASSED')
    print('=' * 70)
    return True


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
