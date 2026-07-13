# emMindRAG

> 嵌入式专用精准 RAG —— 寄存器/手册检索,基于标准 MCP 协议。

为嵌入式开发者:用 **SVD 结构化数据零幻觉查寄存器**,用 **文档 RAG + reranker 检索手册/代码**,两者还能**关联**呈现。Claude Code / Cursor / Codex 即插即用。

## 核心能力

- ⭐ **SVD 寄存器查询(零幻觉)** —— 152 颗 STM32 全系列,精确到寄存器/位域/枚举/地址
- ⭐ **跨芯片对比** —— 同一寄存器在 152 颗芯片里的差异,独家
- ⭐ **SVD ↔ 文档关联** —— 查寄存器自动关联手册/代码用法,结构化+非结构化合一,独家
- 🚀 **文档 RAG + bge-reranker 重排** —— PDF/MD/txt/Word/EPUB/网页/代码 7 种格式
- 🔧 **CLI + MCP** —— 终端命令 + AI 工具双入口,doctor 体检 + 跨电脑迁移

---

## 快速开始

### 1. 环境
Python 3.11+(Windows / Mac / Linux 均可)

### 2. 获取代码 + 安装依赖
```bash
git clone https://github.com/darkChench/emMindRAG.git
cd emMindRAG
python -m venv .venv
.venv\Scripts\activate          # Windows(bash 用 .venv/Scripts/activate)
pip install -r requirements.txt
```

### 3. 下载 SVD 芯片库(~340M,152 颗 STM32)
```bash
git clone --depth 1 https://github.com/tinygo-org/stm32-svd /tmp/stm32-svd
cp /tmp/stm32-svd/svd/*.svd svd_files/
```

### 4. 下载 reranker 模型(~280M,可选)
不下也能用(search 会自动降级为双路融合,只是精度略降)。国内用 hf-mirror 镜像:
```bash
mkdir -p models/bge-reranker-base
curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/onnx/model_quantized.onnx -o models/bge-reranker-base/model.onnx
curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/tokenizer.json -o models/bge-reranker-base/tokenizer.json
curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/config.json -o models/bge-reranker-base/config.json
```

### 5. 体检(确认环境就绪)
```bash
python cli.py doctor
# 想重建 SVD 缓存:python cli.py doctor --fix
```

### 6. 索引文档 + 搜索
```bash
python cli.py add 手册.pdf                    # 索引(PDF/Word/EPUB/网页/代码都行)
python cli.py add demo_driver.c               # 代码自动按函数切
python cli.py search "SPI 的 CPHA 位怎么配"
python cli.py search "GPIO 配置" --code       # 只在代码里搜
python cli.py reg GPIOA MODER stm32f407       # 查寄存器(零幻觉)
python cli.py explain GPIOA MODER stm32f407   # 寄存器事实 + 手册/代码关联(独家)
python cli.py chips                           # 列出 152 颗芯片
```

### 7. 连到 AI 工具(MCP)
`.mcp.json` 已配好。把它放到 AI 工具的工作区根目录,重载 Claude Code / Cursor,首次信任即可。之后对话里就能调 7 个工具。

---

## CLI 命令

| 命令 | 作用 |
|------|------|
| `add <文件>` | 索引(支持 7 种格式,代码自动按函数切) |
| `search <词> [-n N] [--code] [--source 文件]` | 搜索(双路召回 + reranker 重排) |
| `list` | 看书架(按来源分组) |
| `remove --source <文件> \| --all` | 删除 |
| `chips` | 列出已加载的 STM32 芯片 |
| `reg <外设> [寄存器] [芯片]` | 查寄存器(SVD,零幻觉) |
| `explain <外设> [寄存器] [芯片]` | 寄存器事实 + 手册/代码关联(独家) |
| `doctor [--fix]` | 体检 / 重建缓存 |

## 扫描件 / 复杂版式 PDF(可选,用 MinerU 在线 API)

**默认 auto**:add PDF 时先走 PyMuPDF(快),若文字极少(判定扫描件)会自动转 MinerU OCR,无需手动指定。也可强制用 MinerU(不需本地装 torch/模型,只走网络):

```bash
python cli.py add 扫描手册.pdf --mineru          # 强制 MinerU(默认 auto 已自动检测扫描件)
```

大文件配 token 解锁精准 API(≤200MB / ≤200页):
```bash
# 去 https://mineru.net 注册,在 API 管理页创建 token
set MINERU_TOKEN=你的token            # Windows(bash 用 export MINERU_TOKEN=...)
python cli.py add 大手册.pdf --mineru
```

MinerU 失败会自动降级 PyMuPDF,不会中断。AI 工具里调 `index_doc(file, mineru=True)` 同样生效。

