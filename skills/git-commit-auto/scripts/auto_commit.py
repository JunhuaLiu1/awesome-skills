#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Tuple


def _git(repo_root: str, *args: str) -> str:
    out = subprocess.check_output(["git", "-C", repo_root, *args], stderr=subprocess.STDOUT)
    return out.decode("utf-8", errors="replace").strip()


def _repo_root() -> str:
    try:
        return _git(os.getcwd(), "rev-parse", "--show-toplevel")
    except Exception:
        print("not a git repo", file=sys.stderr)
        raise SystemExit(2)


def _has_staged(repo_root: str) -> bool:
    return bool(_git(repo_root, "diff", "--cached", "--name-only").strip())


def _suggest(repo_root: str, hint: str | None) -> Tuple[str, str]:
    script = os.path.join(os.path.dirname(__file__), "suggest_commit_message.py")
    cmd = ["python3", script, "--cached", "--json"]
    if hint:
        cmd.extend(["--hint", hint])
    out = subprocess.check_output(cmd, cwd=repo_root).decode("utf-8", errors="replace")
    data = json.loads(out)
    return data["subject"], data.get("body", "") or ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage (optional), generate message, and run git commit.")
    parser.add_argument("--stage", choices=["auto", "all", "none"], default="auto", help="staging strategy")
    parser.add_argument("--hint", type=str, default=None, help="Chinese summary hint (e.g. '完成注册功能')")
    parser.add_argument("--dry-run", action="store_true", help="only print suggested message")
    parser.add_argument("--yes", action="store_true", help="run git commit without extra confirmation")
    args = parser.parse_args()

    repo_root = _repo_root()

    if not _has_staged(repo_root):
        if args.stage == "none":
            print("no staged changes; pass --stage all/auto or stage manually", file=sys.stderr)
            return 3
        if args.stage in {"auto", "all"}:
            subprocess.check_call(["git", "-C", repo_root, "add", "-A"])

    if not _has_staged(repo_root):
        print("nothing to commit", file=sys.stderr)
        return 4

    subject, body = _suggest(repo_root, args.hint)

    print(f"subject: {subject}")
    if body:
        print("body:")
        print(body)

    if args.dry_run:
        return 0

    if not args.yes:
        print("\npass --yes to execute git commit", file=sys.stderr)
        return 5

    cmd = ["git", "-C", repo_root, "commit", "-m", subject]
    if body:
        cmd.extend(["-m", body])
    subprocess.check_call(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

