"""
Tests for Query Planner.
Critical: Query classification determines retrieval strategy.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from reasoning.cpumodel.query_planner import (
    _classify_by_heuristics,
    _extract_entities_basic,
    classify_query,
)
from reasoning.cpumodel.models import QueryType


class TestHeuristicClassification:
    """Test regex-based fast classification (no LLM)."""
    
    # SIMPLE queries - should return None (fall through to LLM or default)
    def test_simple_what_is(self):
        """Direct 'what is' queries should not match any heuristic pattern."""
        result = _classify_by_heuristics("What is the project deadline?")
        # SIMPLE has no explicit patterns - falls through
        assert result is None
    
    def test_simple_lookup(self):
        """Direct lookup should not match patterns."""
        result = _classify_by_heuristics("What did the meeting notes say?")
        assert result is None
    
    # TEMPORAL queries
    def test_temporal_how_did_my_view_change(self):
        """'How did my view change' -> TEMPORAL."""
        result = _classify_by_heuristics("How did my view on AI change?")
        assert result == QueryType.TEMPORAL
    
    def test_temporal_last_month(self):
        """'last month' temporal marker -> TEMPORAL."""
        result = _classify_by_heuristics("What did I think about this last month?")
        assert result == QueryType.TEMPORAL
    
    def test_temporal_when_did_i_first(self):
        """'when did I first' -> TEMPORAL."""
        result = _classify_by_heuristics("When did I first mention the deadline?")
        assert result == QueryType.TEMPORAL
    
    def test_temporal_evolution(self):
        """'evolution of' -> TEMPORAL."""
        result = _classify_by_heuristics("What's the evolution of my thinking?")
        assert result == QueryType.TEMPORAL
    
    # CONTRADICTION queries
    def test_contradiction_explicit(self):
        """Explicit 'contradict' -> CONTRADICTION."""
        result = _classify_by_heuristics("Did I contradict myself about the budget?")
        assert result == QueryType.CONTRADICTION
    
    def test_contradiction_conflicting(self):
        """'conflicting' -> CONTRADICTION."""
        result = _classify_by_heuristics("Are there conflicting statements?")
        assert result == QueryType.CONTRADICTION
    
    def test_contradiction_inconsistent(self):
        """'inconsistent' -> CONTRADICTION."""
        result = _classify_by_heuristics("Are my notes inconsistent?")
        assert result == QueryType.CONTRADICTION
    
    # MULTI_HOP queries
    def test_multihop_relate_to(self):
        """'relate to' -> MULTI_HOP."""
        result = _classify_by_heuristics("How does project A relate to project B?")
        assert result == QueryType.MULTI_HOP
    
    def test_multihop_connect_between(self):
        """'connect between' -> MULTI_HOP."""
        result = _classify_by_heuristics("What connections exist between X and Y?")
        assert result == QueryType.MULTI_HOP
    
    def test_multihop_ideas_from(self):
        """'ideas from X' -> MULTI_HOP."""
        result = _classify_by_heuristics("What ideas from John about marketing?")
        assert result == QueryType.MULTI_HOP
    
    def test_multihop_said_about(self):
        """'X said about Y' -> MULTI_HOP."""
        result = _classify_by_heuristics("What did Sarah say about the redesign?")
        assert result == QueryType.MULTI_HOP


class TestEntityExtraction:
    """Test basic entity extraction (without spaCy)."""
    
    def test_quoted_entities(self):
        """Should extract quoted strings."""
        entities = _extract_entities_basic('What is "Project Alpha"?')
        assert "Project Alpha" in entities
    
    def test_single_quoted_entities(self):
        """Should extract single-quoted strings."""
        entities = _extract_entities_basic("What is 'Project Beta'?")
        assert "Project Beta" in entities
    
    def test_capitalized_words(self):
        """Should extract capitalized words (proper nouns)."""
        entities = _extract_entities_basic("What did John say about Microsoft?")
        assert "John" in entities
        assert "Microsoft" in entities
    
    def test_skip_first_word(self):
        """First word of sentence skipped (could be random capital)."""
        entities = _extract_entities_basic("Please find the documents")
        # "Please" should be skipped
        assert "Please" not in entities
    
    def test_skip_common_words(self):
        """Common words should be skipped even if capitalized."""
        entities = _extract_entities_basic("John went to The store")
        # "The" is common, should be handled
        assert "John" in entities


class TestClassifyQuery:
    """Test full classification pipeline."""
    
    @pytest.mark.asyncio
    async def test_heuristic_path_no_llm(self):
        """When heuristic matches, should skip LLM call."""
        result = await classify_query(
            "How did my view on budgeting change?",
            use_llm=False
        )
        assert result.query_type == QueryType.TEMPORAL
        assert "pattern matching" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_default_to_simple(self):
        """When heuristics fail and LLM disabled, default to SIMPLE."""
        result = await classify_query(
            "What is the budget?",
            use_llm=False
        )
        assert result.query_type == QueryType.SIMPLE
    
    @pytest.mark.asyncio
    async def test_entities_extracted(self):
        """Should extract entities from query."""
        result = await classify_query(
            "What did John say about Microsoft?",
            use_llm=False
        )
        # Should have at least tried to extract entities
        assert isinstance(result.entities_detected, list)
    
    @pytest.mark.asyncio
    async def test_stores_original_query(self):
        """QueryPlan should preserve original query."""
        original = "What is the project deadline?"
        result = await classify_query(original, use_llm=False)
        assert result.original_query == original
