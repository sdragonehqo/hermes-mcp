from typing import List, Dict, Optional, Union
import numpy as np

# Import dot_score specifically, as recommended for multi-qa-mpnet-base-dot-v1
from sentence_transformers.util import dot_score

# Import the shared embedding model instance
from mcp_server.app import embedding_model
from mcp_server.data_loader import get_all_chunks  # Changed to absolute import


def search_chunks(
    query: str, filename: Optional[str] = None, max_results: int = 5
) -> List[Dict[str, Union[str, float]]]:
    """
    Performs semantic search over the loaded document chunks using embeddings.
    """
    if not query:
        return []
    all_chunks = get_all_chunks()
    if not all_chunks:
        # Consider logging this instead of printing
        # import sys
        # print("Warning: No chunks loaded for searching.", file=sys.stderr)
        return []

    # Generate embedding for the query
    try:
        query_embedding = embedding_model.encode(query)
    except Exception as e:
        # Consider logging this instead of printing
        # import sys
        # print(f"Error encoding query '{query}': {e}", file=sys.stderr)
        return []  # Cannot search if query encoding fails

    results_with_scores = []

    for idx, chunk in enumerate(all_chunks):
        # Filter by filename if provided
        if filename and chunk["filename"] != filename:
            continue

        # Check if chunk has an embedding
        chunk_embedding = chunk.get("embedding")
        if chunk_embedding is None or not isinstance(chunk_embedding, np.ndarray):
            continue  # Skip chunks without embeddings

        # Calculate dot product similarity (recommended for multi-qa-mpnet-base-dot-v1)
        try:
            # Note: dot_score doesn't guarantee a range like [-1, 1], scores can be higher/lower.
            # util.dot_score returns a tensor, get the single value
            similarity = dot_score(query_embedding, chunk_embedding)[0][0].item()
        except Exception as e:
            # Consider logging this instead of printing
            # import sys
            # print(f"Error calculating similarity for chunk {idx}: {e}", file=sys.stderr)
            similarity = -float("inf")  # Assign a very low score if calculation fails

        # Store results with scores
        results_with_scores.append(
            {
                "filename": chunk["filename"],
                "heading": chunk["heading"],
                "content": chunk["content"],  # Return original content
                "score": similarity,
                "source_url": chunk.get("source_url", ""),
            }
        )

    # Sort results by score (descending)
    results_with_scores.sort(key=lambda x: x["score"], reverse=True)

    return results_with_scores[:max_results]
