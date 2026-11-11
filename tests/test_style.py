# House style for the code itself: comments use # instead of docstrings.
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_FILES = [p for p in (ROOT / "src").rglob("*.py")] + [p for p in (ROOT / "tests").glob("*.py")] + [ROOT / "benchmark" / "bench.py"]


class StyleTests(unittest.TestCase):
    def test_no_docstrings(self):
        for path in PY_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
                    first = node.body[0]
                    is_doc = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str)
                    self.assertFalse(is_doc, f"{path.name}:{first.lineno} uses a docstring. Use # comments.")


if __name__ == "__main__":
    unittest.main()
