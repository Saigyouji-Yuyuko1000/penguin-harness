# 历史 Evo Skill 兼容

- **Date:** 2026-10-28
- **Type:** fix
- **Scope:** `skills`
- **PR:** [Saigyouji-Yuyuko1000/penguin-harness#3](https://github.com/Saigyouji-Yuyuko1000/penguin-harness/pull/3)

[English](2026-10-28-backward-compatibility.md)

保留了历史 .6 Reader 原始字节、绝对与相对读取路径、State 身份以及原定 16,000 字节限制。验证仅读取原文件，不重新导出，也不替换分数、费用或结论。

## 兼容性

兼容读取一直保留到用户明确批准移除、且历史实验不再需要为止。由 Evo 插件维护者负责移除；未添加自动迁移或过期机制。
