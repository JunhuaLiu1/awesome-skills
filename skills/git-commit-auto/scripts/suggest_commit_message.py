#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


def _run_git(repo_root: str, args: List[str]) -> str:
    out = subprocess.check_output(["git", "-C", repo_root, *args], stderr=subprocess.STDOUT)
    return out.decode("utf-8", errors="replace")


def _git_try(repo_root: str, args: List[str]) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(["git", "-C", repo_root, *args], stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.output or b"").decode("utf-8", errors="replace")


def _get_repo_root() -> str:
    code, out = _git_try(os.getcwd(), ["rev-parse", "--show-toplevel"])
    if code != 0:
        print("not a git repo", file=sys.stderr)
        sys.exit(2)
    return out.strip()


def _parse_z_pairs(data: bytes) -> List[str]:
    if not data:
        return []
    parts = data.split(b"\x00")
    if parts and parts[-1] == b"":
        parts = parts[:-1]
    return [p.decode("utf-8", errors="replace") for p in parts]


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str


def _list_changed_files(repo_root: str, cached: bool) -> List[ChangedFile]:
    args = ["diff", "--name-status", "-z"]
    if cached:
        args.insert(1, "--cached")
    raw = subprocess.check_output(["git", "-C", repo_root, *args])
    parts = _parse_z_pairs(raw)

    changed: List[ChangedFile] = []
    i = 0
    while i < len(parts):
        status = parts[i]
        if not status:
            i += 1
            continue
        # status is like "M", "A", "D" or "R100" etc.
        if status.startswith("R") or status.startswith("C"):
            # rename/copy: next two paths (old, new); use new as primary
            if i + 2 >= len(parts):
                break
            new_path = parts[i + 2]
            changed.append(ChangedFile(status=status[:1], path=new_path))
            i += 3
            continue

        if i + 1 >= len(parts):
            break
        changed.append(ChangedFile(status=status[:1], path=parts[i + 1]))
        i += 2
    return changed


def _list_untracked_files(repo_root: str) -> List[ChangedFile]:
    raw = subprocess.check_output(
        ["git", "-C", repo_root, "ls-files", "--others", "--exclude-standard", "-z"]
    )
    paths = _parse_z_pairs(raw)
    return [ChangedFile(status="A", path=p) for p in paths]


def _dominant_area(paths: Iterable[str]) -> str:
    counts: dict[str, int] = {}
    for p in paths:
        top = p.split("/", 1)[0] if "/" in p else p
        counts[top] = counts.get(top, 0) + 1
    if not counts:
        return "项目"
    top = max(counts.items(), key=lambda kv: kv[1])[0]
    mapping = {
        "mobile-app": "移动端",
        "backend": "后端",
        "docs": "文档",
    }
    return mapping.get(top, "项目")


def _is_docs_only(paths: List[str]) -> bool:
    if not paths:
        return False
    for p in paths:
        if p.startswith("docs/"):
            continue
        if p.lower().endswith(".md"):
            continue
        return False
    return True


def _is_test_only(paths: List[str]) -> bool:
    if not paths:
        return False
    test_patterns = [
        re.compile(r"_test\.go$"),
        re.compile(r"\.(spec|test)\.(ts|tsx|js|jsx)$"),
        re.compile(r"(^|/)__tests__(/|$)"),
        re.compile(r"(^|/)tests?(/|$)"),
    ]
    for p in paths:
        if any(r.search(p) for r in test_patterns):
            continue
        return False
    return True


def _is_chore_only(paths: List[str]) -> bool:
    if not paths:
        return False
    allow = {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "go.mod",
        "go.sum",
        "tsconfig.json",
        "app.json",
        "app.config.js",
        "app.config.ts",
        ".gitignore",
        ".gitattributes",
    }
    for p in paths:
        base = p.split("/")[-1]
        if base in allow:
            continue
        if p.startswith(".github/"):
            continue
        if p.startswith(".vscode/"):
            continue
        if base.endswith((".yml", ".yaml")) and ("eslint" in base or "prettier" in base):
            continue
        return False
    return True


def _infer_type(paths: List[str], user_hint: str | None) -> str:
    if user_hint and any(k in user_hint for k in ["修复", "bug", "崩溃", "异常", "错误"]):
        return "fix"
    if _is_docs_only(paths):
        return "docs"
    if _is_test_only(paths):
        return "test"
    if _is_chore_only(paths):
        return "chore"
    return "feat"


