import os
import traceback
import sys

from mcp_server.app import mcp_server as mcp_app_instance
from mcp_server.data_loader import load_and_chunk_documents, get_all_chunks
import mcp_server.mcp_tools  # noqa: F401

if __name__ == "__main__":
    print("Loading documents...", file=sys.stderr)
    load_and_chunk_documents()
    num_chunks = len(get_all_chunks())
    print(f"Document loading complete. {num_chunks} chunks loaded.", file=sys.stderr)

    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    try:
        print(f"Starting MCP server on {transport.upper()}...", file=sys.stderr)
        mcp_app_instance.run(transport=transport)
    except KeyboardInterrupt:
        print("\nServer stopped by user.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
