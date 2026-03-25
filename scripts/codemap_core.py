#!/usr/bin/env python3
"""Codemap CLI — auto-generated codebase context for AI agents."""

import os
import shutil
import stat
import subprocess
import sys
from typing import Optional

from frameworks import detect_framework
from incremental import (
    get_changed_files,
    get_changed_files_with_status,
    has_new_or_deleted_files_in_list,
    map_files_to_sections,
)
from meta import (
    compute_hash,
    get_codemap_dir,
    get_current_branch,
    get_git_remote,
    now_iso,
    read_meta,
    write_meta,
)
from repomap_class import RepoMap
from sections import (
    discover_section_files,
    generate_graph_markdown,
    generate_section_markdown,
    generate_structure_markdown,
)

COMMANDS = {
    "init": "Full generation for a project",
    "refresh": "Manual full regeneration",
    "incremental": "Update only changed sections (called by post-commit hook)",
    "setup": "Install git hooks + generate first codemap",
}

HOOK_MARKER = "# codemap-hook"
HOOKS_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "git-hooks"
)

GITIGNORE_ENTRIES = ["docs/codemap/", ".repomap.tags.cache.v1/", ".codemap-errors.log"]


def _log(msg: str) -> None:
    print(f"[codemap] {msg}")


def _write_section(codemap_dir: str, name: str, content: str) -> None:
    path = os.path.join(codemap_dir, f"{name}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _generate_single_project(
    project_root: str, fw_config: dict, codemap_dir: str, repo_map: RepoMap
) -> list:
    """Generate sections for a single (non-monorepo) project. Returns all code files."""
    sections = fw_config["sections"]
    all_code_files = []

    for section_name, section_cfg in sections.items():
        _log(f"Generating {section_name}.md...")
        files = discover_section_files(project_root, section_cfg["pattern"], section_cfg.get("exclude"))
        all_code_files.extend(files)

        route_paths = section_name == "routes"
        schema_mode = section_name == "schema"

        md = generate_section_markdown(
            repo_map,
            project_root,
            section_cfg["label"],
            files,
            route_paths=route_paths,
            schema_mode=schema_mode,
        )
        _write_section(codemap_dir, section_name, md)

    return all_code_files


def _generate_monorepo(
    project_root: str, fw_config: dict, monorepo: dict, codemap_dir: str
) -> list:
    """Generate sections for each app/package in a monorepo. Returns all code files."""
    all_code_files = []
    apps_dir_name = monorepo["apps_dir"]
    packages_dir_name = monorepo["packages_dir"]

    for kind, dir_name in [("apps", apps_dir_name), ("packages", packages_dir_name)]:
        base = os.path.join(project_root, dir_name)
        if not os.path.isdir(base):
            continue

        for entry in sorted(os.listdir(base)):
            entry_path = os.path.join(base, entry)
            if not os.path.isdir(entry_path):
                continue

            _log(f"Processing {kind}/{entry}...")
            sub_fw = detect_framework(entry_path)
            sections = sub_fw["sections"]
            sub_codemap_dir = os.path.join(codemap_dir, kind, entry)
            os.makedirs(sub_codemap_dir, exist_ok=True)

            sub_repo_map = RepoMap(root=entry_path)

            for section_name, section_cfg in sections.items():
                _log(f"  Generating {kind}/{entry}/{section_name}.md...")
                files = discover_section_files(entry_path, section_cfg["pattern"], section_cfg.get("exclude"))

                # Prefix relative paths so they're relative to project_root
                prefix = os.path.join(dir_name, entry)
                prefixed = [os.path.join(prefix, f) for f in files]
                all_code_files.extend(prefixed)

                route_paths = section_name == "routes"
                schema_mode = section_name == "schema"

                md = generate_section_markdown(
                    sub_repo_map,
                    entry_path,
                    section_cfg["label"],
                    files,
                    route_paths=route_paths,
                    schema_mode=schema_mode,
                )
                _write_section(sub_codemap_dir, section_name, md)

    return all_code_files


