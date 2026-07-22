---
name: spec-plan
description: 使用 Spec 驱动开发，先写 Spec，再实现。
---

生成一份精炼、可评审的 Spec，不编写实现代码。

流程：

1. 理解仓库上下文（如可访问）。
2. 只询问影响实现的关键问题，信息足够立即停止。
3. 如有必要，给出 2~3 个方案并推荐一个。
4. 生成唯一 Spec 文件：`docs/specs/spec{n}_<slug>.md`
5. 等待用户 Review，根据反馈修改同一文件。
6. 用户确认后，仅提交该 Spec。

Spec 应包含：

- Background
- Goal
- Scope
- Requirements
- Acceptance

始终遵循：

- Less is More
- 不过度设计
- 不写实现细节
- 不生成额外文档
- 一个 Spec，一次 Commit