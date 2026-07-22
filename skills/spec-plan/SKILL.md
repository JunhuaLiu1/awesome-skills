---
name: spec-plan
description: 使用 Spec 驱动开发，先写 Spec，再实现。
---

生成一份精炼、可评审的 Spec，不编写实现代码。

## Workflow

1. 理解仓库上下文（如可访问）。
2. 只询问影响实现的关键问题，信息足够立即停止。
3. 如有必要，给出 2~3 个方案并推荐一个。
4. 生成唯一 Spec：`docs/specs/spec{n}_<slug>.md`。
5. 等待用户 Review，根据反馈修改同一文件。
6. 用户确认后，仅提交该 Spec。

## Spec

建议包含：

- Background
- Goal
- Overview
- Requirements
- Acceptance

## Principles

- Less is More
- 能一句话说明，就不要写一段
- Spec 聚焦「做什么」，而不是「怎么做」
- Overview 展示整体改动
- 不过度设计
- 不写实现代码
- 不生成额外文档
- 一个 Spec，一个 Commit