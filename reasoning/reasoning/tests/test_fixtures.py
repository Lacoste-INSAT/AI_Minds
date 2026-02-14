"""
Real-World Test Data for Synapsis Reasoning Engine
===================================================

This module contains realistic test data fetched from Wikipedia and other sources
to validate the reasoning engine with actual knowledge content.

Data covers:
- Retrieval-Augmented Generation (RAG)
- Personal Knowledge Management (PKM)
- AI/ML concepts

Usage:
    from reasoning.reasoning.tests.test_fixtures import REAL_TEST_CHUNKS, TEST_QUESTIONS
"""

from reasoning.reasoning.cpumodel.models import ChunkEvidence

# =============================================================================
# Real-World Test Chunks (simulating ingested documents)
# =============================================================================

REAL_TEST_CHUNKS = [
    # RAG Wikipedia content
    ChunkEvidence(
        chunk_id="rag_001",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""Retrieval-augmented generation (RAG) is a technique that enables large language models (LLMs) to retrieve and incorporate new information from external data sources. With RAG, LLMs first refer to a specified set of documents, then respond to user queries. These documents supplement information from the LLM's pre-existing training data. This allows LLMs to use domain-specific and/or updated information that is not available in the training data.""",
        score_final=0.92,
    ),
    ChunkEvidence(
        chunk_id="rag_002",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""RAG improves large language models (LLMs) by incorporating information retrieval before generating responses. Unlike LLMs that rely on static training data, RAG pulls relevant text from databases, uploaded documents, or web sources. This method helps reduce AI hallucinations, which have caused chatbots to describe policies that don't exist, or recommend nonexistent legal cases to lawyers.""",
        score_final=0.89,
    ),
    ChunkEvidence(
        chunk_id="rag_003",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""Typically, the data to be referenced is converted into LLM embeddings, numerical representations in the form of a large vector space. RAG can be used on unstructured (usually text), semi-structured, or structured data (for example knowledge graphs). These embeddings are then stored in a vector database to allow for document retrieval.""",
        score_final=0.87,
    ),
    ChunkEvidence(
        chunk_id="rag_004",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""Given a user query, a document retriever is first called to select the most relevant documents that will be used to augment the query. This comparison can be done using a variety of methods. The model feeds this relevant retrieved information into the LLM via prompt engineering of the user's original query.""",
        score_final=0.85,
    ),
    ChunkEvidence(
        chunk_id="rag_005",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""Hybrid search: Sometimes vector database searches can miss key facts needed to answer a user's question. One way to mitigate this is to do a traditional text search, add those results to the text chunks linked to the retrieved vectors from the vector search, and feed the combined hybrid text into the language model for generation.""",
        score_final=0.84,
    ),
    ChunkEvidence(
        chunk_id="rag_006",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""Sparse vectors, which encode the identity of a word, are typically dictionary-length and contain mostly zeros. Dense vectors, which encode meaning, are more compact and contain fewer zeros. Various enhancements can improve the way similarities are calculated in the vector stores (databases). Hybrid vector approaches may be used to combine dense vector representations with sparse one-hot vectors.""",
        score_final=0.82,
    ),
    ChunkEvidence(
        chunk_id="rag_007",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""RAG does not prevent hallucinations in LLMs. According to Ars Technica, 'It is not a direct solution because the LLM can still hallucinate around the source material in its response.' While RAG improves accuracy, LLMs may struggle to recognize when they lack sufficient information to provide a reliable response.""",
        score_final=0.80,
    ),
    ChunkEvidence(
        chunk_id="rag_008",
        document_id="doc_wikipedia_rag",
        file_name="RAG_Wikipedia.md",
        snippet="""Chunking involves various strategies for breaking up the data into vectors so the retriever can find details in it. Fixed length with overlap is fast and easy. Overlapping consecutive chunks helps to maintain semantic context across chunks. Syntax-based chunks can break the document up into sentences. File format-based chunking respects natural document structure.""",
        score_final=0.78,
    ),
    
    # PKM Wikipedia content
    ChunkEvidence(
        chunk_id="pkm_001",
        document_id="doc_wikipedia_pkm",
        file_name="PKM_Wikipedia.md",
        snippet="""Personal knowledge management (PKM) is a process of collecting information that a person uses to gather, classify, store, search, retrieve and share knowledge in their daily activities. It is a response to the idea that knowledge workers need to be responsible for their own growth and learning. It is a bottom-up approach to knowledge management (KM).""",
        score_final=0.91,
    ),
    ChunkEvidence(
        chunk_id="pkm_002",
        document_id="doc_wikipedia_pkm",
        file_name="PKM_Wikipedia.md",
        snippet="""PKM integrates personal information management (PIM), focused on individual skills, with knowledge management (KM) in addition to input from a variety of disciplines such as cognitive psychology, management and philosophy. From an organizational perspective, understanding of the field has developed in light of expanding knowledge about human cognitive capabilities.""",
        score_final=0.88,
    ),
    ChunkEvidence(
        chunk_id="pkm_003",
        document_id="doc_wikipedia_pkm",
        file_name="PKM_Wikipedia.md",
        snippet="""Wright's PKM model involves four interrelated domains: analytical, information, social, and learning. The analytical domain involves competencies such as interpretation, envisioning, application, creation, and contextualization. The information dimension comprises the sourcing, assessment, organization, aggregation, and communication of information.""",
        score_final=0.86,
    ),
    ChunkEvidence(
        chunk_id="pkm_004",
        document_id="doc_wikipedia_pkm",
        file_name="PKM_Wikipedia.md",
        snippet="""Skills associated with personal knowledge management include: Collaboration skills (coordination, synchronization, experimentation, cooperation and design), Communication skills (perception, intuition, expression, visualization and interpretation), Creative skills (imagination, pattern recognition, appreciation, innovation, inference).""",
        score_final=0.83,
    ),
    ChunkEvidence(
        chunk_id="pkm_005",
        document_id="doc_wikipedia_pkm",
        file_name="PKM_Wikipedia.md",
        snippet="""Some examples of PKM tools include: Logseq, Notion, Obsidian, Roam, Tana, TiddlyWiki, and Zim. These tools facilitate knowledge sharing and personal content management. They use various information visualization techniques including mind maps, concept maps, and argument maps.""",
        score_final=0.81,
    ),
    
    # Made-up team meeting notes (realistic enterprise context)
    ChunkEvidence(
        chunk_id="meeting_001",
        document_id="doc_team_meeting",
        file_name="team_standup_2026-02-10.md",
        snippet="""Team standup 2026-02-10: John mentioned the Q1 deadline is March 15th for the MVP launch. Sarah confirmed the budget has been approved for $50,000. Mike raised concerns about the vector database performance under load.""",
        score_final=0.95,
    ),
    ChunkEvidence(
        chunk_id="meeting_002",
        document_id="doc_team_meeting",
        file_name="team_standup_2026-02-12.md",
        snippet="""Team standup 2026-02-12: Sarah updated that Qdrant benchmarks show 95% recall at 10ms p99 latency. John said the Ollama integration is complete. The team agreed to use qwen2.5:0.5b for CPU-only deployments.""",
        score_final=0.93,
    ),
    ChunkEvidence(
        chunk_id="meeting_003",
        document_id="doc_project_spec",
        file_name="synapsis_architecture.md",
        snippet="""Synapsis uses a 3-tier LLM fallback: T1 (phi4-mini 3.8B) for best quality, T2 (qwen2.5:3b) as backup, T3 (qwen2.5:0.5b 0.5B) for CPU-only. The system is designed to be air-gapped with no external API calls. All data stays localhost.""",
        score_final=0.90,
    ),
]


