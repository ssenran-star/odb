# 运行步骤（占位）

应用代码在 Qoder IDE 中实现。下面是本地准备环境和启动时要遵守的步骤。命令在 `qoder/` 目录下执行。

## 1. 虚拟环境

需要 Python 3.11 或更高版本。

```bash
cd qoder
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -U pyseekdb
```

`.venv/` 和 seekdb 数据目录留在本地，不提交。

## 2. 环境变量

下面都是占位值。远程密码只放在本机环境里，不写进文件、不写进命令历史里的真实口令。

嵌入式模式（默认）：

```bash
export SEEKDB_PATH="./data/seekdb"
export SEEKDB_DATABASE="contest_notes"
export SEEKDB_COLLECTION="prep_notes"
export NOTES_DIR="./data/samples"
```

可选的远程 seekdb / OceanBase。留空 `SEEKDB_HOST` 时走嵌入式模式。

```bash
export SEEKDB_HOST=""
export SEEKDB_PORT="2881"
export SEEKDB_TENANT="sys"
export SEEKDB_USER="root"
export SEEKDB_PASSWORD=""
```

`SEEKDB_PASSWORD` 为空时，pyseekdb 会在远程模式下尝试读取同名环境变量。本地练习使用嵌入式模式即可，不必填写密码。

## 3. 数据路径

练习笔记在 `data/samples/`：

- `01-hybrid-search.md`
- `02-pyseekdb-embedded.md`
- `03-contest-prep-rhythm.md`

嵌入式数据目录是 `data/seekdb/`（与 `SEEKDB_PATH` 一致）。首次导入时由应用创建。

## 4. 启动

Qoder 实现出入口之后，在已激活的虚拟环境里启动。入口名以最终代码为准，占位命令：

```bash
python -m app
```

启动后应看到：

1. 使用的 seekdb 模式（嵌入式路径，或远程 host）。
2. 数据库名 `contest_notes` 与集合名 `prep_notes`。
3. 从 `NOTES_DIR` 导入的块数量。

然后打开页面或 CLI，按 `VERIFY.md` 搜一次「备赛口令」。

## 5. 发布

本地跑通后，在 Qoder 里用 Sites 发布当前站点，访问范围选「任何人都可访问」。把公开 URL 记入 `VERIFY.md`。预览地址和已发布地址不同，以发布后的公开链接为准。
