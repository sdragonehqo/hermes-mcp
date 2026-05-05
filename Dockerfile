FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install CPU-only PyTorch (saves ~1.5GB vs full CUDA build)
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu

# Install server dependencies (no crawl4ai/playwright needed for serving)
RUN uv pip install --system \
    "sentence-transformers>=3.0.1" \
    "fastmcp>=2.0.0"

# Copy server code and pre-crawled documentation
COPY MCPDocSearch/mcp_server/ ./mcp_server/
COPY MCPDocSearch/storage/ ./storage/

# Pre-download embedding model + generate chunk/embedding cache during build
# Container starts instantly with no first-run delay
RUN python -c "from mcp_server.data_loader import load_and_chunk_documents; load_and_chunk_documents()"

ENV MCP_TRANSPORT=sse
EXPOSE 8000

# Railway sets PORT at runtime; map it to FastMCP's setting
CMD ["sh", "-c", "FASTMCP_SERVER_HOST=0.0.0.0 FASTMCP_SERVER_PORT=${PORT:-8000} python -m mcp_server.main"]
