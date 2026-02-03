#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"SKILL.md not found: {skill_md}", file=sys.stderr)
        return 1

    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"(?s)^---\n(.*?)\n---\n", text)
    if not m:
        print("Invalid frontmatter: must start with --- and end with ---", file=sys.stderr)
        return 1

    raw = m.group(1).strip()
    kv = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            print(f"Invalid frontmatter line (expected key: value): {line}", file=sys.stderr)
            return 1
        key, value = line.split(":", 1)
        kv[key.strip()] = value.strip()

    allowed = {"name", "description"}
    extra = set(kv.keys()) - allowed
    missing = {"name", "description"} - set(kv.keys())
    if extra:
        print(f"Frontmatter contains unsupported keys: {sorted(extra)}", file=sys.stderr)
        return 1
    if missing:
        print(f"Frontmatter missing required keys: {sorted(missing)}", file=sys.stderr)
        return 1

    folder_name = skill_dir.name
    if kv["name"] != folder_name:
        print(f'Name mismatch: frontmatter name="{kv["name"]}" but folder="{folder_name}"', file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
