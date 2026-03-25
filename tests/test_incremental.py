import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from incremental import map_files_to_sections, has_new_or_deleted_files_in_list

NEXTJS_SECTIONS = {
    "routes": {"pattern": "src/app/**/page.tsx", "label": "Routes"},
    "schema": {"pattern": "prisma/schema.prisma", "label": "Database Schema"},
    "components": {"pattern": "src/components/**/*.tsx", "label": "Components"},
}

def test_maps_route_change():
    changed = ["src/app/orders/page.tsx"]
    affected = map_files_to_sections(changed, NEXTJS_SECTIONS)
    assert "routes" in affected

def test_maps_schema_change():
    changed = ["prisma/schema.prisma"]
    affected = map_files_to_sections(changed, NEXTJS_SECTIONS)
    assert "schema" in affected

def test_maps_component_change():
    changed = ["src/components/OrderCard.tsx"]
    affected = map_files_to_sections(changed, NEXTJS_SECTIONS)
    assert "components" in affected

def test_unrelated_file_maps_to_nothing():
    changed = ["README.md"]
    affected = map_files_to_sections(changed, NEXTJS_SECTIONS)
    assert len(affected) == 0

def test_always_includes_structure_on_add_delete():
    affected = map_files_to_sections(
        ["src/app/new/page.tsx"], NEXTJS_SECTIONS, files_added_or_deleted=True
    )
    assert "structure" in affected
    assert "routes" in affected

def test_always_includes_graph_when_code_section_affected():
    changed = ["src/components/OrderCard.tsx"]
    affected = map_files_to_sections(changed, NEXTJS_SECTIONS)
    assert "graph" in affected

def test_has_new_or_deleted():
    assert has_new_or_deleted_files_in_list(["A\tsrc/new.ts", "D\tsrc/old.ts"]) is True
    assert has_new_or_deleted_files_in_list(["M\tsrc/changed.ts"]) is False

def test_maps_api_route_change():
    sections = {
        "routes": {"pattern": "src/app/**/page.tsx", "label": "Routes"},
        "api": {"pattern": "src/app/**/route.ts", "label": "API Routes"},
        "layouts": {"pattern": "src/app/**/layout.tsx", "label": "Layouts"},
    }
    changed = ["src/app/api/orders/route.ts"]
    affected = map_files_to_sections(changed, sections)
    assert "api" in affected

def test_maps_layout_change():
    sections = {
        "routes": {"pattern": "src/app/**/page.tsx", "label": "Routes"},
        "layouts": {"pattern": "src/app/**/layout.tsx", "label": "Layouts"},
    }
    changed = ["src/app/layout.tsx"]
    affected = map_files_to_sections(changed, sections)
    assert "layouts" in affected

def test_get_changed_files_first_commit(tmp_path):
    """First commit (no HEAD~1) should not crash."""
    import subprocess
    from incremental import get_changed_files
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "first"], cwd=str(tmp_path), capture_output=True)
    changed = get_changed_files(str(tmp_path))
    assert "file.txt" in changed
