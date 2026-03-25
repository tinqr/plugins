"""Framework detection and section configuration."""

import glob
import json
import os
from typing import Optional

MONOREPO_MARKERS = {
    "detect": ["pnpm-workspace.yaml", "turbo.json", "lerna.json"],
    "apps_dir": "apps",
    "packages_dir": "packages",
}

_NEXTJS_RESERVED = [
    "**/page.tsx", "**/page.jsx",
    "**/layout.tsx", "**/layout.jsx",
    "**/route.ts", "**/route.js",
    "**/loading.tsx", "**/loading.jsx",
    "**/error.tsx", "**/error.jsx",
    "**/not-found.tsx", "**/not-found.jsx",
    "**/template.tsx", "**/template.jsx",
    "**/default.tsx", "**/default.jsx",
]

FRAMEWORKS = {
    "nextjs": {
        "detect": ["next.config.*"],
        "language": "typescript",
        "sections": {
            "routes": {
                "pattern": [
                    "src/app/**/page.tsx", "src/app/**/page.jsx",
                    "app/**/page.tsx", "app/**/page.jsx",
                ],
                "label": "Routes",
            },
            "api": {
                "pattern": [
                    "src/app/**/route.ts", "src/app/**/route.js",
                    "app/**/route.ts", "app/**/route.js",
                ],
                "label": "API Routes",
            },
            "layouts": {
                "pattern": [
                    "src/app/**/layout.tsx", "src/app/**/layout.jsx",
                    "app/**/layout.tsx", "app/**/layout.jsx",
                ],
                "label": "Layouts",
            },
            "schema": {"pattern": "prisma/schema.prisma", "label": "Database Schema"},
            "components": {
                "pattern": [
                    "src/components/**/*.tsx", "src/components/**/*.jsx",
                    "components/**/*.tsx", "components/**/*.jsx",
                    "src/app/**/*.tsx", "src/app/**/*.jsx",
                    "app/**/*.tsx", "app/**/*.jsx",
                ],
                "exclude": _NEXTJS_RESERVED,
                "label": "Components",
            },
            "actions": {
                "pattern": [
                    "src/app/**/actions.ts", "src/app/**/actions.tsx",
                    "app/**/actions.ts", "app/**/actions.tsx",
                ],
                "label": "Server Actions",
            },
            "exports": {
                "pattern": [
                    "src/lib/**/*.ts", "src/lib/**/*.tsx",
                    "lib/**/*.ts", "lib/**/*.tsx",
                    "src/utils/**/*.ts", "src/utils/**/*.tsx",
                ],
                "label": "Shared Libraries",
            },
        },
    },
    "flutter": {
        "detect": ["pubspec.yaml"],
        "language": "dart",
        "sections": {
            "screens": {"pattern": "lib/**/screens/**/*.dart", "label": "Screens"},
            "models": {"pattern": "lib/**/models/**/*.dart", "label": "Models"},
            "widgets": {"pattern": "lib/**/widgets/**/*.dart", "label": "Widgets"},
            "providers": {"pattern": "lib/**/providers/**/*.dart", "label": "State Management"},
            "services": {"pattern": "lib/**/services/**/*.dart", "label": "Services"},
        },
    },
    "prisma": {
        "detect": ["prisma/schema.prisma"],
        "language": "typescript",
        "sections": {
            "schema": {"pattern": "prisma/schema.prisma", "label": "Database Schema"},
            "exports": {"pattern": "src/**/*.ts", "label": "Exports"},
        },
    },
    "generic": {
        "detect": [],
        "language": None,
        "sections": {
            "definitions": {"pattern": "__auto__", "label": "Code Definitions"},
        },
    },
}


def _detect_monorepo(project_root: str) -> Optional[dict]:
    """Check for monorepo markers at project root."""
    for pattern in MONOREPO_MARKERS["detect"]:
        if glob.glob(os.path.join(project_root, pattern)):
            return {
                "apps_dir": MONOREPO_MARKERS["apps_dir"],
                "packages_dir": MONOREPO_MARKERS["packages_dir"],
            }
    return None


def _detect_framework_in_dir(directory: str) -> Optional[str]:
    """Try to match a framework by its detect patterns in a directory."""
    for name, config in FRAMEWORKS.items():
        if name == "generic":
            continue
        for pattern in config["detect"]:
            if glob.glob(os.path.join(directory, pattern)):
                return name
    return None


def detect_framework(project_root: str) -> dict:
    """Detect framework from project root. Returns config dict."""
    monorepo = _detect_monorepo(project_root)

    # Try detecting framework at root level
    framework_name = _detect_framework_in_dir(project_root)

    # If no framework at root but monorepo detected, look inside apps/
    if framework_name is None and monorepo is not None:
        apps_dir = os.path.join(project_root, monorepo["apps_dir"])
        if os.path.isdir(apps_dir):
            for entry in sorted(os.listdir(apps_dir)):
                app_path = os.path.join(apps_dir, entry)
                if os.path.isdir(app_path):
                    framework_name = _detect_framework_in_dir(app_path)
                    if framework_name is not None:
                        break

    # Fall back to generic
    if framework_name is None:
        framework_name = "generic"

    config = FRAMEWORKS[framework_name]

    result = {
        "framework": framework_name,
        "language": config["language"],
        "sections": dict(config["sections"]),
        "monorepo": monorepo,
    }

    # Apply .codemap.json overrides if present
    overrides = load_project_overrides(project_root)
    if overrides:
        result = apply_overrides(result, overrides)

        # Apply monorepo dir overrides
        if result["monorepo"] and "monorepo" in overrides:
            mono_ov = overrides["monorepo"]
            if isinstance(mono_ov, dict):
                if "apps_dir" in mono_ov:
                    result["monorepo"]["apps_dir"] = mono_ov["apps_dir"]
                if "packages_dir" in mono_ov:
                    result["monorepo"]["packages_dir"] = mono_ov["packages_dir"]

    return result


def load_project_overrides(project_root: str) -> Optional[dict]:
    """Load .codemap.json overrides if present."""
    config_path = os.path.join(project_root, ".codemap.json")
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            print("[codemap] Warning: .codemap.json must be a JSON object, skipping")
            return None
        if "sections" in data and not isinstance(data["sections"], dict):
            print("[codemap] Warning: .codemap.json 'sections' must be an object, skipping")
            return None
        return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"[codemap] Warning: Could not read .codemap.json: {e}")
        return None


def apply_overrides(fw_config: dict, overrides: dict) -> dict:
    """Merge .codemap.json overrides into framework config."""
    result = dict(fw_config)
    if "sections" in overrides:
        merged = dict(result["sections"])
        merged.update(overrides["sections"])
        result["sections"] = merged
    if "framework" in overrides:
        result["framework"] = overrides["framework"]
    return result
