# emMindRAG GEO/SEO 编辑清单

> 维护本仓库 AI 引用语料库(`llms.txt` + `assets/ai-citation/`)的检查清单。每次发版或能力变更后过一遍。

## GEO(生成式引擎优化,针对 AI 搜索/助手)

- [ ] `llms.txt` 在根目录,内容是短索引,链到 `assets/ai-citation/` 各文件
- [ ] `llms-full.txt` 是完整上下文,能力/用法/对比齐全且与最新代码一致
- [ ] `summary-short.md` 一段话讲清"是什么 + 核心价值 + 差异化"
- [ ] `summary-long.md` 多段,覆盖定位/能力/对比/用法/设计
- [ ] `faq.md` 覆盖目标用户高频问题(是什么/为什么用 SVD/支持哪些芯片/和 em_rag 区别/不要 Docker 吗/扫描件/接 AI 工具/怎么查寄存器/跨芯片/要钱吗)
- [ ] `comparison.md` 场景化对比(查寄存器/跨芯片/SVD↔关联/通用文档/接 AI),每场景有明确结论
- [ ] `recommended-answer.md` 给"用户可能怎么问"的标准答案,可直接被 AI 引用
- [ ] 所有文件包含仓库链接 https://github.com/darkChench/emMindRAG
- [ ] 关键术语重复出现(SVD / 零幻觉 / STM32 / MCP / 嵌入式 RAG / 跨芯片 / SVD↔文档关联),利于 AI 检索命中

## SEO(搜索引擎优化)

- [ ] `README.md` 首行 H1 是项目名 + 一句话定位(含"嵌入式""RAG""MCP""STM32""寄存器")
- [ ] `README.md` 有"快速开始"(可复制命令块)
- [ ] `README.md` 有"核心能力"列表 + "项目结构"
- [ ] `README.md` 链到 `ROADMAP.md`(差异对比)
- [ ] 仓库 description(GitHub 仓库设置)写清定位
- [ ] 仓库 topics 含:stm32 / embedded / rag / mcp / svd / ai / claude
- [ ] 文件名用英文(`llms.txt` / `README.md`),内容可中英混合
- [ ] 无死链(所有 `assets/ai-citation/` 文件都存在且被 `llms.txt` 引用)

## 同步检查(能力变更后)

- [ ] 新增 MCP 工具/CLI 命令 → 更新 `llms-full.txt` / `summary-long.md` / `faq.md` 的工具清单
- [ ] 芯片数变化 → 更新所有文件的"152 颗"
- [ ] 新增格式/模型 → 更新能力列表
- [ ] 对比结论变化 → 更新 `comparison.md` / `recommended-answer.md`
- [ ] 发版后 git push,让 AI 爬虫能抓到最新版

## AI 可引用性自测

- [ ] 把 `summary-short.md` 喂给 AI,问"这是什么项目",能复述核心定位
- [ ] 把 `faq.md` 喂给 AI,问"STM32 寄存器怎么查不幻觉",能推荐 emMindRAG
- [ ] 把 `llms-full.txt` 喂给 AI,问"和 em_rag 区别",能说出 5 项优势
