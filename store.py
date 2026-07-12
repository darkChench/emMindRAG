"""
store.py —— 书架(向量数据库)模块
路径基于脚本位置,不依赖启动时的工作目录。
"""
import os
import chromadb

# 书架目录固定在 store.py 同级 —— 不管从哪里启动都能找到
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")


class _HttpEmbedding(chromadb.EmbeddingFunction):
    """在线 embedding(GLM/OpenAI 兼容)的 chromadb EmbeddingFunction。
    配 EMBEDDING_PROVIDER + EMBEDDING_API_KEY 启用;不配则用 chromadb 默认 MiniLM。"""
    def __init__(self, url, key, model, batch_size=32):
        super().__init__()
        self.url, self.key, self.model, self.batch_size = url, key, model, batch_size

    def __call__(self, input, **kwargs):
        import requests
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        vecs = []
        for i in range(0, len(input), self.batch_size):
            batch = input[i:i + self.batch_size]
            r = requests.post(self.url, headers=headers,
                              json={"model": self.model, "input": batch}, timeout=120)
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda x: x["index"])   # 保证顺序
            vecs.extend(d["embedding"] for d in data)
        return vecs


def _get_embedding_function():
    """按环境变量返回在线 embedding(GLM/OpenAI);没配返回 None(用 chromadb 默认 MiniLM)。"""
    provider = os.environ.get("EMBEDDING_PROVIDER", "").lower().strip()
    key = os.environ.get("EMBEDDING_API_KEY", "").strip()
    if not provider or not key:
        return None
    if provider == "glm":
        return _HttpEmbedding("https://open.bigmodel.cn/api/paas/v4/embeddings", key,
                              os.environ.get("EMBEDDING_MODEL") or "embedding-3")
    if provider == "openai":
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/embeddings"
        return _HttpEmbedding(base, key, os.environ.get("EMBEDDING_MODEL") or "text-embedding-3-small")
    return None


def get_collection():
    client = chromadb.PersistentClient(path=_DB_PATH)
    ef = _get_embedding_function()
    if ef:
        return client.get_or_create_collection(name="docs", embedding_function=ef)
    return client.get_or_create_collection(name="docs")


def add_chunks(chunks: list[str], source: str = "", is_code: bool = False):
    """把一批文档块放进书架(chromadb 向量 + FTS5 关键词,双引擎)。
    id 从现有数量递增(多次 add 不会互相覆盖);source 记录来源;
    is_code 打 type=code 标签,供 search --code 过滤。"""
    collection = get_collection()
    start = collection.count()
    ids = [f"id_{start + i}" for i in range(len(chunks))]
    typ = "code" if is_code else "doc"
    metas = [{"source": source, "type": typ} for _ in chunks]
    collection.upsert(documents=chunks, ids=ids, metadatas=metas)
    import fts
    fts.add(ids, chunks, source=source, typ=typ)   # 同步 FTS5 索引


def count() -> int:
    return get_collection().count()


def sources() -> dict:
    """返回 {来源文件: 块数}"""
    data = get_collection().get(include=["metadatas"])
    counts = {}
    for m in data.get("metadatas", []):
        s = (m or {}).get("source", "(未知来源)")
        counts[s] = counts.get(s, 0) + 1
    return counts


def remove_source(source: str) -> int:
    """删除某来源的所有块(chromadb + FTS5),返回删除条数"""
    collection = get_collection()
    data = collection.get(include=["metadatas"])
    ids = [i for i, m in zip(data["ids"], data.get("metadatas", []))
           if (m or {}).get("source") == source]
    if ids:
        collection.delete(ids=ids)
    import fts
    fts.remove_by_source(source)
    return len(ids)


def clear():
    """清空整个书架(chromadb + FTS5)"""
    client = chromadb.PersistentClient(path=_DB_PATH)
    try:
        client.delete_collection("docs")
    except Exception:
        pass
    import fts
    fts.clear()
