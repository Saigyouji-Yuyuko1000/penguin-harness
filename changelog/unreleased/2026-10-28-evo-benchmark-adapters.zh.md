# Evo-Harness RSI 工具包

- **Date:** 2026-10-28
- **Type:** feature
- **Scope:** `skills`
- **PR:** [Saigyouji-Yuyuko1000/penguin-harness#3](https://github.com/Saigyouji-Yuyuko1000/penguin-harness/pull/3)

[English](2026-10-28-evo-benchmark-adapters.md)

新增 Evo-Harness RSI 插件，使用现有原生委派、会话续接与 Agent State 接口。

## 细节

- 新增单次训练、原 Solver 会话中的负反馈反思，以及一次独立批量编译。
- 校验候选证据引用、ADD／MERGE／REVISE／SKIP 决策及字节预算内的完整 Skill 导出。
- 冻结后的任务上下文包含全部通用描述和匹配主题的完整正文。
- 默认对 Base／Skill 分别完成三轮完整测试，提供原生评分记录和按轮次计算的统计。
- 完成插件依赖、目录和文档登记。
