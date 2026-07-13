# emMindRAG ROADMAP

> 嵌入式专用精准 RAG,基于标准 MCP 协议。
> **目标**:在"嵌入式寄存器 / 手册检索"细分场景,做到比 em_rag / RAGFlow 更精准、更实用。

---

## 一、项目定位

- **不是**:通用文档 RAG(那是 em_rag 的主场,不全面追赶)
- **是**:**嵌入式专用精准 RAG** —— 结构化数据(SVD)为主、文档检索为辅、AI 编程助手即插即用(MCP)

> **核心信条**:对寄存器 / 位域这种"事实性数据",用结构化源(SVD)零幻觉查询,远胜任何文档理解(含 RAGFlow)。

---

## 二、当前能力(已完成)

### 文档 RAG 通道(辅助)
- 解析:PDF(PyMuPDF)、Markdown、纯文本、Word(.docx)、EPUB、网页(.html)、**代码(.c/.h/.py/...)**
- 分块:元素感知(表格/代码原子 + **标题章节链**)+ 段落优先 + 代码按函数切 + overlap
- Embedding:默认 chromadb MiniLM(英文,本地);可配 GLM/OpenAI 在线(中文质量强)
- 存储:ChromaDB(向量)+ SQLite FTS5(关键词,BM25 排序)
- 检索:向量 + FTS5(BM25)双路召回 → **bge-reranker-base 重排**(cross-encoder 精排,精度超越点)

### SVD 精确查询通道 ⭐(护城河)
- **152 颗 STM32 全系列** SVD 解析(F0/F1/F2/F3/F4/F7/G0/G4/H5/H7/L0/L1/L4/L5/N6/U0/U5/WB/WBA/WL/C0/MP1)
- 跨芯片寄存器对比(152 颗全系列,独家能力)
- 多芯片大小写不敏感 + 模糊匹配(F103 → stm32f103)
- 懒加载 + pickle 缓存:启动 0.04s / 单芯片查询 0.12s / 跨芯片对比 3.3s
- derivedFrom 继承解析(peripheral + register 两级,SPI2/I2C2/ADC2.SR 等继承来的外设/寄存器数据完整)
- **SVD ↔ 文档关联** ⭐(独家):查寄存器自动关联手册用法,结构化(SVD 零幻觉)+ 非结构化(文档)合一

### MCP 工具集(7 个)
| 工具 | 通道 | 作用 |
|------|------|------|
| `search_docs` | 文档 RAG | 语义+关键词双路检索(支持 code/source 过滤) |
| `list_docs` / `index_doc` | 文档 RAG | 文档管理(index_doc 支持 mineru) |
| `get_register` ⭐ | SVD | 精确查寄存器/位域,零幻觉 |
| `explain_register` ⭐ | SVD↔文档 | 寄存器事实 + 手册/代码关联(独家) |
| `list_peripherals` / `list_chips` ⭐ | SVD | 芯片/外设浏览 |

---

## 三、与 em_rag 完整差异对比