def _infer_object(changed: List[ChangedFile]) -> Optional[str]:
    # Prefer very specific new pages/docs over generic folder names (e.g. "profile").
    for c in changed:
        p = c.path.lower()
        if c.status == "A" and "about" in p:
            return "关于我们"
        if c.status == "A" and "privacy" in p:
            return "隐私政策"

    keywords = [
        ("about", "关于我们"),
        ("privacy", "隐私政策"),
        ("register", "注册"),
        ("signup", "注册"),
        ("login", "登录"),
        ("auth", "认证"),
        ("profile", "个人中心"),
        ("account", "账号"),
        ("search", "搜索"),
        ("player", "播放器"),
        ("history", "历史"),
        ("download", "下载"),
        ("cache", "缓存"),
        ("toast", "Toast"),
        ("supabase", "Supabase"),
        ("api", "接口"),
        ("route", "路由"),
        ("layout", "布局"),
    ]
    score: dict[str, int] = {}
    lower_items = [(c.path.lower(), c.status) for c in changed]
    for needle, zh in keywords:
        for path, status in lower_items:
            if needle in path:
                weight = 3 if status == "A" else 1
                score[zh] = score.get(zh, 0) + weight
    if not score:
        return None
    return max(score.items(), key=lambda kv: kv[1])[0]


def _infer_action(statuses: List[str]) -> str:
    if any(s == "A" for s in statuses):
        return "新增"
    if any(s == "D" for s in statuses):
        return "移除"
    return "更新"


def _compact_subject(prefix: str, summary: str, limit: int = 50) -> str:
    subject = f"{prefix}: {summary}".strip()
    if len(subject) <= limit:
        return subject
    # Try compacting common suffixes
    summary2 = summary.replace("功能", "").replace("页面", "")
    subject2 = f"{prefix}: {summary2}".strip()
    if len(subject2) <= limit:
        return subject2
    return subject[:limit]


def _shortstat(repo_root: str, cached: bool) -> str:
    args = ["diff", "--shortstat"]
    if cached:
        args.insert(1, "--cached")
    out = _run_git(repo_root, args).strip()
    return out


def build_message(repo_root: str, cached: bool, user_hint: Optional[str]) -> Tuple[str, str]:
    changed = _list_changed_files(repo_root, cached=cached)
    if not cached:
        changed = changed + _list_untracked_files(repo_root)
    paths = [c.path for c in changed]
    statuses = [c.status for c in changed]

    if not paths:
        raise RuntimeError("no changes to summarize")

    commit_type = _infer_type(paths, user_hint)
    area = _dominant_area(paths)
    obj = _infer_object(changed)
    action = _infer_action(statuses)

    if user_hint:
        summary = user_hint.strip()
    elif obj:
        # Prefer "新增关于我们页面" over "新增移动端变更"
        if commit_type == "docs":
            summary = f"{action}{obj}文档"
        elif obj in {"关于我们", "隐私政策"} and any("about" in p.lower() for p in paths):
            summary = f"{action}{obj}页面"
        elif "页面" in obj or obj.endswith("页"):
            summary = f"{action}{obj}"
        else:
            summary = f"{action}{obj}功能"
    else:
        summary = f"{action}{area}变更"

    subject = _compact_subject(commit_type, summary)

    stat = _shortstat(repo_root, cached=cached)
    lines: List[str] = []
    if stat:
        lines.append(f"- 统计：{stat}")

    # List up to 12 files
    max_files = 12
    for c in changed[:max_files]:
        lines.append(f"- {c.status} {c.path}")
    if len(changed) > max_files:
        lines.append(f"- ... 以及另外 {len(changed) - max_files} 个文件")

    body = "\n".join(lines).strip()
    return subject, body


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest a Chinese Conventional Commit message from git diff.")
    parser.add_argument("--cached", action="store_true", help="summarize staged changes (default)")
    parser.add_argument("--worktree", action="store_true", help="summarize unstaged worktree changes")
    parser.add_argument("--hint", type=str, default=None, help="override/assist the summary in Chinese (e.g. '完成注册功能')")
    parser.add_argument("--json", action="store_true", help="output JSON {subject, body}")
    args = parser.parse_args()

    if args.cached and args.worktree:
        print("choose one of --cached or --worktree", file=sys.stderr)
        return 2

    cached = not args.worktree
    repo_root = _get_repo_root()

    try:
        subject, body = build_message(repo_root, cached=cached, user_hint=args.hint)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps({"subject": subject, "body": body}, ensure_ascii=False))
        return 0

    print(f"subject: {subject}")
    if body:
        print("body:")
        print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
