"""
AST Symbol and Hierarchy Parser.
Extracts classes, functions, imports, signatures, and call references.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str  # "function", "class", "async_function", "method"
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class FileASTSummary:
    file_path: str
    imports: List[str] = field(default_factory=list)
    symbols: List[CodeSymbol] = field(default_factory=list)
    total_lines: int = 0
    raw_content: Optional[str] = None


class PythonASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.imports: List[str] = []
        self.symbols: List[CodeSymbol] = []
        self._current_class: Optional[str] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            self.imports.append(f"{mod}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self._current_class
        self._current_class = node.name
        
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        docstring = ast.get_docstring(node)
        snippet = "\n".join(self.lines[start_line - 1 : end_line])

        sym = CodeSymbol(
            name=node.name,
            symbol_type="class",
            file_path=self.file_path,
            start_line=start_line,
            end_line=end_line,
            docstring=docstring,
            parent_class=prev_class,
            code_snippet=snippet,
        )
        self.symbols.append(sym)
        self.generic_visit(node)
        self._current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node, is_async=True)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        docstring = ast.get_docstring(node)
        params = [a.arg for a in node.args.args]
        snippet = "\n".join(self.lines[start_line - 1 : end_line])

        calls = []
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call):
                if isinstance(sub_node.func, ast.Name):
                    calls.append(sub_node.func.id)
                elif isinstance(sub_node.func, ast.Attribute):
                    calls.append(sub_node.func.attr)

        symbol_type = "method" if self._current_class else ("async_function" if is_async else "function")
        sym = CodeSymbol(
            name=node.name,
            symbol_type=symbol_type,
            file_path=self.file_path,
            start_line=start_line,
            end_line=end_line,
            docstring=docstring,
            parameters=params,
            calls=list(set(calls)),
            parent_class=self._current_class,
            code_snippet=snippet,
        )
        self.symbols.append(sym)
        self.generic_visit(node)


class CodeASTParser:
    """Parses source files into structured AST summaries and symbols."""

    @staticmethod
    def parse_python_file(file_path: Path | str, content: Optional[str] = None) -> Optional[FileASTSummary]:
        path_obj = Path(file_path)
        try:
            if content is None:
                content = path_obj.read_text(encoding="utf-8", errors="replace")
            
            tree = ast.parse(content, filename=str(file_path))
            visitor = PythonASTVisitor(file_path=str(file_path), source_code=content)
            visitor.visit(tree)

            return FileASTSummary(
                file_path=str(file_path),
                imports=visitor.imports,
                symbols=visitor.symbols,
                total_lines=len(content.splitlines()),
                raw_content=content,
            )
        except Exception:
            return None
