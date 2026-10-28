# Evo-Harness Benchmark 适配

- **Date:** 2026-10-28
- **Type:** feature
- **Scope:** `skills`, `core`, `server`, `amsp`
- **PR:** [Saigyouji-Yuyuko1000/penguin-harness#2](https://github.com/Saigyouji-Yuyuko1000/penguin-harness/pull/2)

[English](2026-10-28-evo-benchmark-adapters.md)

添加了基于 .6 学习规则的 Evo-Harness 插件，以及原生会话反馈、Solver 阶段约束和后台任务等待接口。Evo 与 SkillAdam 保持为独立插件。

## 细节

- 添加了官方资源自动获取、固定提交缓存和完整 Project 包指纹校验。
- 将 Evo 运行准备、State 传输和原始 trial 验收工具随插件交付。
- 默认每组训练一次、每个冻结 State 测试三轮；先计算每轮领域平均分，再计算样本方差及标准差。
- 补齐了依赖、目录和文档中的插件登记。

## 兼容性

通过只读校验保留历史 Skill 格式，详见[向后兼容](2026-10-28-backward-compatibility.zh.md)。只有退出后评分的普通 Harbor 仍需原 Session 反馈适配器才能完成 Evo 学习。

2026.10.28.4 工程修订将插件 README 纳入准确的发布包清单，保留文件哈希和私有路径限制。