def _build_meta(
    project_root: str,
    fw_config: dict,
    monorepo: Optional[dict],
    codemap_dir: str,
    sections_data: Optional[dict] = None,
) -> dict:
    """Build meta.json dict with per-section hashes."""
    meta = {
        "framework": fw_config["framework"],
        "language": fw_config["language"],
        "monorepo": monorepo is not None,
        "branch": get_current_branch(project_root),
        "remote": get_git_remote(project_root),
        "generated_at": now_iso(),
        "sections": sections_data if sections_data else {},
    }
    return meta


def _collect_section_hashes_single(project_root: str, sections: dict) -> dict:
    """Compute hashes for each section in a single project."""
    result = {}
    for section_name, section_cfg in sections.items():
        files = discover_section_files(project_root, section_cfg["pattern"], section_cfg.get("exclude"))
        result[section_name] = {
            "hash": compute_hash(project_root, files),
            "updated_at": now_iso(),
            "file_count": len(files),
        }
    return result


def _collect_section_hashes_monorepo(
    project_root: str, monorepo: dict
) -> dict:
    """Compute hashes for each section in monorepo apps/packages."""
    result = {}
    apps_dir_name = monorepo["apps_dir"]
    packages_dir_name = monorepo["packages_dir"]

    for kind, dir_name in [("apps", apps_dir_name), ("packages", packages_dir_name)]:
        base = os.path.join(project_root, dir_name)
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            entry_path = os.path.join(base, entry)
            if not os.path.isdir(entry_path):
                continue
            sub_fw = detect_framework(entry_path)
            for section_name, section_cfg in sub_fw["sections"].items():
                key = f"{kind}/{entry}/{section_name}"
                files = discover_section_files(entry_path, section_cfg["pattern"], section_cfg.get("exclude"))
                result[key] = {
                    "hash": compute_hash(entry_path, files),
                    "updated_at": now_iso(),
                    "file_count": len(files),
                }
    return result


def cmd_init(project_root: str) -> None:
    """Full codemap generation."""
    _log(f"Initializing codemap for {project_root}")

    fw = detect_framework(project_root)
    _log(f"Detected framework: {fw['framework']}")

    codemap_dir = get_codemap_dir(project_root)
    os.makedirs(codemap_dir, exist_ok=True)

    # Structure
    _log("Generating structure.md...")
    structure_md = generate_structure_markdown(project_root)
    _write_section(codemap_dir, "structure", structure_md)

    # Sections
    monorepo = fw["monorepo"]
    repo_map = RepoMap(root=project_root)

    if monorepo:
        all_code_files = _generate_monorepo(project_root, fw, monorepo, codemap_dir)
        sections_data = _collect_section_hashes_monorepo(project_root, monorepo)
    else:
        all_code_files = _generate_single_project(project_root, fw, codemap_dir, repo_map)
        sections_data = _collect_section_hashes_single(project_root, fw["sections"])

    # Graph
    _log("Generating graph.md...")
    graph_md = generate_graph_markdown(repo_map, project_root, all_code_files)
    _write_section(codemap_dir, "graph", graph_md)

    # Meta
    meta = _build_meta(project_root, fw, monorepo, codemap_dir, sections_data)
    write_meta(project_root, meta)
    _log("Wrote meta.json")

    _log("Done.")


def _group_changed_by_subproject(
    changed_files: list, monorepo: dict, project_root: str
) -> dict:
    """Group changed files by their monorepo sub-project."""
    apps_dir = monorepo["apps_dir"]
    packages_dir = monorepo["packages_dir"]
    groups = {}

    for f in changed_files:
        parts = f.split("/")
        matched = False
        for kind_key, dir_name in [("apps", apps_dir), ("packages", packages_dir)]:
            if len(parts) >= 3 and parts[0] == dir_name:
                sub_name = parts[1]
                sub_rel = "/".join(parts[2:])
                key = (kind_key, sub_name)
                groups.setdefault(key, []).append(sub_rel)
                matched = True
                break
        if not matched:
            groups.setdefault((None, None), []).append(f)

    return groups


