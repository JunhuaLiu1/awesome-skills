---
name: git-worktree-flow
description: 用 Git worktree 创建隔离工作区并在独立分支上迭代提交；当用户提到 worktree、git worktree、GitWorkTree、工作树、隔离分支、临时工作区，或希望“先创建 worktree 再实现需求、过程中持续 commit、完成后询问是否合并并清理 worktree”时使用。
---

# Git worktree 工作流（中文为主）

本 Skill 的目标：**先创建 Git worktree**，把本次需求放到独立分支/独立目录里做；过程中在该分支里**持续提交**；完成后**询问是否合并回主分支**，并在确认后**清理 worktree 与分支**。

## 默认约定（可按需覆盖）

- **主分支/基线分支（base）**：优先使用 `origin/HEAD` 指向的默认分支；否则尝试 `main` / `master`；再否则用当前分支。
- **worktree 目录**：默认放在仓库根目录的 `.worktrees/<branch>`（会写入本地 `info/exclude`，避免污染 `git status`）。
- **分支命名**：默认 `wt/<YYYYMMDD-HHMM>-<slug>`（slug 从需求中提取/简化）。
- **合并策略**：默认 `--no-ff --no-edit` 的 merge commit；如用户偏好，可改为 squash。

## 核心流程

### 0) 先冻结需求（避免创建 worktree 后跑题）

- 用 1–3 句复述用户需求与验收标准（中文为主）。
- 记录一个简短 `slug`（用于分支名），例如：`fix-player-cache`、`feat-search-ui`。

### 1) 创建 worktree（必须先做）

1. 确认当前目录在 Git 仓库内：`git rev-parse --show-toplevel`
2. 如当前工作区有未提交修改，优先先提交或 stash；不建议直接创建 worktree 然后把“脏状态”带过去。
3. 定位本 Skill 的脚本目录：
   - `skill_dir` = 本 `SKILL.md` 所在目录
   - 脚本路径：`<skill_dir>/scripts/worktree_create.py`、`<skill_dir>/scripts/worktree_finish.py`
4. 运行创建脚本（推荐）：

   - 自动生成分支名 + worktree 路径：
     - `python3 <skill_dir>/scripts/worktree_create.py --slug "<本次需求简短代号>"`
   - 显式指定 base / branch / path：
     - `python3 <skill_dir>/scripts/worktree_create.py --base main --branch wt/20260203-fix-player --path .worktrees/wt-20260203-fix-player`

脚本会输出 worktree 路径与分支名，并在 Git common dir 里保存本次会话的 state，供后续合并/清理使用。

### 2) 在 worktree 中完成需求（并持续提交）

1. `cd <worktree_path>`
2. 在该 worktree 内完成用户需求（实现 / 修复 / 重构 / 文档 / 测试等）。
3. **持续提交（强制习惯）**：
   - 每个可验证的小步提交一次；提交前先运行最相关的验证命令（例如 `go test ./...` / `npm run lint` / 目标用例）。
   - 典型节奏：改动 → 验证 → `git add -A` → `git commit -m "fix: ..."` → 下一步。
   - 若用户明确要求整理提交历史，再考虑最后 squash；否则优先保留“可回滚的小步提交”。

### 3) 完成后询问：是否合并回主分支 + 是否清理

在你认为需求已完成且验证通过后，必须问用户一个明确问题（默认推荐选项放在最前）：

- A（推荐）合并到 base，然后删除 worktree 与分支
- B 合并到 base，但保留 worktree（方便复查/后续改动）
- C 暂不合并，只给出 worktree 路径与分支名（交由用户决定）

若用户选择 A 或 B：

1. 在**主工作区**（不是 worktree）执行合并（推荐用脚本，避免遗漏）：
   - 预览将执行的动作（不做实际修改）：
     - `python3 <skill_dir>/scripts/worktree_finish.py`
   - 真正执行（会合并；若带 `--cleanup` 则会移除 worktree，并尝试 `git branch -d`）：
     - `python3 <skill_dir>/scripts/worktree_finish.py --yes --merge --cleanup`

若用户选择 C：

- 只输出：worktree 路径、分支名、base 分支、建议的后续命令（merge/cleanup），不要做任何合并/删除。

## 安全护栏（必须遵守）

- **合并与删除属于高风险动作**：必须在执行前再次确认用户选择，并说明会执行哪些命令。
- **不要 `-D` 强删分支**；除非用户明确同意，并且你已解释风险。
- 如果合并/删除失败，停止自动化流程，输出“可复制粘贴”的手工恢复/处理步骤。

## 常见问题

- worktree 目录出现在 `git status`：脚本会写入 `$(git rev-parse --git-common-dir)/info/exclude` 来忽略 `.worktrees/`。
- `worktree add` 提示分支已存在：用 `--branch` 指向已有分支，或先清理旧 worktree。
- 合并冲突：停止并提示用户；在主工作区解决冲突、提交，再继续 cleanup。
