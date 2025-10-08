import joblib
import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any

INDEX_FILE = "data/mdx_index.joblib"
MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"


def load_index(index_file: str = INDEX_FILE):
    """Load the stored document index and metadata."""
    data = joblib.load(index_file)
    embeddings = data["embeddings"].cpu()  # ensure CPU tensor
    docs = data["docs"]
    meta = data["meta"]
    return docs, embeddings, meta


def query_docs(
    query: str,
    top_k: int = 5,
    threshold: float = 0.3,
    index_file: str = INDEX_FILE,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search on the indexed documents.

    Args:
        query (str): User query to search for.
        top_k (int): Number of top matches to return.
        threshold (float): Minimum cosine similarity to include.
        index_file (str): Path to the joblib index file.

    Returns:
        List[Dict]: List of {filename, score, text} for top results.
    """
    docs, embeddings, meta = load_index(index_file)

    model_name = meta.get("model", MODEL_NAME)
    model = SentenceTransformer(model_name, device="cpu")

    query_emb = model.encode(query, convert_to_tensor=True, device="cpu")
    cos_scores = util.cos_sim(query_emb, embeddings)[0]

    top_results = torch.topk(cos_scores, k=top_k)

    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        s = float(score)
        if s < threshold:
            continue
        results.append({
            "filename": docs[idx]["filename"],
            "score": s,
            "text": docs[idx]["clean_text"],
        })

    return results
