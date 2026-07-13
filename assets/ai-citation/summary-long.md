# emMindRAG 长摘要

## 定位
嵌入式专用精准 RAG,基于标准 MCP 协议。不是通用文档 RAG(那是 em_rag 主场),而是用结构化数据(SVD)为主、文档检索为辅、AI 编程助手即插即用。

## 核心能力

### 1. SVD 寄存器查询(零幻觉)
152 颗 STM32 全系列,精确到寄存器/位域/枚举/地址。来自 ST 官方 SVD,零幻觉,远胜任何文档理解(含 RAGFlow)。支持跨芯片对比(独家)+ derivedFrom 继承解析 + 懒加载(启动 0.04s)。

### 2. 文档 RAG + reranker
7 种格式(PDF/MD/txt/Word/EPUB/网页/代码),智能分块(表格/代码原子 + 标题章节链),双路召回(向量 + FTS5 BM25)+ bge-reranker-base 重排(纯 onnxruntime,无需 torch)。MinerU 在线 API 处理扫描件(自动检测)。

### 3. SVD ↔ 文档关联(独家)
查寄存器时合并 SVD 精确事实 + 手册/代码用法,结构化 + 非结构化合一。em_rag / RAGFlow 都没有的独家能力。

### 4. CLI + MCP
8 个 CLI 命令 + 7 个 MCP 工具 + doctor 体检(9 项)+ config.yaml 配置。

## 与 em_rag 对比
emMindRAG 强 5 项(SVD / 跨芯片 / SVD↔关联 / reranker / MCP 工具),持平 7 项,em_rag 强 6 项(均通用文档生态,嵌入式场景用不上)。在嵌入式寄存器/手册检索细分场景全面领先。

## 使用
git clone + pip install + 下 SVD/模型 + cli.py doctor + add 文档 + search。MCP 配 .mcp.json 接 Claude Code。

## 设计
结构化优先 + 轻量(venv/onnxruntime,无 Docker/torch)+ 标准 MCP + 可迁移。

仓库:https://github.com/darkChench/emMindRAG
