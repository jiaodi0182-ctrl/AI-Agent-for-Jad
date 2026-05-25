import sys
sys.path.insert(0, ".")
import pytest
from tools import execute_tool


def test_run_python_basic():
    result = execute_tool("run_python", {"code": "print(1 + 1)"})
    assert result == "2"


def test_run_python_error():
    result = execute_tool("run_python", {"code": "print(1/0)"})
    assert "ZeroDivisionError" in result


def test_write_and_read_file(tmp_path):
    path = str(tmp_path / "test.txt")
    write_result = execute_tool("write_file", {"path": path, "content": "hello world"})
    assert "Written" in write_result

    read_result = execute_tool("read_file", {"path": path})
    assert read_result == "hello world"


def test_read_missing_file():
    result = execute_tool("read_file", {"path": "/nonexistent/file.txt"})
    assert "not found" in result


def test_list_directory(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "subdir").mkdir()
    result = execute_tool("list_directory", {"path": str(tmp_path)})
    assert "file.txt" in result
    assert "subdir" in result


def test_unknown_tool():
    result = execute_tool("nonexistent_tool", {})
    assert "Unknown tool" in result
