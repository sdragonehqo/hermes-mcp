#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_DIR="$SCRIPT_DIR/MCPDocSearch"

echo "=== Hermes MCP Doc Server Setup ==="
echo ""

# 1. Check for uv
if ! command -v uv &>/dev/null; then
  echo "[1/4] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "[1/4] uv already installed."
fi

# 2. Install Python dependencies
echo "[2/4] Installing Python dependencies..."
cd "$MCP_DIR"
uv sync --python 3.13

# 3. Install Playwright browser
echo "[3/4] Installing Playwright Chromium..."
uv run playwright install chromium

# 4. Verify storage exists
if [ -f "$MCP_DIR/storage/hermes-agent.md" ]; then
  echo "[4/4] Pre-crawled docs found (storage/hermes-agent.md)."
else
  echo "[4/4] No pre-crawled docs found. Running crawler..."
  uv run python crawl.py \
    "https://hermes-agent.nousresearch.com/docs/getting-started/quickstart" \
    --include-pattern "*hermes-agent.nousresearch.com/docs*" \
    --max-depth 5 \
    --output ./storage/hermes-agent.md
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Add this to your Claude Code MCP config:"
echo ""
echo "  ~/.claude/settings.json  (or project .claude/settings.json)"
echo ""
cat <<JSONEOF
{
  "mcpServers": {
    "hermes-docs": {
      "command": "uv",
      "args": [
        "--directory",
        "$MCP_DIR",
        "run",
        "python",
        "-m",
        "mcp_server.main"
      ]
    }
  }
}
JSONEOF
echo ""
echo "Then restart Claude Code. The first query will take a few minutes"
echo "while embeddings are generated (cached after that)."