def _incremental_single(
    project_root: str, sections: dict, changed: list,
    files_added_or_deleted: bool, codemap_dir: str, meta: dict,
    repo_map: RepoMap, section_prefix: str = "",
) -> bool:
    """Run incremental update for a single project/sub-project. Returns True if anything changed."""
    affected = map_files_to_sections(
        changed, sections, files_added_or_deleted=files_added_or_deleted
    )
    if not affected:
        return False

    _log(f"Affected sections: {', '.join(sorted(affected))}")
    updated = False

    for section_name in affected:
        if section_name in ("structure", "graph"):
            continue
        if section_name not in sections:
            continue

        section_cfg = sections[section_name]
        full_name = f"{section_prefix}{section_name}" if section_prefix else section_name
        _log(f"Regenerating {full_name}.md...")
        files = discover_section_files(project_root, section_cfg["pattern"], section_cfg.get("exclude"))

        route_paths = section_name == "routes"
        schema_mode = section_name == "schema"

        md = generate_section_markdown(
            repo_map,
            project_root,
            section_cfg["label"],
            files,
            route_paths=route_paths,
            schema_mode=schema_mode,
        )
        _write_section(codemap_dir, section_name, md)

        meta_key = f"{section_prefix}{section_name}" if section_prefix else section_name
        meta.setdefault("sections", {})[meta_key] = {
            "hash": compute_hash(project_root, files),
            "updated_at": now_iso(),
            "file_count": len(files),
        }
        updated = True

    if "structure" in affected:
        _log(f"Regenerating {section_prefix}structure.md...")
        structure_md = generate_structure_markdown(project_root)
        _write_section(codemap_dir, "structure", structure_md)
        updated = True

    return updated


def cmd_incremental(project_root: str) -> None:
    """Incremental update — only regenerate changed sections."""
    meta = read_meta(project_root)
    if meta is None:
        _log("No existing codemap found. Running full init instead.")
        cmd_init(project_root)
        return

    changed = get_changed_files(project_root)
    if not changed:
        _log("No changed files. Nothing to update.")
        return

    if len(changed) > 50:
        _log(f"{len(changed)} files changed (>50). Running full refresh.")
        cmd_init(project_root)
        return

    status_lines = get_changed_files_with_status(project_root)
    files_added_or_deleted = has_new_or_deleted_files_in_list(status_lines)

    fw = detect_framework(project_root)
    monorepo = fw["monorepo"]
    codemap_dir = get_codemap_dir(project_root)
    any_updated = False

    if monorepo:
        groups = _group_changed_by_subproject(changed, monorepo, project_root)

        for (kind, name), sub_changed in groups.items():
            if kind is None:
                if files_added_or_deleted:
                    _log("Regenerating structure.md...")
                    structure_md = generate_structure_markdown(project_root)
                    _write_section(codemap_dir, "structure", structure_md)
                    any_updated = True
                continue

            sub_path = os.path.join(project_root, monorepo[f"{kind}_dir"], name)
            if not os.path.isdir(sub_path):
                continue

            sub_fw = detect_framework(sub_path)
            sub_codemap_dir = os.path.join(codemap_dir, kind, name)
            os.makedirs(sub_codemap_dir, exist_ok=True)

            sub_repo_map = RepoMap(root=sub_path)

            prefix = f"{kind}/{name}/"
            _log(f"Checking {kind}/{name}...")
            updated = _incremental_single(
                sub_path, sub_fw["sections"], sub_changed,
                files_added_or_deleted, sub_codemap_dir, meta,
                sub_repo_map, section_prefix=prefix,
            )
            if updated:
                any_updated = True
    else:
        sections = fw["sections"]
        repo_map = RepoMap(root=project_root)
        any_updated = _incremental_single(
            project_root, sections, changed,
            files_added_or_deleted, codemap_dir, meta,
            repo_map,
        )

    # Regenerate graph if any code sections changed
    if any_updated:
        _log("Regenerating graph.md...")
        repo_map = RepoMap(root=project_root)
        all_code_files = []
        if monorepo:
            for kind, dir_name in [("apps", monorepo["apps_dir"]), ("packages", monorepo["packages_dir"])]:
                base = os.path.join(project_root, dir_name)
                if not os.path.isdir(base):
                    continue
                for entry in sorted(os.listdir(base)):
                    entry_path = os.path.join(base, entry)
                    if not os.path.isdir(entry_path):
                        continue
                    sub_fw = detect_framework(entry_path)
                    prefix = os.path.join(dir_name, entry)
                    for section_cfg in sub_fw["sections"].values():
                        files = discover_section_files(entry_path, section_cfg["pattern"], section_cfg.get("exclude"))
                        all_code_files.extend([os.path.join(prefix, f) for f in files])
        else:
            for section_cfg in fw["sections"].values():
                all_code_files.extend(
                    discover_section_files(project_root, section_cfg["pattern"], section_cfg.get("exclude"))
                )
        graph_md = generate_graph_markdown(repo_map, project_root, all_code_files)
        _write_section(codemap_dir, "graph", graph_md)

    if any_updated:
        meta["generated_at"] = now_iso()
        write_meta(project_root, meta)
        _log("Incremental update complete.")
    else:
        _log("Changed files don't affect any codemap sections.")


