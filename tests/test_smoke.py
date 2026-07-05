import ast
import pathlib


def test_all_sources_parse():
    root = pathlib.Path(__file__).parent.parent / "src"
    for f in root.rglob("*.py"):
        ast.parse(f.read_text(encoding="utf-8"))


def test_package_importable():
    import kipimo  # noqa: F401
