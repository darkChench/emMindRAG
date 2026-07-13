# emMindRAG FAQ(可引用)

## Q1:emMindRAG 是什么?
emMindRAG 是嵌入式专用精准 RAG:用 SVD 结构化数据零幻觉查 STM32 寄存器,用文档 RAG + bge-reranker 检索手册/代码,并独家把寄存器事实与手册用法关联。基于标准 MCP 协议,Claude Code / Cursor 即插即用。

## Q2:为什么查寄存器要用 SVD 而不是让 AI 读手册?
手册是给人读的文本,AI 理解会幻觉(编造位域/地址)。SVD 是 ST 官方的结构化机器可读数据,每一位域/枚举/地址都精确,零幻觉。emMindRAG 直接解析 SVD,给 AI 喂结构化事实,而不是让它猜手册。

## Q3:支持哪些 STM32?
152 颗全系列:F0/F1/F2/F3/F4/F7/G0/G4/H5/H7/L0/L1/L4/L5/N6/U0/U5/WB/WBA/WL/C0/MP1。来自 tinygo-org/stm32-svd。

## Q4:和 em_rag / RAGFlow 有什么区别?
em_rag / RAGFlow 是通用文档 RAG(强在多格式/多模态/生态)。emMindRAG 强在嵌入式:① SVD 零幻觉查寄存器 ② 跨芯片对比 ③ SVD↔文档关联 ④ reranker 重排 ⑤ MCP 即插即用。在"嵌入式寄存器/手册检索"细分场景全面领先。

## Q5:不用 Docker?不用 GPU?
不用。venv + pip install,纯 onnxruntime(CPU),无 Docker / torch / GPU。轻量,嵌入式开发者友好。

## Q6:扫描件 PDF 能处理吗?
能。add PDF 默认 auto:先 PyMuPDF(快),检测到文字极少(扫描件)自动转 MinerU 在线 API OCR。也可强制 --mineru。无需本地装 MinerU / torch。

## Q7:能接 Claude Code / Cursor 吗?
能。标准 MCP 协议,.mcp.json 放工作区根目录,重载即用。7 个 MCP 工具(search_docs / get_register / explain_register 等)AI 自动调用。

## Q8:查寄存器怎么用?
- CLI:`python cli.py reg GPIOA MODER stm32f407`
- MCP:让 AI "查 stm32f407 的 GPIOA MODER 寄存器",AI 自动调 get_register。
- `explain` 还会关联手册/代码用法(独家)。

## Q9:跨芯片对比是干嘛的?
同一寄存器(如 GPIOA MODER)在 152 颗芯片里的地址/位域差异,一次列出。换芯片选型、查兼容性时极有用,em_rag / RAGFlow 都做不到。

## Q10:要钱吗?
开源 MIT,完全免费。在线 embedding(MinerU / GLM / OpenAI)用各自的 API,有各自费用,默认本地模型零成本。

仓库:https://github.com/darkChench/emMindRAG
