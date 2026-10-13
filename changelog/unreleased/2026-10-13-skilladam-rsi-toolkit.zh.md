# SkillAdam 技能自进化工具包

- **Date:** 2026-10-13
- **Type:** feature
- **Scope:** `skills`, `docs`
- **PR:** [#1](https://github.com/Saigyouji-Yuyuko1000/penguin-harness/pull/1)

[English](2026-10-13-skilladam-rsi-toolkit.md)

新增了本地 `skilladam-rsi-toolkit` 插件包，提供一个控制技能，根据执行反馈迭代优化目标 Agent 的工作技能。

## 迭代与评测

该技能结合了持续更新的问题记录、受限补丁、配对评测、接受或回退，以及按方差调整的修改预算。提供了确定性的补丁和分数校验工具，以及训练和留出测试相互隔离的 GDPevo 流程。

评测采用了与 OPRO、APE 相同的 worker 协议和记分板格式，并明确接收评估中心所选的 Benchmark。完整的冒烟与候选结果在固定题集上记录，标注覆盖范围；结果汇总工具拒绝缺题或题集变化的记录。完整模式的小批次决策使用固定题集评测中的对应结果。同时补充了源码安装包的准备流程，以及逐次评测与反馈轨迹的关联记录。

该插件包支持本地导入，本次未将其登记到 npm 默认插件库。
