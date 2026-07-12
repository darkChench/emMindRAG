"""
reranker.py —— bge-reranker-base 重排序(cross-encoder,精度超越点)
检索出候选后,用 cross-encoder 把 query 和每个候选一起打分重排,精度大幅提升。
纯 onnxruntime + tokenizers 实现(无需 torch),模型用 Xenova/bge-reranker-base 量化版(~280MB)。
懒加载:首次重排才加载模型;模型文件缺失/出错时优雅降级(返回 None),上层走原双路融合。

em_rag / RAGFlow 没有决赛级重排,这是文档检索精度的超越点。

模型文件放 models/bge-reranker-base/(model.onnx + tokenizer.json + config.json)。
下载(国内用 hf-mirror 镜像,curl 直接下,绕开 huggingface_hub 的来源校验):
    curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/onnx/model_quantized.onnx -o models/bge-reranker-base/model.onnx
    curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/tokenizer.json -o models/bge-reranker-base/tokenizer.json
    curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/config.json -o models/bge-reranker-base/config.json
"""
import os
import numpy as np

import config
_DIR_NAME = (os.environ.get("RERANKER_MODEL") or config.getd("reranker.model")).split("/")[-1]
_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", _DIR_NAME)
_MAX_LEN = 512   # XLM-R 最长 512 token

_SESSION = None    # onnxruntime InferenceSession
_TOKENIZER = None  # tokenizers.Tokenizer
_LOAD_ERROR = None


def _load():
    """懒加载 onnx 模型 + tokenizer。成功返回 True,失败记录原因并返回 False。"""
    global _SESSION, _TOKENIZER, _LOAD_ERROR
    if _SESSION is not None:
        return True
    if _LOAD_ERROR is not None:
        return False
    onnx = os.path.join(_MODEL_DIR, "model.onnx")
    tok = os.path.join(_MODEL_DIR, "tokenizer.json")
    if not os.path.exists(onnx) or not os.path.exists(tok):
        _LOAD_ERROR = f"模型文件缺失,需下载到 {_MODEL_DIR}"
        return False
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer
        _SESSION = ort.InferenceSession(onnx, providers=["CPUExecutionProvider"])
        _TOKENIZER = Tokenizer.from_file(tok)
        _TOKENIZER.enable_truncation(max_length=_MAX_LEN)
        _TOKENIZER.enable_padding(pad_id=1, pad_token="<pad>")   # XLM-R <pad> 的 id 是 1
        return True
    except Exception as e:
        _LOAD_ERROR = str(e)
        return False


def _feed(pairs):
    """把 (query, doc) pairs 批量喂给 onnx,返回每条的相关性分数。"""
    encs = _TOKENIZER.encode_batch(pairs)
    input_ids = np.array([e.ids for e in encs], dtype=np.int64)
    attention = np.array([e.attention_mask for e in encs], dtype=np.int64)
    feeds = {}
    for inp in _SESSION.get_inputs():            # 按输入名匹配,兼容不同 onnx 命名
        n = inp.name.lower()
        feeds[inp.name] = attention if ("attention" in n or "mask" in n) else input_ids
    logits = _SESSION.run(None, feeds)[0]
    return logits.flatten().tolist()


def rerank(query, docs, top_k=3):
    """对 docs 按 query 相关性重排,返回 top_k 个 [{text, score}],分数越高越相关。
    模型不可用/出错时返回 None,调用方据此时降级。"""
    if not _load() or not docs:
        return None
    try:
        scores = _feed([(query, d) for d in docs])
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [{"text": d, "score": round(float(s), 3)} for d, s in ranked[:top_k]]
    except Exception:
        return None


def status():
    """诊断用:reranker 当前状态。"""
    if _SESSION is not None:
        return "✅ reranker 已就绪(bge-reranker-base 量化版)"
    if _LOAD_ERROR is not None:
        return f"⚠️ reranker 不可用(将降级为双路融合):{_LOAD_ERROR[:120]}"
    return "reranker 未加载(首次重排时加载,需 models/bge-reranker-base/ 下有模型文件)"
