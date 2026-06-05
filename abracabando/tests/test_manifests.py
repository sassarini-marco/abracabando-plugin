"""Tests that plugin.json and .mcp.json are well-formed."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_plugin_json_schema() -> None:
    data = json.loads((ROOT / "plugin.json").read_text())
    assert "name" in data
    assert re.match(r"^\d+\.\d+\.\d+$", data["version"]), "version must be semver"
    assert "license" in data
    assert "skills" in data
    assert "minServerVersion" in data


def test_mcp_json_has_both_servers() -> None:
    data = json.loads((ROOT / ".mcp.json").read_text())
    servers = data["mcpServers"]
    assert "industrial-mcp-free" in servers
    assert "industrial-mcp-pro" in servers
    free = servers["industrial-mcp-free"]
    assert free.get("type") == "streamable-http", "free server must be streamable-http"
    assert "url" in free, "free server must have a url"
    pro = servers["industrial-mcp-pro"]
    assert "headersHelper" in pro, "pro server must use headersHelper workaround"
