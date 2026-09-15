"""
Tests for AST Code Graph Parser and Navigator.
"""

from pathlib import Path
import tempfile
import pytest
from aegis.core.ast_graph.navigator import ASTCodeGraphNavigator
from aegis.core.ast_graph.parser import CodeASTParser


SAMPLE_CODE = """
import os
from typing import List

class DataProcessor:
    def __init__(self, name: str):
        self.name = name

    def process(self, items: List[int]) -> int:
        \"\"\"Sums the items.\"\"\"
        return sum(items)

def helper_func():
    return True
"""


def test_ast_parser_extracts_symbols():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(SAMPLE_CODE)
        f_path = f.name

    summary = CodeASTParser.parse_python_file(f_path)
    assert summary is not None
    assert "os" in summary.imports
    
    sym_names = [s.name for s in summary.symbols]
    assert "DataProcessor" in sym_names
    assert "process" in sym_names
    assert "helper_func" in sym_names

    Path(f_path).unlink(missing_ok=True)


def test_ast_navigator_queries():
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "module.py"
        target.write_text(SAMPLE_CODE, encoding="utf-8")

        nav = ASTCodeGraphNavigator(temp_dir)
        symbols = nav.find_symbol("process")
        assert len(symbols) == 1
        assert symbols[0].symbol_type == "method"
        assert symbols[0].parent_class == "DataProcessor"
