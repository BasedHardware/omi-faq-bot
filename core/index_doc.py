import os
import json
import joblib
import torch
from datetime import datetime
from sentence_transformers import SentenceTransformer


DATA_FILE = "data/clean_docs.json"
INDEX_FILE = "data/mdx_index.joblib"
META_FILE = "data/mdx_meta.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"


def index_docs(
    data_file: str = DATA_FILE,
    index_file: str = INDEX_FILE,
    meta_file: str = META_FILE,
    model_name: str = MODEL_NAME,
    verbose: bool = True
):
    """
    Build and save vector embeddings for cleaned OMI docs.
    Produces both .joblib index and .json metadata.
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"{data_file} not found. Run doc cleaner first.")

    if verbose:
        print(f"📚 Loading {data_file}...")

    with open(data_file, "r", encoding="utf-8") as f:
        docs = json.load(f)

    if len(docs) == 0:
        raise ValueError("clean_docs.json is empty")

    texts = [d["clean_text"] for d in docs]
    filenames = [d["filename"] for d in docs]

    if verbose:
        print(f"🧠 Loading model {model_name}...")

    model = SentenceTransformer(model_name)

    if verbose:
        print(f"🔢 Encoding {len(texts)} documents...")

    embeddings = model.encode(texts, convert_to_tensor=True, show_progress_bar=verbose)
    embeddings = embeddings.cpu()

    meta = {
        "filenames": filenames,
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "embedding_shape": list(embeddings.shape),
    }

    os.makedirs(os.path.dirname(index_file) or ".", exist_ok=True)
    joblib.dump({"embeddings": embeddings, "meta": meta, "docs": docs}, index_file)

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    if verbose:
        print(f"\n✅ Indexed {len(texts)} docs → {index_file}")
        print(f"🧾 Metadata → {meta_file}")
        print(f"Embedding shape: {embeddings.shape}")

        print("\n🔍 Verifying saved index...")
        data = joblib.load(index_file)
        e = data["embeddings"]
        print(f"Reloaded embeddings shape: {e.shape}, dtype: {type(e)}")
        print(f"First filename: {data['docs'][0]['filename']}")


if __name__ == "__main__":
    index_docs()