## Embedding 模型(可选:中文在线)

默认用 chromadb 自带 MiniLM(英文,本地快)。中文手册想提升向量检索精度,可配在线 embedding(GLM / OpenAI 兼容):

```bash
# GLM(智谱,国内首选)
set EMBEDDING_PROVIDER=glm
set EMBEDDING_API_KEY=你的智谱key

# 或 OpenAI / 兼容代理
set EMBEDDING_PROVIDER=openai
set EMBEDDING_API_KEY=你的key
set OPENAI_BASE_URL=https://api.openai.com/v1     # 可选,换代理
set EMBEDDING_MODEL=text-embedding-3-small         # 可选,否则用默认
```

⚠️ **换 embedding 必须重建书架**(向量维度变了,旧数据不兼容):
```bash
python cli.py remove --all
python cli.py add 你的文档.pdf
```

> 在线 embedding 每次索引/查询都调 API(有延迟和费用),中文质量高;默认 MiniLM 本地快但偏英文。按需选。

## MCP 工具(7 个,AI 自动调用)

`search_docs` / `list_docs` / `index_doc` / `get_register` / `explain_register` / `list_peripherals` / `list_chips`

---

## 迁移到新电脑

1. **拷代码** —— 不要拷 `.venv`、`chroma_db`、`svd_files/*.svd`、`models/`、`__pycache__`(这些要么重装、要么重下,见 .gitignore)
2. **装依赖** —— `python -m venv .venv && pip install -r requirements.txt`
3. **下 SVD + 模型** —— 见上面第 3、4 步
4. **体检** —— `python cli.py doctor` 确认齐全
5. **重新索引文档** —— `python cli.py add 你的文档`(或者把旧电脑的 `chroma_db/` 直接拷过来,跳过这步)

> 想保留旧书架:直接把整个 `chroma_db/` 文件夹拷到新机器即可,不用重新索引。

---

## 项目结构

```
emMindRAG/
├── server.py             # MCP 入口(7 个工具)
├── cli.py                # 命令行工具(8 个命令)
├── parser.py             # 文档解析(7 种格式 + MinerU API)
├── chunker.py            # 智能分块(表格/代码原子 + 标题章节链 + 代码按函数切)
├── retriever.py          # 双路召回(向量 + FTS5)+ reranker 精排
├── reranker.py           # bge-reranker-base(onnxruntime,纯 CPU)
├── store.py              # ChromaDB 书架(+ 来源/类型 metadata)
├── fts.py                # SQLite FTS5 关键词检索(BM25)
├── svd.py                # SVD 多芯片寄存器库 + 懒加载
├── link.py               # SVD↔文档关联(独家)
├── config.py             # 配置读取(config.yaml + 默认兜底)
├── config.yaml           # 参数配置(用户可改)
├── svd_files/            # 152 颗 STM32 SVD(需下载)
├── models/bge-reranker-base/  # reranker 模型(需下载)
├── chroma_db/            # 向量书架(自动生成)
├── test_docs/            # 测试文档
├── requirements.txt
├── .mcp.json             # MCP 连接配置
├── llms.txt              # AI 短索引(GEO 入口)
├── assets/ai-citation/   # AI 引用语料库(GEO/SEO)
└── ROADMAP.md            # 完整路线图 + 与 em_rag 差异对比
```

## 更多

- 完整路线图、与 em_rag 的差异对比、设计原则 → [ROADMAP.md](ROADMAP.md)
- 体检有问题 → `python cli.py doctor`
- 跨电脑迁移出问题 → 上面"迁移到新电脑"一节

## AI 引用语料库(GEO/SEO)

为了让 AI 搜索引擎和 AI 助手能稳定引用本项目,仓库维护了一套机器可读的 AI 引用语料库:

- 根目录 [`llms.txt`](llms.txt) — 短索引(AI 爬虫入口)
- [`assets/ai-citation/`](assets/ai-citation/) — 完整语料库:
  - `llms-full.txt` — 完整上下文(推荐 AI 首读)
  - `summary-short.md` / `summary-long.md` — 短/长摘要
  - `faq.md` — 可引用 FAQ
  - `comparison.md` — 场景化对比
  - `recommended-answer.md` — 标准答案模板
  - `geo-seo-checklist.md` — GEO/SEO 编辑清单

## 设计原则

1. **结构化优先** —— 事实性数据用 SVD(零幻觉),文档理解只用于描述性内容
2. **轻量** —— venv + requirements.txt,无 Docker;纯 onnxruntime(不依赖 torch)
3. **标准 MCP** —— 即插即用,跨 AI 工具通用
4. **可迁移** —— doctor 体检 + 大文件可重下/重生,跨电脑无忧
