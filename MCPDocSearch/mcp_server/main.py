import traceback
import sys  # Import sys for stderr usage

# Import the shared FastMCP instance
from mcp_server.app import mcp_server as mcp_app_instance

# Import the data loading function and chunk access function
from mcp_server.data_loader import load_and_chunk_documents, get_all_chunks

# Import the tools module to ensure decorators run and register tools
import mcp_server.mcp_tools  # noqa: F401

# --- Main Execution (for direct run `python -m mcp_server.main`) ---
if __name__ == "__main__":
    # Load documents synchronously before starting the server
    print("Loading documents...", file=sys.stderr)
    load_and_chunk_documents()
    # Print status after loading
    num_chunks = len(get_all_chunks())
    print(f"Document loading complete. {num_chunks} chunks loaded.", file=sys.stderr)

    try:
        print("Starting MCP server on STDIO...", file=sys.stderr)
        # Call run directly on the imported instance
        mcp_app_instance.run(transport="stdio")
    except KeyboardInterrupt:
        print("\nServer stopped by user.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        # Print the full traceback to see the sub-exception details
        traceback.print_exc()  # Prints to stderr by default
