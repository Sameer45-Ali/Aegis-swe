"""
AST Code Graph Navigator.
Provides fast semantic lookup, caller/callee traversal, and context-pruned codebase mapping.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from aegis.core.ast_graph.parser import CodeASTParser, CodeSymbol, FileASTSummary


class ASTCodeGraphNavigator:
    """Builds and queries an in-memory AST symbol graph for a repository."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()
        self.files_map: Dict[str, FileASTSummary] = {}
        self.symbols_map: Dict[str, List[CodeSymbol]] = {}
        self.call_graph: Dict[str, Set[str]] = {}  # caller_symbol -> set(callees)
        self.index_codebase()

    def index_codebase(self) -> int:
        """Indexes all Python files in the codebase."""
        self.files_map.clear()
        self.symbols_map.clear()
        self.call_graph.clear()

        count = 0
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", "build", "dist"}

        for py_file in self.root_dir.rglob("*.py"):
            if any(ignored in py_file.parts for ignored in ignore_dirs):
                continue

            rel_path = str(py_file.relative_to(self.root_dir)).replace("\\", "/")
            summary = CodeASTParser.parse_python_file(py_file)
            if summary:
                summary.file_path = rel_path
                self.files_map[rel_path] = summary
                count += 1

                for sym in summary.symbols:
                    sym.file_path = rel_path
                    self.symbols_map.setdefault(sym.name, []).append(sym)

                    # Build call graph edges
                    for callee in sym.calls:
                        self.call_graph.setdefault(sym.name, set()).add(callee)

        return count

    def get_structure_overview(self) -> str:
        """Returns a high-level summary of all files, classes, and top-level functions."""
        lines = []
        for path, summary in sorted(self.files_map.items()):
            symbols_desc = [f"{s.symbol_type}:{s.name}(L{s.start_line}-{s.end_line})" for s in summary.symbols]
            syms_str = ", ".join(symbols_desc) if symbols_desc else "no exported symbols"
            lines.append(f"- {path} ({summary.total_lines} lines): {syms_str}")
        return "\n".join(lines)

    def find_symbol(self, symbol_name: str) -> List[CodeSymbol]:
        """Finds all definitions of a symbol by name."""
        return self.symbols_map.get(symbol_name, [])

    def get_file_content(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Optional[str]:
        """Reads file content, optionally sliced by line range."""
        clean_path = file_path.replace("\\", "/")
        full_path = self.root_dir / clean_path
        if not full_path.exists() or not full_path.is_file():
            return None

        content = full_path.read_text(encoding="utf-8", errors="replace")
        if start_line is None and end_line is None:
            return content

        lines = content.splitlines()
        start = max(1, start_line or 1)
        end = min(len(lines), end_line or len(lines))
        return "\n".join(lines[start - 1 : end])

    def search_relevant_context(self, keywords: List[str], max_symbols: int = 8) -> str:
        """Finds relevant symbols and snippets based on query keywords."""
        matched: List[CodeSymbol] = []
        kw_lower = [k.lower() for k in keywords if len(k) > 2]

        for name, sym_list in self.symbols_map.items():
            name_lower = name.lower()
            if any(k in name_lower for k in kw_lower):
                matched.extend(sym_list)

        matched = matched[:max_symbols]
        if not matched:
            return "No matching symbols found via AST query."

        results = []
        for s in matched:
            results.append(
                f"### Symbol: `{s.name}` ({s.symbol_type}) in `{s.file_path}:L{s.start_line}-{s.end_line}`\n"
                f"```python\n{s.code_snippet}\n```"
            )
        return "\n\n".join(results)
