"""
server.py —— MCP 服务入口
把 RAG 能力暴露成 MCP 工具,供 AI(Claude Code 等)调用。
"""
import os
from mcp.server.fastmcp import FastMCP
from retriever import search_combined
from store import count
from svd import (
    get_register as svd_get_register,
    list_peripherals as svd_list_peripherals,
    list_chips as svd_list_chips,
)

mcp = FastMCP("emMindRAG")


@mcp.tool()
def search_docs(query: str, code: bool = False, source: str = "") -> str:
    """搜索已索引的嵌入式文档(芯片手册 / 寄存器 / 代码)。
    当用户询问寄存器、位域、引脚、配置方法、外设用法等具体细节时调用。
    参数 query:用户的问题,例如 'SPI 的 CPHA 位怎么配置'
    参数 code:只想看代码实现时设 True(只在 .c/.py 等代码文件里搜)
    参数 source:只想在某来源文件里搜时填文件名,如 'demo_driver.c'
    """
    where = {"type": "code"} if code else ({"source": source} if source else None)
    findings = search_combined(query, top_k=3, where=where)
    if not findings:
        return "书架里没有相关内容。可能还没索引文档。"
    parts = []
    for i, item in enumerate(findings, 1):
        parts.append(f"[片段{i}] 来源:{item['via']}\n{item['text']}")
    return "\n\n".join(parts)


@mcp.tool()
def list_docs() -> str:
    """查看书架里有多少文档块。"""
    return f"书架里现有 {count()} 个文档块。"


@mcp.tool()
def index_doc(file_path: str, mineru="auto") -> str:
    """把一个新文档(PDF/txt/md/代码)索引进书架。
    当用户明确要求添加/导入新文档时调用。
    参数 mineru:True=强制 MinerU;False=强制 PyMuPDF;'auto'(默认)=自动检测扫描件(文字少则 OCR)。
    """
    from parser import parse, is_code_file
    from chunker import chunk_text
    from store import add_chunks
    text = parse(file_path, mineru=mineru, token=os.environ.get("MINERU_TOKEN"))
    chunks = chunk_text(text, is_code=is_code_file(file_path))
    add_chunks(chunks, source=os.path.basename(file_path), is_code=is_code_file(file_path))
    return f"已索引 {file_path},切出 {len(chunks)} 块,书架现有 {count()} 块"


@mcp.tool()
def get_register(peripheral: str, register: str = "", chip: str = "") -> str:
    """精确查询 ARM 芯片寄存器(来自 SVD 文件,零幻觉)。
    用于:寄存器地址、位域含义、位宽、外设列表等"精确事实"查询。
    比 search_docs 查 PDF 更准确——这是芯片厂商原厂定义,不会错。
    参数 peripheral:外设名,如 'SPI1' 'GPIOA'
    参数 register:寄存器名(可选),如 'CR1'。留空则返回该外设所有寄存器名
    参数 chip:芯片型号(可选),如 'stm32f103' 'f407'。留空则跨所有已加载芯片搜索并返回对比
    """
    return svd_get_register(peripheral, register, chip)


@mcp.tool()
def explain_register(peripheral: str, register: str = "", chip: str = "") -> str:
    """查寄存器并自动关联手册用法说明(SVD↔文档,独家创新)。
    在 get_register 的精确事实基础上,额外检索手册里该寄存器的用法/配置说明,
    把"零幻觉的寄存器事实"和"可读的手册用法"合二为一。
    参数同 get_register:peripheral 外设名、register 寄存器名(可选)、chip 芯片型号(可选)。"""
    from link import explain_register as _explain
    return _explain(peripheral, register, chip)


@mcp.tool()
def list_peripherals(chip: str = "") -> str:
    """列出芯片的外设名(来自 SVD)。
    参数 chip:芯片型号(可选),如 'stm32f103'。留空则汇总所有芯片
    """
    return svd_list_peripherals(chip)


@mcp.tool()
def list_chips() -> str:
    """列出当前已加载的所有 STM32 芯片型号(SVD 文件)。"""
    return svd_list_chips()


if __name__ == "__main__":
    mcp.run(transport="stdio")
