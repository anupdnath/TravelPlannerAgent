"""Load mcp_client.json and open a FastMCP client for one server."""

import json
import os
import re
from typing import Any
from urllib.parse import urlparse

from fastmcp import Client
from fastmcp.exceptions import FastMCPError
from loguru import logger
from mcp.shared.exceptions import MCPError

from app.config import MCP_CONFIG_PATH, MCP_TIMEOUT_SECONDS, ROOT

PLACEHOLDER = re.compile(r"\$\{(\w+)\}")
MCP_FAILURES = (
    MCPError,
    FastMCPError,
    OSError,
    RuntimeError,
    ValueError,
    IndexError,
    KeyError,
    AttributeError,
    TypeError,
    ExceptionGroup,
)


class MissingSecretError(RuntimeError):
    """mcp_client.json names an environment variable that has no value."""


def _expand_text(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name == "PROJECT_ROOT":
            return ROOT.as_posix()
        value = os.environ.get(name)
        if not value:
            raise MissingSecretError(f"{name} is not set. Add it to the .env file.")
        return value

    return PLACEHOLDER.sub(replace, text)


def expand(value: Any) -> Any:
    """Replace ${NAME} in every string of a parsed JSON value."""
    if isinstance(value, str):
        return _expand_text(value)
    if isinstance(value, list):
        return [expand(item) for item in value]
    if isinstance(value, dict):
        return {key: expand(item) for key, item in value.items()}
    return value


def load_server(name: str) -> dict[str, Any]:
    servers = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))["mcpServers"]
    return expand(servers[name])


def open_client(name: str) -> Client:
    """Build a client for one server, so that one failure cannot affect another."""
    # Log only the name. The expanded settings can hold a secret.
    logger.debug(f"ACTION: open_client | server={name}")
    return Client(
        {"mcpServers": {name: load_server(name)}}, timeout=MCP_TIMEOUT_SECONDS
    )


def is_https_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.hostname)
