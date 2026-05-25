import os
import subprocess
from pathlib import Path

try:
    from duckduckgo_search import DDGS
    _ddgs_available = True
except ImportError:
    _ddgs_available = False

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Use this for facts, news, or anything requiring up-to-date knowledge.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file from the local filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path to the file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates the file if it doesn't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_python",
        "description": "Execute a Python code snippet and return the output. Use for calculations, data processing, or testing logic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories at a given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: current directory)", "default": "."},
            },
            "required": [],
        },
    },
]


def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "web_search":
            return _web_search(inputs["query"], inputs.get("max_results", 5))
        elif name == "read_file":
            return _read_file(inputs["path"])
        elif name == "write_file":
            return _write_file(inputs["path"], inputs["content"])
        elif name == "run_python":
            return _run_python(inputs["code"])
        elif name == "list_directory":
            return _list_directory(inputs.get("path", "."))
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error: {e}"


def _web_search(query: str, max_results: int) -> str:
    if not _ddgs_available:
        return "Web search unavailable: install duckduckgo-search"
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(f"**{r['title']}**\n{r['href']}\n{r['body']}")
    return "\n\n---\n\n".join(results) if results else "No results found."


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"File not found: {path}"
    if p.stat().st_size > 1_000_000:
        return "File too large (>1MB). Read in chunks."
    return p.read_text(encoding="utf-8", errors="replace")


def _write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} characters to {path}"


def _run_python(code: str) -> str:
    result = subprocess.run(
        ["python3", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout
    if result.stderr:
        output += f"\nSTDERR:\n{result.stderr}"
    return output.strip() or "(no output)"


def _list_directory(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Path not found: {path}"
    entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
    lines = []
    for entry in entries:
        prefix = "📁 " if entry.is_dir() else "📄 "
        lines.append(f"{prefix}{entry.name}")
    return "\n".join(lines) if lines else "(empty directory)"
