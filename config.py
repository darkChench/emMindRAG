"""config.py —— 集中配置(读 config.yaml,留空/无文件则用代码默认)。
参数走 yaml(用户可改),敏感 key 走环境变量(见 config.yaml 注释)。"""
import os

_DEFAULTS = {
    "chunk": {"size": 300, "overlap": 1, "code_size": 400, "code_overlap": 2},
    "search": {"top_k": 3, "pool_factor": 4},
    "reranker": {"model": "BAAI/bge-reranker-base"},
    "mineru": {"language": "ch"},
}

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
_cfg = None


def _load():
    """读 config.yaml(没文件或没装 pyyaml 则空 dict,用 _DEFAULTS)。"""
    global _cfg
    if _cfg is not None:
        return _cfg
    cfg = {}
    if os.path.exists(_PATH):
        try:
            import yaml
            with open(_PATH, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            pass
    _cfg = cfg
    return cfg


def get(path, default=None):
    """get("chunk.size") → yaml 有则用,否则 default。"""
    val = _load()
    for k in path.split("."):
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val


def getd(path):
    """getd("chunk.size") → yaml 有则用,否则 _DEFAULTS 默认。"""
    d = _DEFAULTS
    for p in path.split("."):
        d = d.get(p) if isinstance(d, dict) else None
        if d is None:
            break
    return get(path, d)
