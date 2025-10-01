import json
import joblib
import os
from sentence_transformers import SentenceTransformer, util
from typing import Optional, Dict, List, Tuple
import asyncio
from datetime import datetime
import logging
import torch

logger = logging.getLogger(__name__)

class FAQIndexer:
    """Singleton FAQ indexer that manages sentence-transformer search index."""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(self.project_root, "data")
            self.index_path = os.path.join(self.data_dir, "st_index.joblib")
            self.faq_path = os.path.join(self.data_dir, "faq.json")
            
            self.kb_data: Optional[List[Dict]] = None
            self.model: Optional[SentenceTransformer] = None
            self.embeddings: Optional[torch.Tensor] = None
            self.questions: Optional[List[str]] = None
            self.last_indexed: Optional[datetime] = None
            self.index_version: int = 0
            
            # Configuration
            self.min_score_threshold = 0.6  # Minimum cosine similarity score for a match
            self.top_k_results = 3  # Number of top results to consider
            self.model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            
            # Load index on initialization
            self.load_index()
    
    def load_index(self) -> bool:
        """Load the sentence-transformer index from disk."""
        try:
            if not os.path.exists(self.index_path):
                logger.warning("Sentence-transformer index not found. Creating new index...")
                return self.create_index()
            
            with open(self.index_path, "rb") as f:
                data = joblib.load(f)
                self.kb_data = data["kb"]
                self.embeddings = data["embeddings"]
                self.questions = data.get("questions", [entry["question"] for entry in self.kb_data])
                self.last_indexed = data.get("last_indexed", datetime.now())
                self.index_version = data.get("version", 1)
            
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Index loaded successfully. Version: {self.index_version}, "
                       f"Documents: {len(self.kb_data)}, "
                       f"Last indexed: {self.last_indexed}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def create_index(self) -> bool:
        """Create a new sentence-transformer index from the FAQ data."""
        try:
            if not os.path.exists(self.faq_path):
                logger.error(f"FAQ file not found at {self.faq_path}")
                return False
            
            with open(self.faq_path, "r", encoding="utf-8") as f:
                self.kb_data = json.load(f)
            
            self.questions = [entry["question"] for entry in self.kb_data]
            
            documents = []
            for entry in self.kb_data:
                doc_text = f"{entry['question']} {entry.get('keywords', '')} {entry['answer'][:200]}"
                documents.append(doc_text)
            
            self.model = SentenceTransformer(self.model_name)
            self.embeddings = self.model.encode(documents, convert_to_tensor=True)
            
            self.last_indexed = datetime.now()
            self.index_version += 1
            
            index_data = {
                "kb": self.kb_data,
                "embeddings": self.embeddings,
                "questions": self.questions,
                "last_indexed": self.last_indexed,
                "version": self.index_version
            }
            
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.index_path, "wb") as f:
                joblib.dump(index_data, f)
            
            logger.info(f"Index created successfully. Version: {self.index_version}, "
                       f"Documents: {len(self.kb_data)}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    async def search(self, query: str, threshold: Optional[float] = None, top_k: Optional[int] = None) -> List[Dict]:
        """
        Search the FAQ index for matching questions.
        
        Returns a list of results with scores, sorted by relevance.
        """
        if self.model is None or self.embeddings is None or not self.kb_data:
            logger.error("Index not loaded. Cannot perform search.")
            return []

        # Exact match check
        for i, question in enumerate(self.questions):
            if query.lower() == question.lower():
                return [{
                    "question": self.kb_data[i]["question"],
                    "answer": self.kb_data[i]["answer"],
                    "score": 1.0, # High score for exact match
                    "confidence": "high"
                }]

        try:
            min_score = threshold or self.min_score_threshold
            k = top_k or self.top_k_results
            
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            
            cos_scores = util.cos_sim(query_embedding, self.embeddings)[0]
            
            top_results = torch.topk(cos_scores, k=k)
            
            results = []
            for score, idx in zip(top_results[0], top_results[1]):
                if score >= min_score:
                    results.append({
                        "question": self.kb_data[idx]["question"],
                        "answer": self.kb_data[idx]["answer"],
                        "score": float(score),
                        "confidence": self._calculate_confidence(score)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def _calculate_confidence(self, score: float) -> str:
        """Calculate confidence level based on cosine similarity score."""
        if score > 0.8:
            return "high"
        elif score > 0.6:
            return "medium"
        else:
            return "low"
    
    async def get_best_answer(self, query: str) -> Optional[Tuple[str, float]]:
        """Get the best matching answer for a query."""
        results = await self.search(query)
        if results:
            best = results[0]
            return best["answer"], best["score"]
        return None, 0.0
    
    def get_stats(self) -> Dict:
        """Get indexer statistics."""
        return {
            "documents": len(self.kb_data) if self.kb_data else 0,
            "last_indexed": self.last_indexed.isoformat() if self.last_indexed else None,
            "version": self.index_version,
            "index_loaded": self.embeddings is not None
        }