def cmd_setup(project_root: str) -> None:
    """First-time project setup: hooks + gitignore + init."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _log(f"Error: {project_root} is not a git repository.")
        sys.exit(1)

    git_dir = result.stdout.strip()
    if not os.path.isabs(git_dir):
        git_dir = os.path.join(project_root, git_dir)

    hooks_dir = os.path.join(git_dir, "hooks")

    if os.path.isdir(HOOKS_SOURCE_DIR):
        for hook_file in os.listdir(HOOKS_SOURCE_DIR):
            src = os.path.join(HOOKS_SOURCE_DIR, hook_file)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(hooks_dir, hook_file)

            with open(src) as f:
                hook_content = f.read()

            if os.path.exists(dst):
                with open(dst) as f:
                    existing = f.read()
                if HOOK_MARKER in existing:
                    _log(f"Updating {hook_file} hook...")
                    with open(dst, "w") as f:
                        f.write(hook_content)
                else:
                    _log(f"Appending codemap hook to existing {hook_file}...")
                    with open(dst, "a") as f:
                        f.write(f"\n{hook_content}")
            else:
                _log(f"Installing {hook_file} hook...")
                with open(dst, "w") as f:
                    f.write(hook_content)

            st = os.stat(dst)
            os.chmod(dst, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    else:
        _log("Warning: git-hooks/ directory not found. Skipping hook installation.")

    # Update .gitignore
    gitignore_path = os.path.join(project_root, ".gitignore")
    existing_lines = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            existing_lines = f.read().splitlines()

    added = []
    for entry in GITIGNORE_ENTRIES:
        if entry not in existing_lines:
            existing_lines.append(entry)
            added.append(entry)

    if added:
        with open(gitignore_path, "w") as f:
            f.write("\n".join(existing_lines) + "\n")
        _log(f"Added to .gitignore: {', '.join(added)}")
    else:
        _log(".gitignore already has codemap entries.")

    # Run init
    cmd_init(project_root)

    _log(f"Setup complete for {project_root}")


def cli_main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: codemap <init|refresh|incremental|setup> <project_root>")
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd:15s} {desc}")
        sys.exit(1)

    command = sys.argv[1]
    project_root = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    project_root = os.path.abspath(project_root)

    if command in ("init", "refresh"):
        cmd_init(project_root)
    elif command == "incremental":
        cmd_incremental(project_root)
    elif command == "setup":
        cmd_setup(project_root)


if __name__ == "__main__":
    cli_main()