# =============================================================================
# Test Questions with Expected Characteristics
# =============================================================================

TEST_QUESTIONS = [
    # Simple factual questions
    {
        "query": "What is RAG?",
        "expected_type": "SIMPLE",
        "expected_keywords": ["retrieval", "augmented", "generation", "LLM"],
        "description": "Basic definition lookup",
    },
    {
        "query": "What is the project deadline?",
        "expected_type": "SIMPLE",
        "expected_keywords": ["March 15", "deadline", "Q1"],
        "description": "Meeting notes factual recall",
    },
    {
        "query": "What is personal knowledge management?",
        "expected_type": "SIMPLE",
        "expected_keywords": ["PKM", "knowledge", "process", "collecting"],
        "description": "PKM definition lookup",
    },
    
    # Multi-hop questions (require connecting multiple sources)
    {
        "query": "How does hybrid search relate to RAG accuracy?",
        "expected_type": "MULTI_HOP",
        "expected_keywords": ["hybrid", "vector", "text search", "accuracy"],
        "description": "Connects hybrid search + RAG limitations",
    },
    {
        "query": "What did John say about Ollama?",
        "expected_type": "MULTI_HOP",
        "expected_keywords": ["John", "Ollama", "integration", "complete"],
        "description": "Entity + topic cross-reference",
    },
    {
        "query": "What model tier should I use for CPU-only devices?",
        "expected_type": "MULTI_HOP",
        "expected_keywords": ["T3", "qwen2.5:0.5b", "CPU"],
        "description": "Architecture decision lookup",
    },
    
    # Contradiction detection questions
    {
        "query": "Does RAG completely prevent hallucinations?",
        "expected_type": "CONTRADICTION",
        "expected_keywords": ["does not prevent", "hallucinate", "not a direct solution"],
        "description": "Tests nuanced understanding",
    },
    
    # Temporal questions
    {
        "query": "What updates were discussed in the February meetings?",
        "expected_type": "TEMPORAL",
        "expected_keywords": ["February", "2026", "standup"],
        "description": "Time-scoped query",
    },
]


