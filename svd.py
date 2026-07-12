"""
svd.py —— SVD 芯片寄存器数据库(多芯片版 + 枚举值 + 懒加载)
启动只建文件名索引(秒级),查询到哪颗才解析哪颗;跨芯片对比时用 pickle 缓存加速。
加载 svd_files/ 下所有 .svd 文件,解析外设/寄存器/位域/枚举值,支持跨芯片查询/对比。
"""
import os
import glob
import pickle
import copy
import xml.etree.ElementTree as ET

_SVD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svd_files")
_CACHE_FILE = os.path.join(_SVD_DIR, "_cache.pkl")
# 解析逻辑有变化时 bump 这个版本号,旧 pickle 缓存自动失效
_CACHE_VERSION = "v2-derivedFrom"
_SVD_INDEX = {}   # chip_lower -> file_path(启动建,秒级)
_CHIPS = {}        # chip_lower -> parsed peripherals(lazy 填充 / pickle 载入)
_CHIP_NAMES = []   # 原始文件名顺序(显示用)


def _parse_enums(field_elem):
    """解析 field 下的 enumeratedValues -> [{value, name, desc}]"""
    enums = []
    for ev in field_elem.findall(".//enumeratedValue"):
        v = (ev.findtext("value", "") or "").strip()
        n = (ev.findtext("name", "") or "").strip()
        d = (ev.findtext("description", "") or "").strip()
        if v:
            enums.append({"value": v, "name": n, "desc": d})
    return enums


def _parse_svd(file_path):
    root = ET.parse(file_path).getroot()
    peripherals = {}
    for periph in root.findall(".//peripheral"):
        p_name = (periph.findtext("name", "") or "").strip()
        base = (periph.findtext("baseAddress", "") or "").strip()
        registers = {}
        for reg in periph.findall(".//register"):
            r_name = (reg.findtext("name", "") or "").strip()
            offset = (reg.findtext("addressOffset", "") or "").strip()
            fields = {}
            for f in reg.findall(".//field"):
                f_name = (f.findtext("name", "") or "").strip()
                fields[f_name] = {
                    "desc": (f.findtext("description", "") or "").strip(),
                    "bitOffset": (f.findtext("bitOffset", "") or "").strip(),
                    "bitWidth": (f.findtext("bitWidth", "") or "").strip(),
                    "enums": _parse_enums(f),
                }
            registers[r_name] = {
                "desc": (reg.findtext("description", "") or "").strip(),
                "offset": offset,
                "abs": _add(base, offset),
                "fields": fields,
                "derivedFrom": (reg.get("derivedFrom", "") or "").strip(),
            }
        peripherals[p_name] = {
            "base": base,
            "registers": registers,
            "derivedFrom": (periph.get("derivedFrom", "") or "").strip(),
        }
    _resolve_inheritance(peripherals)
    return peripherals


def _add(base, offset):
    try:
        return hex(int(base, 0) + int(offset, 0))
    except Exception:
        return "?"


def _resolve_peripheral(peripherals, name, seen):
    """递归解析 peripheral 的 derivedFrom:从源外设拷贝寄存器组,目标显式寄存器覆盖。
    支持链式继承(A→B→C),seen 防环。继承后用本外设 base 重算绝对地址。"""
    if name in seen or name not in peripherals:
        return
    seen.add(name)
    p = peripherals[name]
    df = p.get("derivedFrom")
    if df:
        _resolve_peripheral(peripherals, df, seen)
        src = peripherals.get(df)
        if src:
            merged = copy.deepcopy(src["registers"])
            merged.update(p["registers"])
            base = p["base"]
            for r in merged.values():
                r["abs"] = _add(base, r["offset"])
            p["registers"] = merged


def _resolve_register(peripherals, pname, rname, seen):
    """递归解析 register 的 derivedFrom:从源寄存器拷贝位域 fields/desc。
    支持跨外设引用(ADC1.SR)和同外设引用(SR),支持链式,seen 防环。"""
    p = peripherals.get(pname)
    if not p:
        return
    r = p["registers"].get(rname)
    if not r or not r.get("derivedFrom"):
        return
    if (pname, rname) in seen:
        return
    seen.add((pname, rname))
    df = r["derivedFrom"]
    src_p, src_r = df.split(".", 1) if "." in df else (pname, df)
    _resolve_register(peripherals, src_p, src_r, seen)
    src = peripherals.get(src_p, {}).get("registers", {}).get(src_r)
    if src:
        if not r.get("fields"):
            r["fields"] = copy.deepcopy(src["fields"])
        if not r.get("desc"):
            r["desc"] = src.get("desc", "")


def _resolve_inheritance(peripherals):
    """先解 peripheral 继承(补全寄存器组),再解 register 继承(补全位域)。"""
    seen_p = set()
    for name in list(peripherals.keys()):
        _resolve_peripheral(peripherals, name, seen_p)
    seen_r = set()
    for pname, p in peripherals.items():
        for rname in list(p["registers"].keys()):
            _resolve_register(peripherals, pname, rname, seen_r)


def _ensure_loaded():
    """建索引(chip_lower -> 文件路径),秒级。不解析 XML 内容。"""
    global _SVD_INDEX, _CHIP_NAMES
    if _SVD_INDEX:
        return
    files = glob.glob(os.path.join(_SVD_DIR, "*.svd")) + \
            glob.glob(os.path.join(_SVD_DIR, "*.xml"))
    for f in files:
        chip = os.path.splitext(os.path.basename(f))[0]
        _CHIP_NAMES.append(chip)
        _SVD_INDEX[chip.lower()] = f


