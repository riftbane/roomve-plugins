#!/usr/bin/env python3
"""Checks the marketplace before a push reaches the people who installed it.

    python3 scripts/check.py [--base <git ref>]

- .claude-plugin/marketplace.json and every plugin's plugin.json and .mcp.json are valid and say what they must;
- every SKILL.md has a frontmatter with a name equal to its folder and a description of at most 1024 characters
  (the limit of claude.ai), is at most 500 lines long, and the files it points to exist;
- with --base: a plugin whose files changed since that commit must have a higher `version`, because Claude
  keeps the installed copy until the version changes.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def fail(path, message: str) -> None:
    rel = Path(path).relative_to(ROOT) if Path(path).is_absolute() else path
    errors.append(f"{rel}: {message}")
    print(f"::error file={rel}::{message}")


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(path, f"not valid JSON ({exc})")
        return None


def version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, OSError):
        return None


def check_skill(skill: Path) -> None:
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return fail(skill, "frontmatter missing")
    fields = dict(re.findall(r"^([\w-]+):\s*(.*)$", m.group(1), re.M))
    name, desc = fields.get("name", ""), fields.get("description", "").strip()
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        fail(skill, f"name '{name}' is not valid (1-64 characters among a-z, 0-9, -)")
    if name != skill.parent.name:
        fail(skill, f"name '{name}' differs from its folder '{skill.parent.name}'")
    if not 1 <= len(desc) <= 1024:
        fail(skill, f"description of {len(desc)} characters: the limit is 1024")
    lines = text.count("\n")
    if lines > 500:
        fail(skill, f"{lines} lines: keep SKILL.md under 500 and move detail to references/")
    for ref in set(re.findall(r"`(references/[\w./-]+)`", text)):
        if not (skill.parent / ref).is_file():
            fail(skill, f"points to {ref}, which does not exist")
    print(f"{skill.relative_to(ROOT)}: name={name}, description of {len(desc)} characters, {lines} lines")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    base = ap.parse_args().base.strip()

    market = load(ROOT / ".claude-plugin" / "marketplace.json")
    if market is None:
        return 1
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", str(market.get("name", ""))):
        fail(".claude-plugin/marketplace.json", "name missing or not valid")
    if not (market.get("owner") or {}).get("name"):
        fail(".claude-plugin/marketplace.json", "owner.name missing")
    plugins = market.get("plugins") or []
    if not plugins:
        fail(".claude-plugin/marketplace.json", "no plugins listed")

    for entry in plugins:
        source = entry.get("source")
        if not isinstance(source, str) or not source.startswith("./") or ".." in source:
            fail(".claude-plugin/marketplace.json", f"plugin {entry.get('name')}: source must be a path like ./name")
            continue
        folder = ROOT / source
        manifest = load(folder / ".claude-plugin" / "plugin.json")
        if manifest is None:
            continue
        if manifest.get("name") != entry.get("name"):
            fail(folder / ".claude-plugin" / "plugin.json", "name differs from the marketplace entry")
        if "version" in entry:
            fail(".claude-plugin/marketplace.json", "set version in plugin.json only, not in the marketplace entry")
        version = str(manifest.get("version", ""))
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            fail(folder / ".claude-plugin" / "plugin.json", f"version '{version}' is not x.y.z")
        mcp = folder / ".mcp.json"
        if mcp.exists():
            servers = (load(mcp) or {}).get("mcpServers") or {}
            for key, server in servers.items():
                if server.get("type") in ("http", "sse") and not str(server.get("url", "")).startswith("https://"):
                    fail(mcp, f"server {key}: url must be https")
                if "headers" in server or "env" in server:
                    fail(mcp, f"server {key}: no headers or env here (a public file must hold no secrets)")
        skills = sorted((folder / "skills").glob("*/SKILL.md"))
        if not skills:
            fail(folder, "no skills found")
        for skill in skills:
            check_skill(skill)

        if base and set(base) != {"0"} and git("cat-file", "-e", f"{base}^{{commit}}") is not None:
            changed = git("diff", "--name-only", base, "HEAD", "--", source) or ""
            old = git("show", f"{base}:{source[2:]}/.claude-plugin/plugin.json")
            if changed.strip() and old:
                old_version = str(json.loads(old).get("version", ""))
                if version_tuple(version) <= version_tuple(old_version):
                    fail(folder / ".claude-plugin" / "plugin.json",
                         f"the plugin changed but version is still {version} (was {old_version}): raise it, or Claude "
                         "will not pick up the change")
                else:
                    print(f"{entry.get('name')}: {old_version} -> {version}")

    print("FAILED" if errors else "OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