| 维度 | em_rag | emMindRAG | 谁强 |
|------|--------|-------------|------|
| 文档格式 | PDF/MD/代码/txt/网页/Word/EPUB(7种) | PDF/MD/txt/Word/EPUB/网页/**代码**(7种) | **持平** |
| PDF 强解析 | MinerU 本地(全功能) | PyMuPDF + MinerU 在线 API(轻量免登录/精准) | em_rag 略 |
| PDF 时序图提取 | 有(heuristic/hybrid/llm) | 无 | em_rag |
| 元素分类 | 有(element_classifier + context_chain) | 标题章节链 + 表格/代码 + MinerU 结构 | em_rag 略 |
| 分块策略 | 元素感知(表格/代码/标题分别切) | 元素感知(表格/代码原子 + 标题章节链)+ 代码按函数切 | 持平 |
| Embedding 选项 | ONNX 本地 + GLM/OpenAI 在线 | 默认 MiniLM + 可配 GLM/OpenAI 在线 | **持平** |
| 存储架构 | ChromaDB + SQLite FTS5 | ChromaDB + SQLite FTS5(BM25) | **持平** |
| 检索融合(召回) | 向量+关键词+keyword_priority+context_expand | 向量+关键词 + 候选池扩大(精排见 reranker 行) | em_rag 略 |
| 重排序 reranker | ❌ 无 | ✅ bge-reranker-base | **我们** 🏆 |
| **SVD 寄存器查询** | ❌ 无 | ✅ 有(零幻觉) | **我们** 🏆 |
| **跨芯片对比** | ❌ 无 | ✅ 152 颗 STM32 全系列 | **我们** 🏆 |
| MCP 工具数 | 4 | 7(寄存器三件套 + explain 关联) | **我们** 🏆 |
| CLI 命令 | 完整(init/add/search/...) | add/search/list/remove/chips/reg/explain/doctor(8 命令) | 持平(各有侧重) |
| 配置系统 | config.yaml | config.yaml(参数)+ 环境变量(敏感 key) | **持平** |
| 多工程隔离 | mcp_auto 自动发现 | 单工程 | em_rag |
| 健康检查 | doctor/repair | doctor(6 项)+ --fix 重建 | 持平 |
| 多模态 | 时序图存路径(半成品) | 无 | em_rag 略 |
| **SVD↔文档关联** | ❌ 无 | ✅ explain_register | **我们** 🏆 |

**计分**:em_rag 主场(文档生态 / 工程化)强 **6 项**;我们主场(SVD / 寄存器 / reranker / 关联)强 **5 项**,**持平 7 项**(文档格式 / 分块 / CLI / 健康检查 / Embedding / 存储架构 / 配置)。其中 reranker 是文档精度上的**反超**,SVD / 跨芯片 / SVD↔文档关联是 em_rag **完全没有的差异化**——在我们定位的"嵌入式寄存器/手册检索"细分场景全面领先。

---

## 四、超越策略:守 / 补 / 超

| 类别 | 含义 | 对应阶段 |
|------|------|----------|
| 🛡️ **守** | 放大 SVD 护城河,em_rag 追不上 | 阶段 1 |
| 🚀 **超** | 做双方都没有的(reranker/创新) | 阶段 2、5 |
| 🔧 **补** | 只补高价值短板,不全补 | 阶段 3、4 |

**顺序原则**:先守 → 再超 → 再补 → 最后创新。**把差异化放前面,把追赶放后面**——每一步都在扩大领先,而不是在补作业。

---

## 五、路线图(5 阶段)

### 🛡️ 阶段 1:深化 SVD 护城河【已完成】`status: done ✅`
- [x] **1.1 SVD 枚举值解析** ✅ —— 解析 `enumeratedValues`,位域不只"位3宽3",还有"00=输入/01=输出/10=复用"。精度再上一阶。难度:低
- [x] **1.2 扩到全部芯片系列** ✅ —— 从 `tinygo-org/stm32-svd` 拉满 152 颗(含 F0/F2/F3/F7/G0/G4/H5/H7/L0/L4/L5/N6/U0/WB/WBA/WL/C0/MP1)。并升级为懒加载 + pickle 缓存,启动 40s→0.04s。难度:低
- [x] **1.3 derivedFrom 继承解析** ✅ —— peripheral 级(SPI2←SPI1)+ register 级(ADC2.SR←ADC1.SR)两轮继承,支持链式与防环。继承外设/寄存器现数据完整。难度:中

### 🚀 阶段 2:加 reranker(超越点)【已完成】`status: done ✅`
- [x] **2.1 bge-reranker-base 重排序** ✅ —— 双路召回后 cross-encoder 精排(量化版 280MB,纯 onnxruntime+tokenizers 无需 torch),懒加载+降级。**em_rag/RAGFlow 无重排,文档精度反超**。难度:中

### 🔧 阶段 3:补文档处理【已完成】`status: done ✅`
- [x] **3.1 多格式解析** ✅ —— Word(.docx,python-docx,段落+表格)/ EPUB(ebooklib,章节正文)/ 网页(.html,beautifulsoup4,去脚本样式后提正文)。难度:中
- [x] **3.2 智能分块** ✅ —— 元素感知:表格/代码块识别为原子单元(不切断),普通段落按 size+overlap;标题随段落。难度:中-高
- [x] **3.3 可选 MinerU** ✅ —— 用 MinerU 在线 API(免本地重依赖):无 token 走 Agent 轻量 API(10MB/20页),配 MINERU_TOKEN 走精准 API(200MB/200页,vlm 模型)。输出 markdown,失败降级 PyMuPDF。难度:中

### 🔧 阶段 4:补工程化【已完成】`status: done ✅`
- [x] **4.1 CLI 命令** ✅ —— cli.py 八个子命令:add / search / list / remove / chips / reg / explain / doctor(argparse,无新依赖)。难度:中
- [x] **4.2 config.yaml 配置系统** ✅ —— config.py 读 config.yaml(chunk / search / reranker / mineru 参数),敏感 key 走环境变量。各模块走 config.getd,doctor [9] 显示。难度:中
- [x] **4.3 doctor 健康检查 + repair** ✅ —— cli.py doctor:9 项体检(Python 库 / SVD / reranker / 书架 / 核心模块 / MCP 配置 / MinerU / Embedding / config)+ --fix 自动重建 SVD 缓存。难度:中

### 🚀 阶段 5:创新(独家)【进行中】`status: in progress`(5.1 ✅)
- [x] **5.1 SVD ↔ 文档关联** ✅ —— link.py:查寄存器时合并 SVD 精确事实(零幻觉)+ 手册用法(文档检索+reranker)。MCP 工具 explain_register + CLI explain。难度:高
- [ ] **5.2 多模态时序图** —— VLM 描述图片,超越 em_rag"只存路径"的半成品。难度:高

---

## 六、技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | |
| MCP | `mcp[cli]` (FastMCP) | 标准协议,跨 AI 工具 |
| 向量库 | ChromaDB | 含默认 embedding |
| PDF 解析 | PyMuPDF | |
| SVD 解析 | Python 标准库 `xml.etree` | 零额外依赖 |
| SVD 数据源 | tinygo-org/stm32-svd | 社区从 ST 官方提取 |
| 隔离 | venv(不用 Docker) | 轻量、可迁移 |

---

## 七、项目结构

```
emMindRAG/
├── server.py             # MCP 入口(7 个工具)
├── cli.py               # 命令行工具(add/search/list/remove/chips/reg/explain/doctor)
├── parser.py             # 文档解析(PDF/MD/txt/Word/EPUB/网页/代码 7 种;+ MinerU 在线 API)
├── chunker.py            # 智能分块(表格/代码原子 + 标题章节链 + 代码按函数切)
├── retriever.py          # 双路召回(向量 + FTS5)+ bge-reranker 精排
├── reranker.py           # bge-reranker-base(onnxruntime,纯 CPU,无需 torch)
├── store.py              # ChromaDB 书架(+ 来源/类型 metadata,可配在线 embedding)
├── fts.py               # SQLite FTS5 关键词检索(BM25)
├── svd.py                # SVD 多芯片寄存器库 + 懒加载 + derivedFrom 继承 ⭐
├── link.py              # SVD↔文档关联(独家)⭐
├── config.py            # 配置读取(config.yaml + 默认兜底)
├── config.yaml          # 参数配置(用户可改:chunk/search/reranker/mineru)
├── svd_files/            # 152 颗 STM32 SVD(340M)+ _cache.pkl(130M 懒加载缓存)
├── models/bge-reranker-base/  # reranker 模型(280M,onnx 量化版)
├── chroma_db/            # 向量书架(自动生成)
├── test_docs/            # 测试文档
├── requirements.txt
├── .mcp.json             # MCP 连接配置(venv python 绝对路径)
├── README.md            # 项目说明 + 安装/用法/迁移指南
├── .gitignore           # 忽略大文件(SVD/模型/缓存/书架,可重下/重生)
└── ROADMAP.md            # 本文件
```

---

## 八、设计原则

1. **结构化优先** —— 事实性数据用 SVD(零幻觉),文档理解只用于描述性内容
2. **轻量** —— venv + requirements.txt,不依赖 Docker;迁移体积 ~740M(SVD 340M + reranker 280M + pickle 缓存 130M + 书架);启动秒级(懒加载)
3. **标准 MCP** —— 即插即用,Claude Code / Cursor / Codex 通用
4. **护城河优先于补短板** —— 先扩大 SVD 领先,再补 em_rag 强项

---

## 九、进度日志

- **2026-07-01**:完成 M0~M7 + SVD 多芯片系统。32 颗 STM32 跨芯片对比上线。当前在嵌入式寄存器查询细分场景已领先 em_rag / RAGFlow。下一步:阶段 1.2(扩到全部 152 颗芯片)。
- **2026-07-01(续)**:✅ 阶段 1.1 完成 —— SVD 枚举值解析上线。位域现带精确枚举(F1 MODE: 0=Input/1=Output/2=Output2/3=Output50;F4 MODER: 0=Input/1=Output/2=Alternate/3=Analog)。机器可读精度,em_rag/RAGFlow 拿不到。下一步:1.2 扩到全部 152 颗芯片。
- **2026-07-01(续2)**:✅ 阶段 1.2 完成 —— SVD 从 32 颗扩到 **152 颗全系列**(新增 F0/F2/F3/F7/G0/G4/H5/H7/L0/L4/L5/N6/U0/WB/WBA/WL/C0/MP1,含双核 H7 的 cm4/cm7 两个核)。加载架构升级为**懒加载**:启动建索引 0.04s、单芯片查询 0.12s、pickle 缓存让跨芯片对比 40s→3.3s。跨芯片对比覆盖面 ×5(32→152 颗)。注:HRTIM 等复合外设在 SVD 中按子外设命名(如 `HRTIM_Master`/`HRTIM_TIMA`),查子外设即可。下一步:1.3 derivedFrom 继承解析。
- **2026-07-01(续3)**:✅ 阶段 1.3 完成 —— derivedFrom 继承解析上线。两轮解析:peripheral 级(SPI2 继承 SPI1,补全寄存器组)+ register 级(ADC2.SR 继承 ADC1.SR,补全位域),支持链式继承(A→B→C)与环保护。验证:SPI2/I2C2/GPIOB 寄存器数与源一致,ADC2.SR 位域 0→5。pickle 缓存加版本号(v2),解析逻辑变更自动失效。**🎉 阶段 1(深化 SVD 护城河)三项全部完成**,下一步进入阶段 2(bge-reranker 超越点)。
- **2026-07-01(续4)**:✅ 阶段 2.1 完成 —— bge-reranker-base 重排序上线。双路召回后加 cross-encoder 精排(Xenova 量化版 280MB,纯 onnxruntime+tokenizers 手写加载,无需 torch),懒加载 + 降级(模型缺失走原双路)。验证:CPHA 相关文档 +4.9 分 vs 无关 -10 分,中文区分精准。绕过 huggingface_hub 镜像来源校验问题(curl 直下 + 本地 onnx 加载)。**🎉 阶段 2(超越点)完成,文档检索精度反超 em_rag/RAGFlow**。
- **2026-07-02**:✅ 阶段 3.1 完成 —— 多格式解析上线。新增 Word(.docx,段落+表格)、EPUB(章节正文)、网页(.html,去 script/style/nav 后提正文)。python-docx + ebooklib + beautifulsoup4(均轻量,共 ~5M)。验证:三种格式构造测试文件解析均正确,html 干扰元素有效剔除。文档格式从 3 种扩到 6 种。下一步:3.2 智能分块。
- **2026-07-02(续)**:✅ 阶段 3.2 完成 —— 智能分块上线。chunker 先识别单元类型(表格 / 代码块 / 普通段落),表格和代码作为**原子单元**整体保留(绝不在中间被腰斩),普通段落沿用 size + overlap。验证:6 行寄存器表、代码块均完整落入同一块。纯 stdlib 实现,无新依赖。下一步:3.3 可选 MinerU(扫描件,依赖重,建议按需)。
- **2026-07-02(续2)**:✅ 阶段 4.1 完成 —— CLI 命令行工具上线(cli.py)。6 个子命令:add(索引,支持全 6 种格式)/ search(双路+reranker)/ list(按来源分组)/ remove(--source / --all)/ chips(芯片清单)/ reg(寄存器查询)。顺手修 store 的 id 覆盖隐患(id 从 count 递增 + 记录来源 metadata)。验证:add→list→search→remove 完整闭环,书架可恢复。doctor 留 4.3。
- **2026-07-02(续3)**:✅ 阶段 4.3 完成 —— doctor 健康检查上线(cli.py doctor)。6 项体检(Python 库 / SVD 芯片库 / reranker 模型 / 文档书架 / 核心模块导入 / MCP 配置)+ --fix 自动重建 SVD 缓存。验证:体检全绿(9 库 / 152 颗 / 266M 模型 / 3434 块 / 6 模块),--fix 重建 123M/39s。4.2 config.yaml 暂缓(路径已自动定位)。**🎉 阶段 4(工程化)基本完成**,下一站阶段 5 创新(SVD↔文档关联)。
- **2026-07-02(续4)**:✅ 阶段 5.1 完成 —— SVD↔文档关联上线(link.py)。查寄存器时合并两部分:SVD 精确事实(位域/地址/枚举,零幻觉)+ 手册用法片段(文档检索 + reranker 重排)。新增 MCP 工具 explain_register(工具数 6→7)+ CLI explain 命令。**结构化 + 非结构化结合,em_rag/RAGFlow 都没有的独家能力**。验证:f407 GPIOA>MODER 的 SVD 事实 + U575 手册 GPIO 寄存器章节关联呈现。
- **2026-07-03**:✅ 文档格式追平 em_rag —— 方案 A 补代码格式(.c/.h/.cpp/.s/.py/.js/.java/.rs/.go 等,代码本质是文本,直读)+ 方案 B 代码智能分块(按"顶级行 + 前空行"边界切,不切断函数/类)。验证:.c 测试文件 gpio_init/spi_init 完整保留(普通分块会拆 2 次)。文档格式 6→7 种,该维度从「落后」追到「持平」(计分:em_rag 10→9,持平 3→4)。
- **2026-07-03(续2)**:✅ 收尾 polish —— 新增 README.md(项目说明 + 安装/用法 + 迁移指南)+ .gitignore(忽略 SVD/模型/缓存/书架等大文件,均可重下或自动生成)。**项目达到可分享、可迁移、可上手状态**。
- **2026-07-03(续3)**:✅ 3.3 MinerU 接入(在线 API 版)—— 不装本地重依赖(torch + 模型几 GB),改用 mineru.net 在线 API:无 token 走 Agent 轻量 API(免登录,10MB/20页),配 MINERU_TOKEN 走精准 API(200MB/200页,vlm 模型,输出 zip 含 markdown+json)。输出结构化 markdown(标题/表格保留),失败自动降级 PyMuPDF。实测:U575 手册前 3 页 → 2092 字符 markdown。PDF 强解析从「无」追到「有 API 方案」,差距大缩。
- **2026-07-06**:✅ Embedding 在线配置 —— store 加 _HttpEmbedding(继承 chromadb.EmbeddingFunction),支持 EMBEDDING_PROVIDER=glm/openai + EMBEDDING_API_KEY。默认仍 MiniLM(本地快),配 key 切在线 GLM/OpenAI(中文质量↑)。doctor 加 [8] Embedding 检测。Embedding 维度从「em_rag 强」追到「持平」(计分 em_rag 9→8,持平 4→5)。
- **2026-07-06(续)**:✅ FTS5 关键词检索 —— fts.py 用 SQLite FTS5(BM25 + 倒排索引)替代手写 2-gram。chromadb 向量 + FTS5 关键词双引擎(同 em_rag)。验证:"SPI CPHA" / "波特率" BM25 精准排序(代码注释排前,稀有词加权),中文(unicode61)+ type 过滤正常,3466 块自动迁移。存储架构从「em_rag 强」追到「持平」(计分 em_rag 8→7,持平 5→6)。
- **2026-07-08**:✅ 4.2 config.yaml 配置系统 —— config.py 读 config.yaml(chunk / search / reranker / mineru 参数),敏感 key(MINERU_TOKEN / EMBEDDING_* 等)走环境变量。各模块(chunker / retriever / reranker / parser)走 config.getd,doctor 加 [9] 配置显示。用户改 config.yaml 重启即生效。**🎉 阶段 4(工程化)全部完成**(4.1 CLI + 4.2 config + 4.3 doctor)。配置系统从「em_rag 强」追到「持平」(计分 em_rag 7→6,持平 6→7)。
- **2026-07-08(续2)**:✅ 元素分类(标题上下文链)—— chunker 识别 markdown # 标题,遇新标题先封块(不跨章节),每块带〔章节〕标签。验证:GPIO 块标〔GPIO 寄存器〕、MODER 块标〔MODER 寄存器〕,检索结果自带章节定位。元素分类维度从「em_rag 强」缩到「em_rag 略」(我们有标题链 + 表格/代码 + MinerU 结构,em_rag 是全分类器)。
- **2026-07-13**:✅ 改名 em-rag-mini → **emMindRAG** + 上 GitHub —— 全局改名(目录 / 文件内容 / .mcp.json / venv activate 脚本);修 .gitignore 行内注释问题(此前导致大文件未排除);git init + 首次提交 + push 到 https://github.com/darkChench/emMindRAG。仓库 23 文件(代码/文档/配置),大文件(SVD 340M / 模型 280M / 缓存 / 书架)按 .gitignore 忽略,clone 后照 README 重下。
