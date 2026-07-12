"""
retriever.py —— 检索模块(向量 + 关键词 双路召回 + reranker 精排)
支持 where 按 metadata 过滤:{"type":"code"} 只搜代码,{"source":"x.pdf"} 只搜某文档。
"""
import re
from store import get_collection


# ============ 向量检索(M5,按"意思"找)============
def search(query: str, top_k: int = 3, where: dict = None) -> list[dict]:
    """向量语义检索(where 可按 metadata 过滤范围)"""
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=top_k, where=where)
    docs = results["documents"][0]
    distances = results["distances"][0]
    return [{"text": d, "distance": round(dist, 3)} for d, dist in zip(docs, distances)]


# ============ 关键词检索(M7,按"字面"找)============
def _tokenize(text: str) -> set:
    """把文本切成关键词片段:英文按整词,中文按2字组合。"""
    tokens = set()
    for w in re.findall(r"[a-zA-Z0-9]+", text.lower()):   # 英文/数字:整词
        if len(w) >= 2:
            tokens.add(w)
    for seg in re.findall(r"[一-龥]+", text):      # 中文段:2字滑窗
        for i in range(len(seg) - 1):
            tokens.add(seg[i:i + 2])
    return tokens


def keyword_search(query: str, top_k: int = 3, where: dict = None) -> list[dict]:
    """关键词检索(SQLite FTS5 + BM25 排序,替代手写 2-gram)。
    where 支持 {"source":"x"} / {"type":"code"} 过滤。"""
    import fts
    from store import get_collection
    fts.ensure_synced(get_collection())   # 首次或迁移时从 chromadb 同步 FTS5
    source = where.get("source") if where else None
    typ = where.get("type") if where else None
    results = fts.search(query, top_k=top_k, source=source, typ=typ)
    return [{"text": r["text"], "matches": 1} for r in results]   # FTS5 已按 BM25 排序


# ============ 双路召回 + reranker 精排(最终给 AI 用的入口)============
def search_combined(query: str, top_k: int = None, where: dict = None) -> list[dict]:
    """向量 + 关键词 双路召回 → reranker 精排。
    where 过滤召回范围(如只搜代码);reranker 不可用时降级为双路融合顺序。"""
    import config
    if top_k is None: top_k = config.getd("search.top_k")
    pool_k = max(top_k * config.getd("search.pool_factor"), 12)
    seen, combined = set(), []
    for item in keyword_search(query, pool_k, where):          # 关键词命中优先
        if item["text"] not in seen:
            seen.add(item["text"])
            combined.append({"text": item["text"], "via": "关键词"})
    for item in search(query, pool_k, where):                  # 向量补充
        if item["text"] not in seen:
            seen.add(item["text"])
            combined.append({"text": item["text"], "via": "语义"})

    # reranker 精排:cross-encoder 把 query+候选一起打分(精度超越点)
    try:
        from reranker import rerank
        ranked = rerank(query, [c["text"] for c in combined], top_k=top_k)
        if ranked:
            return [{"text": r["text"], "via": f"重排({r['score']})"} for r in ranked]
    except Exception:
        pass
    return combined[:top_k]                                     # 降级:双路融合顺序
