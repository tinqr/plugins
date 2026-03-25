import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from repomap_class import RepoMap
from sections import discover_section_files, generate_section_markdown, generate_structure_markdown

FIXTURES = Path(__file__).parent / "fixtures"

def test_discovers_nextjs_routes():
    files = discover_section_files(str(FIXTURES / "nextjs"), "src/app/**/page.tsx")
    assert len(files) == 2
    assert any("orders" in f for f in files)

def test_discovers_flutter_screens():
    files = discover_section_files(str(FIXTURES / "flutter"), "lib/**/screens/**/*.dart")
    assert len(files) == 1
    assert "home_screen.dart" in files[0]

def test_discovers_prisma_schema():
    files = discover_section_files(str(FIXTURES / "nextjs"), "prisma/schema.prisma")
    assert len(files) == 1

def test_ignores_node_modules_and_git():
    files = discover_section_files(str(FIXTURES / "nextjs"), "**/*.tsx")
    for f in files:
        assert "node_modules" not in f
        assert ".git" not in f

def test_generate_structure_markdown():
    md = generate_structure_markdown(str(FIXTURES / "nextjs"))
    assert "src/" in md or "src" in md
    assert "prisma" in md
    assert "page.tsx" in md

def test_generate_section_routes():
    root = str(FIXTURES / "nextjs")
    repo_map = RepoMap(root=root)
    files = discover_section_files(root, "src/app/**/page.tsx")
    md = generate_section_markdown(repo_map, root, "Routes", files, route_paths=True)
    assert "/orders" in md
    assert "page.tsx" in md

def test_generate_section_schema():
    root = str(FIXTURES / "nextjs")
    repo_map = RepoMap(root=root)
    files = discover_section_files(root, "prisma/schema.prisma")
    md = generate_section_markdown(repo_map, root, "Database Schema", files, schema_mode=True)
    assert "Tenant" in md
    assert "Order" in md

def test_discover_auto_parseable_files():
    """__auto__ pattern discovers files tree-sitter can parse."""
    files = discover_section_files(str(FIXTURES / "generic"), "__auto__")
    assert len(files) >= 1
    assert any("index.js" in f for f in files)

def test_generate_section_generic_definitions():
    root = str(FIXTURES / "generic")
    repo_map = RepoMap(root=root)
    files = discover_section_files(root, "__auto__")
    md = generate_section_markdown(repo_map, root, "Code Definitions", files)
    assert "index.js" in md or "main" in md

def test_route_group_stripping():
    from sections import _derive_route_path
    assert _derive_route_path("src/app/(marketing)/about/page.tsx") == "/about"
    assert _derive_route_path("src/app/(dashboard)/settings/page.tsx") == "/settings"
    assert _derive_route_path("src/app/orders/page.tsx") == "/orders"
    assert _derive_route_path("src/app/page.tsx") == "/"
