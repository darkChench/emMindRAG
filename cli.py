"""
cli.py —— emMindRAG 命令行工具
不开 AI 也能管理:索引文档、搜索、看芯片、查寄存器、清理书架。

用法示例:
    python cli.py add 芯片手册.pdf            # 索引一个文档
    python cli.py search "SPI 的 CPHA 位"     # 搜索(双路召回 + reranker 重排)
    python cli.py list                         # 看书架(按来源分组)
    python cli.py remove --source 芯片手册.pdf # 删某文档
    python cli.py remove --all                 # 清空书架
    python cli.py chips                        # 列出已加载的 STM32 芯片
    python cli.py reg GPIOA MODER stm32f103    # 查寄存器(SVD,零幻觉)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_add(args):
    from parser import parse, is_code_file
    from chunker import chunk_text
    from store import add_chunks, count
    if not os.path.exists(args.file):
        sys.exit(f"[!] 文件不存在: {args.file}")
    text = parse(args.file, mineru=(True if args.mineru else "auto"), token=os.environ.get("MINERU_TOKEN"))
    chunks = chunk_text(text, is_code=is_code_file(args.file))
    add_chunks(chunks, source=os.path.basename(args.file), is_code=is_code_file(args.file))
    print(f"✅ 已索引 {args.file}")
    print(f"   切出 {len(chunks)} 块,书架现有 {count()} 块")


def cmd_search(args):
    from retriever import search_combined
    where = None
    if args.code:
        where = {"type": "code"}        # 只在代码文件里搜
    elif args.source:
        where = {"source": args.source}  # 只在指定来源文件里搜
    results = search_combined(args.query, top_k=args.top, where=where)
    if not results:
        print("没找到相关内容。")
        return
    for i, item in enumerate(results, 1):
        print(f"\n─── [{i}] {item['via']} ───")
        print(item["text"][:400])


def cmd_list(args):
    from store import count, sources
    n = count()
    print(f"书架共 {n} 块,来源分布:")
    for src, c in sources().items():
        print(f"  {src}: {c} 块")


def cmd_remove(args):
    from store import clear, remove_source, count
    if args.all:
        clear()
        print("✅ 已清空书架")
    elif args.source:
        n = remove_source(args.source)
        print(f"✅ 删除 {args.source} 的 {n} 块,书架剩 {count()} 块")
    else:
        sys.exit("请指定 --source <文件名> 或 --all")


def cmd_chips(args):
    from svd import list_chips
    print(list_chips())


def cmd_reg(args):
    from svd import get_register, _ensure_loaded, _find_chip
    _ensure_loaded()
    peripheral, register, chip = args.peripheral, args.register, args.chip
    # 只给 2 个位置参数时,第 2 个若像芯片型号(stm32f103/f407/f7...)→ 当 chip
    # 这样 "reg GPIOA stm32f103" 理解为"查 f103 的 GPIOA 所有寄存器"
    if register and not chip and _find_chip(register):
        chip, register = register, ""
    print(get_register(peripheral, register, chip))


def cmd_explain(args):
    from link import explain_register
    from svd import _ensure_loaded, _find_chip
    _ensure_loaded()
    peripheral, register, chip = args.peripheral, args.register, args.chip
    if register and not chip and _find_chip(register):   # 同 reg:智能识别芯片型号
        chip, register = register, ""
    print(explain_register(peripheral, register, chip))


def cmd_doctor(args):
    """体检:检查库 / SVD / reranker / 书架 / 模块 / MCP 配置是否就绪;--fix 重建 SVD 缓存。"""
    import glob
    base = os.path.dirname(os.path.abspath(__file__))
    print("=== emMindRAG 体检 ===\n")

    print("[1] Python 库")
    libs = {"mcp": "mcp[cli]", "fitz": "pymupdf", "chromadb": "chromadb",
            "onnxruntime": "onnxruntime", "tokenizers": "tokenizers",
            "docx": "python-docx", "ebooklib": "ebooklib", "bs4": "beautifulsoup4",
            "numpy": "numpy"}
    for mod, pkg in libs.items():
        try:
            __import__(mod); print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} 缺失  →  pip install {pkg}")

    print("\n[2] SVD 芯片库")
    svd_dir = os.path.join(base, "svd_files")
    svds = glob.glob(os.path.join(svd_dir, "*.svd"))
    print(f"  {'✅' if len(svds) >= 100 else '⚠️'} {len(svds)} 颗 .svd(期望 ~152)")
    cache = os.path.join(svd_dir, "_cache.pkl")
    if os.path.exists(cache):
        print(f"  ✅ _cache.pkl({os.path.getsize(cache) // 1024 // 1024}M)")
    else:
        print("  ⚠️ _cache.pkl 缺失(首次跨芯片查询会自动重建,或 doctor --fix)")

    print("\n[3] reranker 模型(可选,缺失则 search 降级为双路融合)")
    model_dir = os.path.join(base, "models", "bge-reranker-base")
    onnx, tok = os.path.join(model_dir, "model.onnx"), os.path.join(model_dir, "tokenizer.json")
    if os.path.exists(onnx) and os.path.exists(tok):
        print(f"  ✅ model.onnx({os.path.getsize(onnx) // 1024 // 1024}M)+ tokenizer.json")
    else:
        print(f"  ⚠️ 模型缺失。下载到 {model_dir}:")
        print("     curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/onnx/model_quantized.onnx -o models/bge-reranker-base/model.onnx")
        print("     curl -L https://hf-mirror.com/Xenova/bge-reranker-base/resolve/main/tokenizer.json -o models/bge-reranker-base/tokenizer.json")

    print("\n[4] 文档书架")
    if os.path.exists(os.path.join(base, "chroma_db")):
        try:
            from store import count
            print(f"  ✅ chroma_db,{count()} 块")
        except Exception as e:
            print(f"  ❌ 书架读取失败:{e}")
    else:
        print("  ℹ️ chroma_db 不存在(还没索引文档 → cli.py add 文档)")

    print("\n[5] 核心模块导入")
    for mod in ["parser", "chunker", "store", "retriever", "svd", "reranker"]:
        try:
            __import__(mod); print(f"  ✅ {mod}.py")
        except Exception as e:
            print(f"  ❌ {mod}.py: {e}")

    print("\n[6] MCP 配置")
    print("  ✅ .mcp.json" if os.path.exists(os.path.join(base, ".mcp.json"))
          else "  ⚠️ .mcp.json 缺失(AI 工具靠它连接)")

    print("\n[7] MinerU 在线 API(可选,PDF 扫描件/复杂版式)")
    token = os.environ.get("MINERU_TOKEN")
    if token:
        print("  ✅ MINERU_TOKEN 已配 → 精准 API(200MB/200页)")
    else:
        print("  ℹ️ 未配 MINERU_TOKEN → 免登录轻量 API(10MB/20页);配 token 解锁大文件")

    print("\n[8] Embedding(向量模型)")
    from store import _get_embedding_function
    ef = _get_embedding_function()
    if ef:
        print(f"  ✅ 在线:{os.environ.get('EMBEDDING_PROVIDER')} / {ef.model}")
    else:
        print("  ℹ️ 默认 chromadb MiniLM(英文);配 EMBEDDING_PROVIDER=glm/openai + EMBEDDING_API_KEY 用中文在线")

    print("\n[9] 配置(config.yaml)")
    import config
    print(f"  ✅ chunk.size={config.getd('chunk.size')} / search.top_k={config.getd('search.top_k')} / pool={config.getd('search.pool_factor')}")
    print(f"     reranker={config.getd('reranker.model')} / mineru.lang={config.getd('mineru.language')}")

    if args.fix:
        print("\n=== 自动修复:重建 SVD 缓存 ===")
        try:
            if os.path.exists(cache):
                os.remove(cache); print("  已删旧缓存")
            from svd import _load_all
            import time; t0 = time.time()
            _load_all()
            sz = os.path.getsize(cache) // 1024 // 1024 if os.path.exists(cache) else 0
            print(f"  ✅ 重建完成({sz}M,{time.time()-t0:.0f}s)")
        except Exception as e:
            print(f"  ❌ 重建失败:{e}")


def main():
    p = argparse.ArgumentParser(prog="emrag", description="emMindRAG 命令行工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="索引文档(PDF/Word/EPUB/网页/txt/md)")
    a.add_argument("file", help="文件路径")
    a.add_argument("--mineru", action="store_true", help="强制 PDF 用 MinerU(默认 auto:自动检测扫描件)")
    a.set_defaults(func=cmd_add)

    s = sub.add_parser("search", help="搜索文档(双路召回 + reranker 重排)")
    s.add_argument("query", help="搜索词")
    s.add_argument("-n", "--top", type=int, default=3, help="返回条数(默认 3)")
    s.add_argument("--code", action="store_true", help="只在代码文件里搜")
    s.add_argument("--source", help="只在指定来源文件里搜,如 手册.pdf")
    s.set_defaults(func=cmd_search)

    sub.add_parser("list", help="看书架里的文档(按来源分组)").set_defaults(func=cmd_list)

    r = sub.add_parser("remove", help="删除文档块")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--source", help="删除指定来源文件的所有块")
    g.add_argument("--all", action="store_true", help="清空整个书架")
    r.set_defaults(func=cmd_remove)

    sub.add_parser("chips", help="列出已加载的 STM32 芯片").set_defaults(func=cmd_chips)

    reg = sub.add_parser("reg", help="查寄存器(SVD,零幻觉)")
    reg.add_argument("peripheral", help="外设名,如 GPIOA")
    reg.add_argument("register", nargs="?", default="", help="寄存器名(可选),如 MODER")
    reg.add_argument("chip", nargs="?", default="", help="芯片型号(可选),如 stm32f103")
    reg.set_defaults(func=cmd_reg)

    e = sub.add_parser("explain", help="查寄存器 + 关联手册用法(SVD↔文档,独家)")
    e.add_argument("peripheral", help="外设名,如 GPIOA")
    e.add_argument("register", nargs="?", default="", help="寄存器名(可选)")
    e.add_argument("chip", nargs="?", default="", help="芯片型号(可选)")
    e.set_defaults(func=cmd_explain)

    d = sub.add_parser("doctor", help="体检:检查环境/数据是否就绪")
    d.add_argument("--fix", action="store_true", help="重建 SVD 缓存")
    d.set_defaults(func=cmd_doctor)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