# =============================================================================
# BM25 Test Corpus (for sparse retrieval testing)
# =============================================================================

BM25_TEST_CORPUS = [
    {
        "chunk_id": "bm25_001",
        "content": "RAG retrieval augmented generation helps LLMs access external knowledge bases",
    },
    {
        "chunk_id": "bm25_002",
        "content": "Vector embeddings convert text into numerical representations for similarity search",
    },
    {
        "chunk_id": "bm25_003",
        "content": "The project deadline is March 15th 2026 for Q1 MVP release",
    },
    {
        "chunk_id": "bm25_004",
        "content": "Personal knowledge management PKM tools include Obsidian Notion and Roam",
    },
    {
        "chunk_id": "bm25_005",
        "content": "Hybrid search combines dense vectors with sparse BM25 for better recall",
    },
    {
        "chunk_id": "bm25_006",
        "content": "Ollama is a local LLM runtime that supports qwen phi and other models",
    },
    {
        "chunk_id": "bm25_007",
        "content": "Chunking strategies include fixed length overlap and syntax based approaches",
    },
    {
        "chunk_id": "bm25_008",
        "content": "Knowledge graphs store entity relationships for multi-hop reasoning",
    },
]


# =============================================================================
# Graph Test Data (for entity relationship testing)
# =============================================================================

GRAPH_TEST_ENTITIES = [
    ("John", "mentioned", "deadline"),
    ("John", "works_on", "Ollama integration"),
    ("Sarah", "confirmed", "budget"),
    ("Sarah", "benchmarked", "Qdrant"),
    ("Mike", "raised", "performance concerns"),
    ("RAG", "reduces", "hallucinations"),
    ("RAG", "uses", "vector embeddings"),
    ("RAG", "uses", "hybrid search"),
    ("PKM", "includes", "information management"),
    ("PKM", "requires", "collaboration skills"),
    ("Synapsis", "uses", "Ollama"),
    ("Synapsis", "uses", "Qdrant"),
    ("Synapsis", "uses", "qwen2.5"),
]


# =============================================================================
# LLM/Transformer Wikipedia Data (Real Data - fetched from Wikipedia)
# =============================================================================

