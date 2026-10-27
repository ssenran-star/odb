# 备赛知识库助手

第六届 OceanBase 数据库大赛 · Qoder 赛道素材仓。

本目录提供项目说明、可粘贴给 Qoder 的任务书、运行占位步骤和练习笔记。应用代码在 **Qoder IDE** 里继续编写，可访问的作品用 **Qoder Sites** 发布，并把访问范围设为任何人可访问。

## 项目想法

备赛时，笔记、语雀摘录和官方 README 片段散落在各处。关键词对不上标题时，就翻不到原来的那一句。

「备赛知识库助手」把这些材料收进 **seekdb**，用 **pyseekdb 嵌入式模式**做混合检索：向量语义和关键词全文一起查，结果带回原文片段和来源路径。

复习进度可以以后再接到 PowerContext，用来记下「这篇看过、这道题还要回看」。当前验收不依赖这一步。

## 本目录里有什么

| 文件 | 用途 |
| --- | --- |
| `PROJECT_BRIEF_FOR_QODER.md` | 粘贴到 Qoder 的任务书 |
| `RUN.md` | 本地运行占位（虚拟环境、pyseekdb、数据路径、启动方式） |
| `VERIFY.md` | 一条验收样例：初始数据、查询、步骤、期望命中、如何证明用了 seekdb |
| `data/samples/` | 三篇练习用中文笔记，内容连贯，供导入和验收 |

## 基线

分支 `qoder` 从官方仓库 `oceanbase/powercontext` 的 `2026-competition-ecosystem` 拉出，起点提交：

`d647275c308e09b7b623f322a26f5c4e85734fb0`

同层的 `minimax/`、`dify/`、`gaode/`、`stepfun/` 保持官方占位，本分支只往 `qoder/` 里加素材。
