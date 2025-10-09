import joblib
import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

INDEX_FILE = "data/mdx_index.joblib"
MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"


class DocSearcher:
    """Handles loading and querying the document search index."""

    def __init__(self, index_file: str = INDEX_FILE):
        self.index_file = index_file
        self.docs = []
        self.embeddings = None
        self.meta = {}
        self.model = None
        self.load()

    def load(self):
        """Load the index and sentence transformer model."""
        if not os.path.exists(self.index_file):
            logger.warning(
                f"Index file not found at {self.index_file}. Search will be disabled."
            )
            return

        logger.info("🔃 Loading document index...")
        data = joblib.load(self.index_file)
        self.docs = data["docs"]
        self.embeddings = data["embeddings"].cpu()
        self.meta = data["meta"]

        model_name = self.meta.get("model", MODEL_NAME)
        logger.info(f"🧠 Loading sentence transformer model '{model_name}'...")
        self.model = SentenceTransformer(model_name, device="cpu")
        logger.info("✅ Document searcher loaded.")

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the indexed documents.
        """
        if self.model is None or self.embeddings is None:
            return []

        query_emb = self.model.encode(query, convert_to_tensor=True, device="cpu")
        cos_scores = util.cos_sim(query_emb, self.embeddings)[0]

        top_results = torch.topk(cos_scores, k=min(top_k, len(self.docs)))

        results = []
        for score, idx in zip(top_results[0], top_results[1]):
            s = float(score)
            if s < threshold:
                continue
            results.append(
                {
                    "filename": self.docs[idx]["filename"],
                    "score": s,
                    "text": self.docs[idx]["clean_text"],
                }
            )

        return results

    def reload(self):
        """Reloads the index from disk."""
        logger.info("🔄 Reloading document index...")
        self.load()