def _try_load_cache():
    """若 pickle 缓存的芯片清单与当前一致,载入全部解析结果。失败静默跳过。"""
    if not os.path.exists(_CACHE_FILE):
        return
    try:
        with open(_CACHE_FILE, "rb") as f:
            data = pickle.load(f)
    except Exception:
        return
    if data.get("v") == _CACHE_VERSION and set(data.get("keys", [])) == set(_SVD_INDEX.keys()):
        _CHIPS.update(data.get("chips", {}))


def _save_cache():
    """把已解析结果写盘,下次跨芯片对比可直接加载(免去 40s 全量解析)。"""
    try:
        with open(_CACHE_FILE, "wb") as f:
            pickle.dump({"v": _CACHE_VERSION, "keys": list(_SVD_INDEX.keys()), "chips": _CHIPS},
                        f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass


def _load_chip(chip_lower):
    """解析单颗芯片并缓存(lazy)。"""
    _ensure_loaded()
    if chip_lower in _CHIPS:
        return _CHIPS[chip_lower]
    f = _SVD_INDEX.get(chip_lower)
    if not f:
        return None
    try:
        _CHIPS[chip_lower] = _parse_svd(f)
    except Exception as e:
        _CHIPS[chip_lower] = {"_error": str(e)}
    return _CHIPS[chip_lower]


def _load_all():
    """确保全部芯片已解析(跨芯片对比用)。先吃 pickle,缺的再解析,完事写缓存。"""
    _ensure_loaded()
    if len(_CHIPS) >= len(_SVD_INDEX):
        return
    _try_load_cache()
    pending = [k for k in _SVD_INDEX if k not in _CHIPS]
    for k in pending:
        _load_chip(k)
    if pending:
        _save_cache()


def _find_chip(chip):
    cl = chip.lower()
    if cl in _SVD_INDEX:
        return cl
    m = [k for k in _SVD_INDEX if cl in k or k in cl]
    if len(m) == 1:
        return m[0]
    return m if m else None


def list_chips():
    _ensure_loaded()
    if not _SVD_INDEX:
        return "[!] 还没加载任何 SVD。把 .svd 文件放到 svd_files/ 目录。"
    return f"已加载 {len(_SVD_INDEX)} 颗芯片:{_CHIP_NAMES}"


def list_peripherals(chip=""):
    _ensure_loaded()
    if not _SVD_INDEX:
        return "[!] 还没加载 SVD。"
    if not chip:
        _load_all()
        lines = []
        for n in _CHIP_NAMES:
            cp = _CHIPS.get(n.lower(), {})
            cnt = len(cp) if isinstance(cp, dict) and "_error" not in cp else 0
            lines.append(f"{n}: {cnt} 个外设")
        return "\n".join(lines)
    key = _find_chip(chip)
    if not key:
        return f"没找到芯片 {chip}。有:{_CHIP_NAMES}"
    if isinstance(key, list):
        return f"芯片 {chip} 有多个匹配:{key},请用更精确的名字"
    cp = _load_chip(key)
    if not cp or "_error" in cp:
        return f"芯片 {chip} 解析失败"
    return f"{chip} 共 {len(cp)} 个外设:{list(cp.keys())[:50]}"


def get_register(peripheral, register="", chip=""):
    _ensure_loaded()
    if not _SVD_INDEX:
        return "[!] 还没加载 SVD。"

    if chip:
        key = _find_chip(chip)
        if not key:
            return f"没找到芯片 {chip}。有:{_CHIP_NAMES}"
        if isinstance(key, list):
            return f"芯片 {chip} 有多个匹配:{key},请用更精确的名字"
        cp = _load_chip(key)
        targets = [(chip, cp)] if cp and "_error" not in cp else []
    else:
        _load_all()
        targets = [(n, _CHIPS[n.lower()]) for n in _CHIP_NAMES
                   if "_error" not in _CHIPS.get(n.lower(), {"_error": 1})]

    results = []
    for cname, cp in targets:
        if "_error" in cp:
            continue
        p = cp.get(peripheral.upper())
        if not p:
            continue
        if not register:
            regs = list(p["registers"].keys())
            results.append(f"[{cname}] {peripheral}(基地址 {p['base']}) 共 {len(regs)} 个寄存器:{regs}")
            continue
        r = p["registers"].get(register.upper())
        if not r:
            continue
        lines = [f"[{cname}] {peripheral} > {register}  地址 {r['abs']}  ({r['desc'] or '无说明'})"]
        for fn, fi in r["fields"].items():
            line = f"  位{fi['bitOffset']}(宽{fi['bitWidth']}): {fn} — {fi['desc'] or '(无)'}"
            if fi.get("enums"):
                enum_str = ", ".join(f"{e['value']}={e['name']}" for e in fi["enums"])
                line += f"  枚举[{enum_str}]"
            lines.append(line)
        results.append("\n".join(lines))

    if not results:
        near = set()
        for cp in _CHIPS.values():
            if isinstance(cp, dict) and "_error" not in cp:
                for k in cp:
                    if peripheral.upper() in k.upper():
                        near.add(k)
        hint = f"没找到 {peripheral}" + (f".{register}" if register else "")
        if near:
            hint += f"。相近外设:{sorted(near)[:10]}"
        return hint
    return "\n\n".join(results)