LLM_TRANSFORMER_CHUNKS = [
    ChunkEvidence(
        chunk_id="llm_001",
        document_id="doc_wikipedia_llm",
        file_name="LLM_Wikipedia.md",
        snippet="""A large language model (LLM) is a language model trained with self-supervised machine learning on a vast amount of text, designed for natural language processing tasks, especially language generation. The largest and most capable LLMs are generative pre-trained transformers (GPTs) that provide the core capabilities of modern chatbots. LLMs can be fine-tuned for specific tasks or guided by prompt engineering.""",
        score_final=0.95,
    ),
    ChunkEvidence(
        chunk_id="llm_002",
        document_id="doc_wikipedia_llm",
        file_name="LLM_Wikipedia.md",
        snippet="""LLMs evolved from earlier statistical and recurrent neural network approaches to language modeling. The transformer architecture, introduced in 2017, replaced recurrence with self-attention, allowing efficient parallelization, longer context handling, and scalable training on unprecedented data volumes. This innovation enabled models like GPT, BERT, and their successors.""",
        score_final=0.91,
    ),
    ChunkEvidence(
        chunk_id="llm_003",
        document_id="doc_wikipedia_llm",
        file_name="LLM_Wikipedia.md",
        snippet="""Retrieval-augmented generation (RAG) is an approach that integrates LLMs with document retrieval systems. Given a query, a document retriever is called to retrieve the most relevant documents. This is usually done by encoding the query and the documents into vectors, then finding the documents with vectors most similar to the vector of the query. The LLM then generates an output based on both the query and context included from the retrieved documents.""",
        score_final=0.93,
    ),
    ChunkEvidence(
        chunk_id="transformer_001",
        document_id="doc_wikipedia_transformer",
        file_name="Transformer_Wikipedia.md",
        snippet="""In deep learning, the transformer is an artificial neural network architecture based on the multi-head attention mechanism, in which text is converted to numerical representations called tokens, and each token is converted into a vector via lookup from a word embedding table. At each layer, each token is then contextualized within the scope of the context window with other tokens via a parallel multi-head attention mechanism.""",
        score_final=0.94,
    ),
    ChunkEvidence(
        chunk_id="transformer_002",
        document_id="doc_wikipedia_transformer",
        file_name="Transformer_Wikipedia.md",
        snippet="""The modern version of the transformer was proposed in the 2017 paper 'Attention Is All You Need' by researchers at Google. Transformers have the advantage of having no recurrent units, therefore requiring less training time than earlier recurrent neural architectures (RNNs) such as long short-term memory (LSTM). Later variations have been widely adopted for training large language models on large datasets.""",
        score_final=0.92,
    ),
    ChunkEvidence(
        chunk_id="transformer_003",
        document_id="doc_wikipedia_transformer",
        file_name="Transformer_Wikipedia.md",
        snippet="""The attention mechanism used in the transformer architecture are scaled dot-product attention units. For each unit, the transformer model learns three weight matrices: the query weights, the key weights, and the value weights. The attention weights are calculated using the query and key vectors and passed through a softmax which normalizes the weights.""",
        score_final=0.88,
    ),
]

# Extend REAL_TEST_CHUNKS with LLM/Transformer data
REAL_TEST_CHUNKS.extend(LLM_TRANSFORMER_CHUNKS)


# =============================================================================
# Accuracy Evaluation Data
# =============================================================================

ACCURACY_TEST_CASES = [
    {
        "query": "What technique helps LLMs access external knowledge?",
        "golden_answer": "RAG (Retrieval-Augmented Generation)",
        "must_contain": ["RAG", "retrieval"],
        "must_not_contain": ["hallucinate", "error"],
    },
    {
        "query": "What is the approved budget amount?",
        "golden_answer": "$50,000",
        "must_contain": ["50,000", "$50"],
        "must_not_contain": ["unknown", "not specified"],
    },
    {
        "query": "Which PKM tools are mentioned?",
        "golden_answer": "Obsidian, Notion, Roam, Logseq, Tana, TiddlyWiki, Zim",
        "must_contain_any": ["Obsidian", "Notion", "Roam", "Logseq"],
        "must_not_contain": ["unknown"],
    },
    {
        "query": "What are the model tiers in Synapsis?",
        "golden_answer": "T1 (phi4-mini), T2 (qwen2.5:3b), T3 (qwen2.5:0.5b)",
        "must_contain_any": ["T1", "T2", "T3", "phi4", "qwen"],
        "must_not_contain": ["GPT", "Claude"],
    },
]
