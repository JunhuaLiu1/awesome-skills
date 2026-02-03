#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any


def run(args: list[str], *, cwd: Optional[Path] = None) -> str:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def load_state(explicit_state: Optional[str]) -> Dict[str, Any]:
    if explicit_state:
        p = Path(explicit_state).expanduser()
        return json.loads(p.read_text(encoding="utf-8"))
    toplevel = Path(run(["git", "rev-parse", "--show-toplevel"]))
    git_common_dir = Path(run(["git", "-C", str(toplevel), "rev-parse", "--git-common-dir"]))
    state_path = git_common_dir / "codex-worktree-flow" / "state.json"
    if not state_path.exists():
        raise RuntimeError(f"state not found: {state_path}")
    return json.loads(state_path.read_text(encoding="utf-8"))


def git_is_clean(repo_root: Path) -> bool:
    out = run(["git", "-C", str(repo_root), "status", "--porcelain"])
    return out.strip() == ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge back and/or cleanup a git worktree (Codex helper).")
    parser.add_argument("--state", default="", help="Path to state.json (optional).")
    parser.add_argument("--yes", action="store_true", help="Actually perform actions. Without this, only prints plan.")
    parser.add_argument("--merge", action="store_true", help="Merge branch into base in the main worktree.")
    parser.add_argument("--cleanup", action="store_true", help="Remove worktree and delete branch (safe delete).")
    parser.add_argument("--strategy", default="merge", choices=["merge", "squash"], help="Merge strategy.")
    parser.add_argument("--squash-message", default="", help="Commit message to use for squash merge.")
    args = parser.parse_args()

    state = load_state(args.state or None)
    repo_root = Path(state["repo_root"])
    base = state["base"]
    branch = state["branch"]
    worktree_path = Path(state["worktree_path"])

    planned = []
    if args.merge:
        if args.strategy == "merge":
            planned.append(f"git checkout {base} (in {repo_root})")
            planned.append(f"git merge --no-ff --no-edit {branch}")
        else:
            planned.append(f"git checkout {base} (in {repo_root})")
            planned.append(f"git merge --squash {branch}")
            planned.append('git commit -m "<squash-message>"')
    if args.cleanup:
        planned.append(f"git worktree remove {worktree_path}")
        planned.append(f"git branch -d {branch}")
        planned.append("remove state.json")

    if not args.yes:
        print(
            json.dumps(
                {
                    "repo_root": str(repo_root),
                    "base": base,
                    "branch": branch,
                    "worktree_path": str(worktree_path),
                    "planned": planned,
                    "note": "Add --yes to execute. This tool does not prompt interactively.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.merge:
        if not git_is_clean(repo_root):
            raise RuntimeError(f"main worktree not clean: {repo_root} (commit/stash first)")

        run(["git", "-C", str(repo_root), "checkout", base])
        if args.strategy == "merge":
            run(["git", "-C", str(repo_root), "-c", "merge.autoEdit=false", "merge", "--no-ff", "--no-edit", branch])
        else:
            msg = args.squash_message.strip()
            if not msg:
                raise RuntimeError("--strategy squash requires --squash-message to avoid opening an editor")
            run(["git", "-C", str(repo_root), "merge", "--squash", branch])
            run(["git", "-C", str(repo_root), "commit", "-m", msg])

    if args.cleanup:
        run(["git", "-C", str(repo_root), "worktree", "remove", str(worktree_path)])
        # Safe delete only; if not merged, Git will refuse.
        run(["git", "-C", str(repo_root), "branch", "-d", branch])
        state_path = Path(state["git_common_dir"]) / "codex-worktree-flow" / "state.json"
        if state_path.exists():
            state_path.unlink()

    print(
        json.dumps(
            {
                "done": True,
                "repo_root": str(repo_root),
                "base": base,
                "branch": branch,
                "worktree_path": str(worktree_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[git-worktree-flow] ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
