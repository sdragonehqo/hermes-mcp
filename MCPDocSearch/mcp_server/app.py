import torch  # Import torch to check for GPU
import mcp.types as types
from fastmcp import FastMCP
from sentence_transformers import SentenceTransformer

# --- Determine Device ---
# Check for MPS (Apple Silicon GPU), then CUDA, then fallback to CPU
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

# --- Embedding Model ---
# Load the model once when the app starts.
# Choose a model suitable for your needs.
# 'all-MiniLM-L6-v2' is a good starting point: fast and decent quality.
# Other options: 'multi-qa-mpnet-base-dot-v1' (good for QA),
# 'all-mpnet-base-v2' (higher quality, slower)
# Use try-except to handle potential model loading issues gracefully
try:
    # Switch to a model trained for QA/Retrieval tasks
    model_name = "multi-qa-mpnet-base-dot-v1"
    # Pass the determined device to the model
    embedding_model = SentenceTransformer(model_name, device=device)
    # Log the device being used
    import sys

    print(
        f"Embedding model '{model_name}' loaded on device: {device}",
        file=sys.stderr,
    )
except Exception as e:
    # Log errors to stderr instead of stdout if needed for debugging
    import sys

    print(
        f"FATAL: Failed to load embedding model on device '{device}': {e}",
        file=sys.stderr,
    )
    # Decide how to handle this - exit? Or proceed without semantic search?
    # For now, let's raise it to stop the server from starting incorrectly.
    raise RuntimeError("Failed to load embedding model") from e


# --- MCP Server Instance ---
# Initialize FastMCP server instance in a central place
# Document loading will happen in main.py when run directly
mcp_server = FastMCP(
    name="doc-query-server",
    version="0.1.0",
    # Define server capabilities - we only offer tools here
    capabilities=types.ServerCapabilities(
        # Instantiate ToolsCapability directly (corrected name)
        tools=types.ToolsCapability(listChanged=False)
    ),
)

# Tools are imported when mcp_tools.py is loaded, which happens implicitly
# when main.py imports this module or mcp_tools directly.
# Ensure mcp_tools is imported somewhere before mcp_server.run() is called.
# We'll rely on the import in main.py or its chain.
