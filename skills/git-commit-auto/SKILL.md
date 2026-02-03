---
name: git-commit-auto
description: 自动扫描 Git 暂存区/工作区变更，生成中文提交信息（feat/fix/docs/refactor/test/chore 等）并执行 `git commit`。当用户提示词包含 “commit”/“git commit”/“提交”/“生成提交信息”/“帮我提交” 等时使用。
---

# 目标

- 在当前 Git 仓库里完成一次可控的提交：检查变更 →（必要时）暂存 → 生成中文 commit message → `git commit` → 输出结果。
- 提交信息遵循 Conventional Commit 形式，subject 用中文：`feat: 完成注册功能`。

# 工作流（按顺序执行）

## 1) 侦测变更

运行以下命令收集信息（不要臆测）：

- `git rev-parse --is-inside-work-tree`
- `git status --porcelain=v1`
- `git diff --stat`
- `git diff --cached --stat`

## 2) 暂存策略（安全优先）

- 若存在 staged 变更：默认只提交 staged（使用 `git diff --cached` 生成信息）。
- 若没有 staged 但工作区有变更：
  - 若用户明确说“全部提交/提交所有/直接提交工作区变更”，执行 `git add -A`。
  - 否则只问 1 个问题确认：是否执行 `git add -A` 再提交（默认推荐确认后再做）。

## 3) 生成提交信息（中文）

优先用脚本生成候选提交信息（基于 staged diff）：

- `python3 codex-skills/git-commit-auto/scripts/suggest_commit_message.py --cached`

若希望一键执行（先暂存再提交），可用：

- `python3 codex-skills/git-commit-auto/scripts/auto_commit.py --stage auto --yes`

若脚本无法给出清晰描述（例如“更新项目变更”过于笼统），只问 1 个问题让用户补一句中文摘要（例如“完成注册功能 / 修复播放页崩溃”），并保留脚本推断出的类型前缀（feat/fix 等）。

### 类型选择（启发式）

- 仅 `docs/` 或 `*.md`：`docs`
- 仅测试相关（如 `*_test.go`、`*.spec.ts`、`*.test.ts`）：`test`
- 仅配置/工程化（如 `package.json`、`go.mod`、CI 配置等）：`chore`
- 无明确证据时默认：`feat`
- 用户明确“修复/bug/崩溃/异常”：`fix`

### Message 约束

- subject 使用半角冒号：`feat: ...`
- subject 尽量 ≤ 50 字符（太长时压缩）
- body 可选：列 3–8 条要点或主要文件（不要堆满 diff）

## 4) 提交

- 提交前输出变更概览（文件列表 + stat），避免“盲提交”
- 执行：`git commit -m "<subject>"`（有 body 则用第二个 `-m`）
- 提交后校验：`git status --porcelain=v1`

# 默认交互策略（尽量少问）

- 能自动推断就直接提交（用户明确“直接提交/commit -y/不用确认”时不再二次确认）。
- 不确定会不会把不该提交的内容带上时（比如 unstaged 很多、含敏感文件、或变更跨度过大）必须先确认。
