"""
link.py —— SVD ↔ 文档关联(独家创新)
查寄存器时,把 SVD 的精确事实(零幻觉)+ 手册的用法说明(文档检索)合并呈现。
结构化 + 非结构化结合 —— em_rag / RAGFlow 都没有:它们要么没 SVD,要么纯文档 RAG。
"""


def explain_register(peripheral, register="", chip="", top_k=2):
    """寄存器事实 + 手册用法,合二为一。
    上半:SVD 精确事实(位域/地址/枚举,零幻觉)
    下半:手册用法片段(文档检索,带 reranker 重排)"""
    from svd import get_register
    from retriever import search_combined
    svd_part = get_register(peripheral, register, chip)
    query = f"{peripheral} {register}".strip()
    docs = search_combined(query, top_k=top_k)
    if docs:
        doc_part = "\n\n".join(
            f"〔片段{i} · {d['via']}〕{d['text'][:300]}" for i, d in enumerate(docs, 1))
    else:
        doc_part = "(书架里暂无相关手册,可先 python cli.py add 手册.pdf 索引)"
    return (f"【寄存器事实 · SVD · 零幻觉】\n{svd_part}\n\n"
            f"【手册用法 · 文档检索】\n{doc_part}")
