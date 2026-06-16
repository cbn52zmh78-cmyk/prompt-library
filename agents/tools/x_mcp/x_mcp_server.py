#!/usr/bin/env python3
"""X MCP server stub — auth check delegates to Grok Projects x_publisher."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

X_PUBLISHER = Path.home() / "Videos" / "Grok Projects" / "tools" / "x_publisher.py"


def cmd_auth() -> int:
    print("X MCP Server — credential check")
    print("=" * 50)
    if not X_PUBLISHER.exists():
        print(f"Error: x_publisher.py not found at {X_PUBLISHER}")
        return 1
    result = subprocess.run(
        [sys.executable, str(X_PUBLISHER), "verify"],
        check=False,
    )
    if result.returncode == 0:
        print("\nAuth OK — MCP server can use X API credentials from Grok Projects/.env")
    else:
        print("\nAuth failed — fill OAuth tokens in ~/Videos/Grok Projects/.env then re-run:")
        print(f"  python {Path(__file__).resolve()} --auth")
    return result.returncode


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: x_mcp_server.py --auth")
        return 1
    if sys.argv[1] == "--auth":
        return cmd_auth()
    print(f"Unknown option: {sys.argv[1]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())