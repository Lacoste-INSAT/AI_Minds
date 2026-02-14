from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Generator
EMBEDDING_MODEL="all-MiniLM-L6-v2"

def embed_chunks(
    chunks: List[Dict],
    model_name: str = EMBEDDING_MODEL,
    batch_size: int = 32
) -> Generator[Tuple[str, Dict], None, None]:
    """
    Adds SBERT embeddings to each text chunk.

    Args:
        chunks (List[Dict]): List of chunks with 'text' field.
        model_name (str): Pretrained Sentence-BERT model name.

    Returns:
        List[Dict]: Same chunks with added 'embedding' field (as a list of floats).
    """
    model = SentenceTransformer(model_name)
    texts = [chunk["text"] for chunk in chunks]

    total = len(texts)
    embeddings = []
    for i in range(0, total, batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=True, convert_to_numpy=True)
        embeddings.extend(batch_embeddings)
        yield f"🔄 Embedding Progress: {int((i + batch_size) / total * 100)}% [{(i + batch_size)}/{total}]"

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()  # convert NumPy array to list for serialization

    yield {"done": chunks}