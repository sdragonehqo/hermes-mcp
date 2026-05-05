# Hermes MCP Doc Server

A searchable MCP server for the [Hermes Agent](https://hermes-agent.nousresearch.com) documentation. Lets Claude Code (or any MCP client) semantically search 286 pages of Hermes docs locally.

## What's Inside

```
hermes-mcp/
├── README.md                 # This file
├── setup.sh                  # One-shot setup script
├── hermes-docs-links.md      # All 113 source doc URLs
└── MCPDocSearch/             # Crawler + MCP server (cloned from alizdavoodi/MCPDocSearch)
    ├── storage/
    │   └── hermes-agent.md   # Pre-crawled docs (3 MB, 286 pages)
    └── ...
```

## Quick Start

### 1. Run setup

```bash
cd hermes-mcp
./setup.sh
```

This installs `uv` (if missing), Python dependencies, and Playwright's Chromium. If the pre-crawled `storage/hermes-agent.md` is present it skips crawling; otherwise it re-crawls everything (~5 min).

### 2. Add MCP config to Claude Code

Add to `~/.claude/settings.json` (global) or your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "hermes-docs": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/hermes-mcp/MCPDocSearch",
        "run",
        "python",
        "-m",
        "mcp_server.main"
      ]
    }
  }
}
```

Replace `/ABSOLUTE/PATH/TO/hermes-mcp/MCPDocSearch` with the actual path on your machine.

### 3. Restart Claude Code

The first query triggers embedding generation (~2-5 min depending on hardware). Results are cached after that.

## Available MCP Tools

Once running, Claude Code can use these tools:

| Tool | Description |
|---|---|
| `list_documents` | Lists all crawled doc files |
| `get_document_headings` | Shows heading structure of a doc |
| `search_documentation` | Semantic search across all Hermes docs |

## Re-crawling

To refresh the docs (e.g., after Hermes publishes updates):

```bash
cd hermes-mcp/MCPDocSearch
uv run python crawl.py \
  "https://hermes-agent.nousresearch.com/docs/getting-started/quickstart" \
  --include-pattern "*hermes-agent.nousresearch.com/docs*" \
  --max-depth 5 \
  --output ./storage/hermes-agent.md
```

Delete `storage/document_chunks_cache.pkl` afterward so the MCP server regenerates embeddings on next start.

## Requirements

- macOS or Linux
- Python 3.11-3.13 (3.14 is not yet supported by PyTorch)
- ~500 MB disk (Chromium + Python deps + model weights)

## Credits

- Crawler/server: [MCPDocSearch](https://github.com/alizdavoodi/MCPDocSearch) by alizdavoodi
- Documentation: [Hermes Agent](https://hermes-agent.nousresearch.com) by Nous Research
