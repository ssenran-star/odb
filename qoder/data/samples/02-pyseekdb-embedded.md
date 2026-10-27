# pyseekdb 嵌入式连接备忘

练习素材，非正式官方文档。记录本地不单独起数据库服务时怎么连 seekdb。

## 嵌入式就够用

练习阶段用 pyseekdb 的嵌入式模式。数据落在本机目录里，进程退出后再打开，笔记还在。

```python
import pyseekdb

client = pyseekdb.Client(path="./data/seekdb", database="contest_notes")
collection = client.get_or_create_collection("prep_notes")
```

对应的环境变量：

- `SEEKDB_PATH=./data/seekdb`
- `SEEKDB_DATABASE=contest_notes`
- `SEEKDB_COLLECTION=prep_notes`
- `NOTES_DIR=./data/samples`

密码不放在代码里。嵌入式练习不需要 `SEEKDB_PASSWORD`。以后若改连远程 seekdb 或 OceanBase，主机、端口、租户、用户用环境变量，密码只放在 `SEEKDB_PASSWORD`。

## 中文笔记

样例笔记是中文。集合的全文解析使用 IK，避免按空格切开后中文句子无法命中。向量由集合上的 embedding function 在写入和 `query_texts` 查询时生成。

## 和远程模式怎么选

本机演示、Sites 上的小规模笔记库，优先嵌入式目录。已经有 seekdb 或 OceanBase 服务、并且要多人共用一份数据时，再把 `SEEKDB_HOST` 指到那台服务。两种模式都走同一个 `Client`，应用侧保留这一层切换即可。
