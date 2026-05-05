import pickle
from pathlib import Path

# Directory where the crawled markdown files are stored
STORAGE_DIR = Path("./storage")

# Path for caching the processed chunks and embeddings
# Store it alongside the storage dir for simplicity
CACHE_FILE_PATH = STORAGE_DIR / "document_chunks_cache.pkl"
