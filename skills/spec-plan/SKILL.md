---
name: spec-plan
description: 当用户希望进行 Spec 驱动开发时，先澄清需求，再生成一份精炼、可实施的 Spec。本 Skill 不编写实现代码。
---

# Spec Workflow

## 1. 建立上下文

快速查看：

- README
- docs/
- src/
- git log -20

了解项目结构和已有约定即可。

如果无法访问仓库，说明缺少上下文，并将未知项标记为 `TBD`。

---

## 2. 澄清需求

只问影响开发的问题。

规则：

- 每轮最多 3 个问题
- 总问题数不超过 8 个
- 优先使用多选
- 信息足够立即停止提问

重点确认：

- 要解决什么问题？
- 成功标准是什么？
- 本次范围是什么？
- 有哪些重要约束？

---

## 3. 收敛方案

给出 2~3 个方案。

每个方案仅包含：

- 简介
- 优点
- 缺点
- 复杂度

最后推荐一个即可。

---

## 4. 编写 Spec

生成唯一文件：

`docs/specs/spec{n}_<slug>.md`

自动递增编号。

不要生成 Design、Todo 或其他文档。

Spec 保持精炼，建议控制在 300~800 字。

结构：

```md
# Title

## Background
为什么做

## Goal
本次目标

## Out of Scope
明确不做什么

## Requirements
5~10 条核心需求

## Acceptance
- [ ] ...

## Constraints
重要限制（没有可写 None）

## Open Questions（可选）
```

原则：

- 能一句话就不用一段
- 能列表就不用长文
- 不写实现细节
- 不过度设计

---

## 5. Review

写入文件后，仅告诉用户：

- 文件路径
- 标题
- 简要摘要

不要在聊天中输出完整 Spec。

根据用户意见持续修改同一个文件。

---

## 6. Commit

只有用户明确确认后才允许：

```
git add docs/specs/spec{n}_<slug>.md
git commit -m "docs: add spec{n} <slug>"
```

整个流程仅允许一次 Commit。