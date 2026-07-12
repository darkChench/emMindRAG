def _is_table_row(line: str) -> bool:
    """判断一行是否像表格行:含至少 2 个 |(形成 "a | b" 的结构)"""
    s = line.strip()
    return "|" in s and s.count("|") >= 2


def _classify_units(text: str) -> list[dict]:
    """把文本拆成带类型的逻辑单元:[{type, text}]
    type: 'table'(表格)/ 'code'(代码块)/ 'para'(普通段落)
    - 表格 = 连续 >=2 行含 |
    - 代码块 = ``` 围起来的 fenced block
    - 其余按空行分段"""
    lines = text.split("\n")
    units, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        # 代码块:``` 围栏
        if line.strip().startswith("```"):
            block, i = [line], i + 1
            while i < n and not lines[i].strip().startswith("```"):
                block.append(lines[i]); i += 1
            if i < n:                       # 闭合的 ```
                block.append(lines[i]); i += 1
            units.append({"type": "code", "text": "\n".join(block)})
            continue
        # 表格:连续多行像表格行
        if _is_table_row(line):
            block, i = [line], i + 1
            while i < n and _is_table_row(lines[i]):
                block.append(lines[i]); i += 1
            if len(block) >= 2:             # 至少 2 行才算表格
                units.append({"type": "table", "text": "\n".join(block)})
                continue
            units.append({"type": "para", "text": "\n".join(block)})   # 单行 | 不算
            continue
        # 普通段落:攒到空行 / 表格行 / 代码块为止
        block, i = [line], i + 1
        while (i < n and lines[i].strip() != ""
               and not _is_table_row(lines[i])
               and not lines[i].strip().startswith("```")):
            block.append(lines[i]); i += 1
        units.append({"type": "para", "text": "\n".join(block)})
        while i < n and lines[i].strip() == "":    # 跳过空行
            i += 1
    return units


def _chunk_code(text: str, chunk_size: int = None, overlap_lines: int = None) -> list[str]:
    """代码文件分块:边界对齐"顶级行"(行首无缩进),尽量不切断函数/类。
    单个超大块(>2×chunk_size)才强制封,避免无限累积。"""
    import config
    if chunk_size is None: chunk_size = config.getd("chunk.code_size")
    if overlap_lines is None: overlap_lines = config.getd("chunk.code_overlap")
    lines = text.split("\n")
    blocks, current = [], []
    prev_blank = True   # 文件开头视为"前置空行",让首个定义能起新块
    for line in lines:
        if line.strip() == "":
            current.append(line); prev_blank = True; continue
        # 顶级行(行首无空白)且前面是空行 → 函数/类边界,起新块
        # (函数体内的 { 等虽行首无空白,但前面非空行,不会误判)
        if not line[0].isspace() and prev_blank and any(l.strip() for l in current):
            blocks.append(current); current = []
        current.append(line)
        prev_blank = False
    if current:
        blocks.append(current)

    chunks, buf, buf_len = [], [], 0
    for block in blocks:
        block_len = sum(len(l) + 1 for l in block)
        if buf and buf_len + block_len > chunk_size:
            chunks.append("\n".join(buf))
            buf = buf[-overlap_lines:] if overlap_lines else []  # 留已封块末尾几行接力
            buf_len = sum(len(l) + 1 for l in buf)
        buf.extend(block)
        buf_len += block_len
        if buf_len > chunk_size * 2:        # 单块超大也封,避免失控
            chunks.append("\n".join(buf))
            buf, buf_len = [], 0
    if buf:
        chunks.append("\n".join(buf))
    return chunks


def _is_heading(line: str) -> bool:
    """markdown 标题行(# / ## / ### ...),用于元素分类的章节上下文"""
    import re
    return bool(re.match(r'^#{1,6}\s+\S', line.strip()))


def _heading_text(line: str) -> str:
    """提取标题文字(去掉 # 前缀)"""
    import re
    return re.sub(r'^#{1,6}\s+', '', line.strip())


def chunk_text(
    text: str,
    chunk_size: int = None,     # 每块字符上限(不填走 config.yaml)
    overlap_lines: int = None,  # 相邻块重叠行(不填走 config)
    is_code: bool = False,      # 代码文件:按函数/逻辑块切,不切断函数
) -> list[str]:
    """按段落优先切分,保证完整条目不被切断。
    元素感知:表格、代码块作为"原子单元"整体保留,绝不在中间切断。
    is_code=True 时改用代码分块(顶级行边界,不切断函数/类)。"""
    import config
    if chunk_size is None: chunk_size = config.getd("chunk.size")
    if overlap_lines is None: overlap_lines = config.getd("chunk.overlap")
    if is_code:
        return _chunk_code(text, chunk_size, overlap_lines)
    units = _classify_units(text)
    chunks: list[str] = []
    current: list[str] = []     # 正在攒的当前块(装的是"行")
    current_len = 0
    current_section = ""        # 标题上下文链:最近一个 # 标题(Markdown / MinerU 输出)

    def seal():
        """封出当前块,带上当前章节标签〔...〕,并按 overlap 留几行接力"""
        nonlocal current, current_len
        if current:
            prefix = f"〔{current_section}〕\n" if current_section else ""
            chunks.append(prefix + "\n".join(current))
            current = current[-overlap_lines:] if overlap_lines else []
            current_len = sum(len(line) + 1 for line in current)

    for u in units:
        utext, utype = u["text"], u["type"]
        first = utext.split("\n")[0]
        if _is_heading(first):              # 元素分类:遇 # 标题 → 先封当前块(不跨章节),再更新
            if current: seal()
            current_section = _heading_text(first)
        # 加上会超上限,且当前块非空 → 先封一块
        if current and current_len + len(utext) > chunk_size:
            seal()
        current.extend(utext.split("\n"))
        current_len += len(utext) + 1
        # 表格/代码是原子单元:放进去后若已超上限,立即封块(不和后续文字混着被切)
        if utype in ("table", "code") and current_len > chunk_size:
            seal()

    seal()                      # 收尾
    return chunks
