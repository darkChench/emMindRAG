"""fts.py —— SQLite FTS5 关键词检索(BM25 排序),替代手写 2-gram。
和 chromadb 配合:chromadb 管向量(语义),FTS5 管关键词(字面),双引擎。
无新依赖(Python 标准库 sqlite3,FTS5 是 SQLite 自带扩展)。"""
import os
import re
import sqlite3

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db", "fts.db")


def _conn():
    os.makedirs(os.path.dirname(_DB), exist_ok=True)
    conn = sqlite3.connect(_DB)
    # id/source/type 不索引(UNINDEXED),只 content 建倒排;source/type 供 WHERE 过滤
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5("
        "id UNINDEXED, content, source UNINDEXED, type UNINDEXED, tokenize='unicode61')"
    )
    return conn


def _sanitize(q):
    """去掉 FTS5 MATCH 的特殊字符(* " ( ) 等),避免语法报错。"""
    return re.sub(r'[^\w一-鿿]+', ' ', q).strip() or '?'


def add(ids, docs, source="", typ="doc"):
    """批量建索引(id 对齐 chromadb 的 id)"""
    conn = _conn()
    rows = [(i, d, source, typ) for i, d in zip(ids, docs)]
    conn.executemany("INSERT INTO docs_fts(id, content, source, type) VALUES(?,?,?,?)", rows)
    conn.commit(); conn.close()


def remove_by_source(source):
    conn = _conn()
    conn.execute("DELETE FROM docs_fts WHERE source=?", (source,))
    conn.commit(); conn.close()


def clear():
    if os.path.exists(_DB):
        os.remove(_DB)


def search(query, top_k=10, source=None, typ=None):
    """FTS5 BM25 查询,返回 [{id, text, score}],score 越小越相关(BM25 返回负数)。"""
    conn = _conn()
    sql = "SELECT id, content, bm25(docs_fts) FROM docs_fts WHERE content MATCH ?"
    params = [_sanitize(query)]
    if source:
        sql += " AND source = ?"; params.append(source)
    if typ:
        sql += " AND type = ?"; params.append(typ)
    sql += " ORDER BY bm25(docs_fts) LIMIT ?"; params.append(top_k)
    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        rows = []    # query 语法兜底
    conn.close()
    return [{"id": r[0], "text": r[1], "score": round(r[2], 3)} for r in rows]


def ensure_synced(collection):
    """FTS5 与 chromadb 同步:行数不等则从 chromadb 全量重建(用于首次/迁移)。"""
    conn = _conn()
    fts_count = conn.execute("SELECT COUNT(*) FROM docs_fts").fetchone()[0]
    if fts_count != collection.count():
        conn.execute("DELETE FROM docs_fts")
        data = collection.get(include=["documents", "metadatas"])
        rows = [
            (i, d, (m or {}).get("source", ""), (m or {}).get("type", "doc"))
            for i, d, m in zip(data["ids"], data["documents"], data.get("metadatas") or [])
        ]
        conn.executemany("INSERT INTO docs_fts(id, content, source, type) VALUES(?,?,?,?)", rows)
        conn.commit()
        print(f"[i] FTS5 已从 chromadb 同步({len(rows)} 块)")
    conn.close()
