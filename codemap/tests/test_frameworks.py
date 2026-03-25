import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from frameworks import detect_framework, apply_overrides

FIXTURES = Path(__file__).parent / "fixtures"

def test_detects_nextjs():
    result = detect_framework(str(FIXTURES / "nextjs"))
    assert result["framework"] == "nextjs"
    assert result["language"] == "typescript"
    assert "routes" in result["sections"]

def test_detects_flutter():
    result = detect_framework(str(FIXTURES / "flutter"))
    assert result["framework"] == "flutter"
    assert result["language"] == "dart"
    assert "screens" in result["sections"]

def test_falls_back_to_generic():
    result = detect_framework(str(FIXTURES / "generic"))
    assert result["framework"] == "generic"
    assert result["language"] is None

def test_detects_monorepo():
    result = detect_framework(str(FIXTURES / "monorepo"))
    assert result["monorepo"] is not None
    assert result["monorepo"]["apps_dir"] == "apps"
    assert result["monorepo"]["packages_dir"] == "packages"

def test_returns_section_configs():
    result = detect_framework(str(FIXTURES / "nextjs"))
    routes = result["sections"]["routes"]
    assert isinstance(routes["pattern"], list)
    assert "src/app/**/page.tsx" in routes["pattern"]
    assert routes["label"] == "Routes"

def test_apply_overrides():
    fw = {
        "framework": "flutter",
        "language": "dart",
        "sections": {
            "screens": {"pattern": "lib/**/screens/**/*.dart", "label": "Screens"},
        },
        "monorepo": None,
    }
    overrides = {
        "sections": {
            "screens": {"pattern": "lib/**/pages/**/*.dart", "label": "Pages"},
            "blocs": {"pattern": "lib/**/bloc/**/*.dart", "label": "BLoCs"},
        }
    }
    result = apply_overrides(fw, overrides)
    assert result["sections"]["screens"]["label"] == "Pages"
    assert result["sections"]["screens"]["pattern"] == "lib/**/pages/**/*.dart"
    assert "blocs" in result["sections"]
    assert result["framework"] == "flutter"

def test_apply_overrides_framework():
    fw = {
        "framework": "generic",
        "language": None,
        "sections": {},
        "monorepo": None,
    }
    overrides = {"framework": "custom"}
    result = apply_overrides(fw, overrides)
    assert result["framework"] == "custom"

def test_generic_has_definitions_section():
    result = detect_framework(str(FIXTURES / "generic"))
    assert "definitions" in result["sections"]
    assert result["sections"]["definitions"]["pattern"] == "__auto__"

def test_load_overrides_malformed_returns_none(tmp_path):
    """Malformed .codemap.json should return None, not crash."""
    from frameworks import load_project_overrides
    (tmp_path / ".codemap.json").write_text('"just a string"')
    assert load_project_overrides(str(tmp_path)) is None

def test_load_overrides_bad_sections_returns_none(tmp_path):
    from frameworks import load_project_overrides
    (tmp_path / ".codemap.json").write_text('{"sections": "bad"}')
    assert load_project_overrides(str(tmp_path)) is None

def test_load_overrides_invalid_json_returns_none(tmp_path):
    from frameworks import load_project_overrides
    (tmp_path / ".codemap.json").write_text('{broken json')
    assert load_project_overrides(str(tmp_path)) is None
