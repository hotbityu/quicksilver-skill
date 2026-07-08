#!/usr/bin/env python3
"""
Fast QS OpenAPI reference exporter.

Usage:
    python3 scripts/export_qs_api.py /path/to/qs-project
    python3 scripts/export_qs_api.py /path/to/qs-project /path/to/output.md

The exporter scans module Java @Api handlers, TsUnit SQL metadata, and
EntityApiImpl inherited handlers, then writes a Markdown API calling reference.
It is designed for fast first-pass API discovery. Deep service-level request
shape tracing may still need manual review for complex handlers.
"""

import argparse
import gc
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree


SCRIPT_DIR = Path(__file__).resolve().parent
BASIC_INFO_SOURCE_LABELS = {"源碼", "源碼依據", "源码", "源码依据", "Source", "Source Evidence"}
BASE_UNIT_BY_API = {}
API_ANNOTATION_CACHE = {}
FIELD_EXTRACTION_CACHE = {}
SUPERCLASS_CHAIN_CACHE = {}
JAVA_SOURCE_ROOTS = []
JAVA_SOURCE_CLASS_CACHE = {}
CONSTANT_TYPE_CACHE = {}
CONSTANT_OPTIONS_CACHE = {}
TOP_LEVEL_API_BASE_CLASSES = {"BaseApiImpl", "EntityApiImpl", "BusinessEntityApiImpl", "TreeEntityApiImpl"}
WORKFLOW_API_SUFFIXES = {"submit", "assign", "execute", "finish", "discard", "revise"}
ENTITY_EDIT_IDS = {
    "541c707d-79dd-4dbb-85fc-1a214fd5fce4",
    "e87b8d5b-f747-4467-9754-e149bc047e1c",
}
NON_ENTITY_EDIT_IDS = {"8b7ebd7e-8173-4787-9e34-3d27ad4c9c29"}
DEEP_FIELD_SCAN_MAX_API_COUNT = 25
DEEP_FIELD_SCAN_MAX_TEXT_SIZE = 30000
DEEP_FIELD_SCAN_MAX_METHOD_BODY_SIZE = 12000


def read(path):
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def rel(path, root):
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def split_assignments(text):
    parts = []
    buf = []
    quote = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'":
            buf.append(ch)
            if quote and i + 1 < len(text) and text[i + 1] == "'":
                buf.append("'")
                i += 2
                continue
            quote = not quote
        elif ch == "," and not quote:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)
        i += 1
    part = "".join(buf).strip()
    if part:
        parts.append(part)
    return parts


def parse_set_clause(clause):
    data = {}
    for part in split_assignments(clause):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip(" `")
        value = value.strip()
        if value.lower() == "null":
            data[key] = None
        elif value.startswith("'") and value.endswith("'"):
            data[key] = value[1:-1].replace("''", "'")
        else:
            data[key] = value
    return data


def version_tuple(value):
    parts = []
    for part in str(value or "").split("."):
        if not part.isdigit():
            return ()
        parts.append(int(part))
    return tuple(parts)


def sql_filename_version(path):
    matches = re.findall(r"(?<!\d)(\d+(?:\.\d+)+)(?!\d)", Path(path).name)
    return version_tuple(matches[-1]) if matches else ()


def selected_unit_sql_files(sql_root, metadata=None):
    metadata = metadata or {}
    sql_root = Path(sql_root)
    init_sql = sql_root / "init.sql"
    if not metadata.get("has_init_sql"):
        return sorted(Path(sql_root).rglob("*.sql"))

    init_version = metadata.get("init_version", "")
    if not init_version:
        return [init_sql] if init_sql.exists() else sorted(Path(sql_root).rglob("*.sql"))

    threshold = version_tuple(init_version)
    selected = []
    sql_files = sorted(Path(sql_root).rglob("*.sql"))
    for sql_file in sql_files:
        if sql_file.name == "init.sql":
            selected.append(sql_file)
            continue
        file_version = sql_filename_version(sql_file)
        if file_version and file_version > threshold:
            selected.append(sql_file)
    return selected


def parse_unit_sql_files(sql_files, source_root):
    units = parse_base_units()
    insert_re = re.compile(r"insert\s+into\s+TsUnit\s+set\s+(.*?);", re.I | re.S)
    update_re = re.compile(r"update\s+TsUnit\s+set\s+(.*?)\s+where\s+(.*?);", re.I | re.S)
    for sql_file in sql_files:
        text = read(sql_file)
        for m in insert_re.finditer(text):
            data = parse_set_clause(m.group(1))
            key = data.get("FId") or data.get("FCode")
            if key:
                data["_source"] = f"{rel(sql_file, source_root)}:{text[:m.start()].count(chr(10)) + 1}"
                units[key] = data

        for m in update_re.finditer(text):
            data = parse_set_clause(m.group(1))
            where = m.group(2)
            targets = []
            for key in ("FId", "FCode"):
                wm = re.search(key + r"\s*=\s*'([^']+)'", where, re.I)
                if wm:
                    targets = [u for u in units.values() if u.get(key) == wm.group(1)]
            for target in targets:
                target.update(data)
                target["_source"] = f"{target.get('_source', '')}; update {rel(sql_file, source_root)}:{text[:m.start()].count(chr(10)) + 1}"
    return units


def parse_field_sql_files(sql_files, source_root):
    fields_by_unit_id = parse_base_fields()
    insert_re = re.compile(r"insert\s+into\s+TsField\s+set\s+(.*?);", re.I | re.S)
    update_re = re.compile(r"update\s+TsField\s+set\s+(.*?)\s+where\s+(.*?);", re.I | re.S)
    for sql_file in sql_files:
        text = read(sql_file)
        for m in insert_re.finditer(text):
            data = parse_set_clause(m.group(1))
            unit_id = data.get("FUnitId")
            field_name = data.get("FName")
            if unit_id and field_name:
                data["_source"] = f"{rel(sql_file, source_root)}:{text[:m.start()].count(chr(10)) + 1}"
                fields_by_unit_id.setdefault(unit_id, {})[field_name] = data

        for m in update_re.finditer(text):
            data = parse_set_clause(m.group(1))
            where = m.group(2)
            unit_id = ""
            field_name = ""
            unit_match = re.search(r"FUnitId\s*=\s*'([^']+)'", where, re.I)
            name_match = re.search(r"FName\s*=\s*'([^']+)'", where, re.I)
            id_match = re.search(r"FId\s*=\s*'([^']+)'", where, re.I)
            if unit_match:
                unit_id = unit_match.group(1)
            if name_match:
                field_name = name_match.group(1)
            targets = []
            if unit_id and field_name:
                target = fields_by_unit_id.get(unit_id, {}).get(field_name)
                if target:
                    targets.append(target)
            elif id_match:
                field_id = id_match.group(1)
                for fields in fields_by_unit_id.values():
                    targets.extend(field for field in fields.values() if field.get("FId") == field_id)
            for target in targets:
                target.update(data)
                target["_source"] = f"{target.get('_source', '')}; update {rel(sql_file, source_root)}:{text[:m.start()].count(chr(10)) + 1}"
    return fields_by_unit_id


def parse_units(module_dir, metadata=None):
    sql_root = Path(module_dir) / "src/main/resources/QS-MODULE/data/sql/default"
    if not sql_root.exists():
        return {}
    metadata = metadata or parse_module_sql_metadata(module_dir)
    return parse_unit_sql_files(selected_unit_sql_files(sql_root, metadata), Path(module_dir).parent)


def parse_fields(module_dir, metadata=None):
    sql_root = Path(module_dir) / "src/main/resources/QS-MODULE/data/sql/default"
    if not sql_root.exists():
        return {}
    metadata = metadata or parse_module_sql_metadata(module_dir)
    return parse_field_sql_files(selected_unit_sql_files(sql_root, metadata), Path(module_dir).parent)


def base_init_sql_files():
    sql_dir = SCRIPT_DIR.parent / "assets/templates/api-discovery/sql"
    return sorted(sql_dir.glob("*.sql")) if sql_dir.exists() else []


def base_field_sql_files():
    api_sql_dir = SCRIPT_DIR.parent / "assets/templates/api-discovery/sql"
    return sorted(api_sql_dir.glob("*.sql")) if api_sql_dir.exists() else []


def parse_base_units():
    insert_re = re.compile(r"insert\s+into\s+TsUnit\s+set\s+(.*?);", re.I | re.S)
    units = {}
    for init_sql in base_init_sql_files():
        text = read(init_sql)
        for m in insert_re.finditer(text):
            data = parse_set_clause(m.group(1))
            key = data.get("FId") or data.get("FCode")
            if key:
                data["_source"] = f"{rel(init_sql, SCRIPT_DIR.parent)}:{text[:m.start()].count(chr(10)) + 1}"
                units[key] = data
    return units


def parse_base_fields():
    insert_re = re.compile(r"insert\s+into\s+TsField\s+set\s+(.*?);", re.I | re.S)
    fields_by_unit_id = {}
    for init_sql in base_field_sql_files():
        text = read(init_sql)
        for m in insert_re.finditer(text):
            data = parse_set_clause(m.group(1))
            unit_id = data.get("FUnitId")
            field_name = data.get("FName")
            if unit_id and field_name:
                data["_source"] = f"{rel(init_sql, SCRIPT_DIR.parent)}:{text[:m.start()].count(chr(10)) + 1}"
                fields_by_unit_id.setdefault(unit_id, {})[field_name] = data
    return fields_by_unit_id


def find_base_unit_by_api(api_fqcn):
    if api_fqcn in BASE_UNIT_BY_API:
        return BASE_UNIT_BY_API[api_fqcn]
    if not api_fqcn:
        return None
    marker = f"FApiClassName='{api_fqcn}'"
    for init_sql in base_init_sql_files():
        text = read(init_sql)
        pos = text.find(marker)
        if pos == -1:
            continue
        start = text.rfind("insert into TsUnit set", 0, pos)
        end = text.find(";", pos)
        if start == -1 or end == -1:
            continue
        statement = text[start:end]
        m = re.search(r"insert\s+into\s+TsUnit\s+set\s+(.*)", statement, re.I | re.S)
        if not m:
            continue
        data = parse_set_clause(m.group(1))
        data["_source"] = f"{rel(init_sql, SCRIPT_DIR.parent)}:{text[:start].count(chr(10)) + 1}"
        BASE_UNIT_BY_API[api_fqcn] = data
        return data
    BASE_UNIT_BY_API[api_fqcn] = None
    return None


def parse_module_sql_metadata(module_dir):
    sql_root = Path(module_dir) / "src/main/resources/QS-MODULE/data/sql/default"
    init_sql = sql_root / "init.sql"
    init_xml = sql_root / "init.xml"
    metadata = {
        "sql_root": sql_root,
        "has_init_sql": init_sql.exists(),
        "init_version": "",
    }
    if init_xml.exists():
        try:
            root = ElementTree.fromstring(read(init_xml))
            version = root.findtext("version")
            metadata["init_version"] = (version or "").strip()
        except ElementTree.ParseError:
            metadata["init_version"] = ""
    return metadata


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//.*", "", text)


def mask_java_comments(text):
    chars = list(text)
    quote = None
    i = 0
    while i < len(chars):
        ch = chars[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif text.startswith("//", i):
            end = text.find("\n", i + 2)
            if end == -1:
                end = len(chars)
            for j in range(i, end):
                chars[j] = " "
            i = end
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                end = len(chars) - 2
            for j in range(i, min(end + 2, len(chars))):
                if chars[j] != "\n":
                    chars[j] = " "
            i = end + 2
            continue
        i += 1
    return "".join(chars)


def parse_java_class(path, project_root):
    text = read(path)
    package = re.search(r"package\s+([\w.]+)\s*;", text)
    cls = re.search(r"public\s+(?:abstract\s+)?class\s+(\w+)(?:<[^>{}]+>)?\s+extends\s+([\w.<>]+)", text)
    imports = {
        imp.rsplit(".", 1)[-1]: imp
        for imp in re.findall(r"import\s+([\w.]+)\s*;", text)
    }
    return {
        "path": Path(path),
        "rel": rel(path, project_root),
        "text": text,
        "package": package.group(1) if package else "",
        "class": cls.group(1) if cls else Path(path).stem,
        "extends": cls.group(2).split("<", 1)[0] if cls else "",
        "extends_raw": cls.group(2) if cls else "",
        "imports": imports,
    }


def find_matching(text, start, left, right):
    if start < 0 or start >= len(text) or text[start] != left:
        return -1
    depth = 0
    quote = None
    i = start
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif text.startswith("//", i):
            end = text.find("\n", i + 2)
            if end == -1:
                return -1
            i = end
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                return -1
            i = end + 2
            continue
        elif ch == left:
            depth += 1
        elif ch == right:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def comment_first_line(comment):
    if comment.lstrip().startswith("//"):
        lines = re.split(r"\n", comment)
    else:
        lines = re.sub(r"^\s*/\*\*?", "", comment, flags=re.S)
        lines = re.sub(r"\*/\s*$", "", lines, flags=re.S).splitlines()
    cleaned_lines = [
        re.sub(r"^\s*(?://|\*)\s?", "", line).strip()
        for line in lines
    ]
    if is_paired_separator_comment(cleaned_lines):
        return ""
    for line in cleaned_lines:
        if line and not line.startswith("@") and not is_separator_comment_line(line):
            return line
    return ""


def is_separator_comment_line(line):
    return bool(re.fullmatch(r"[-=_*]{3,}", re.sub(r"\s+", "", line or "")))


def is_paired_separator_comment(lines):
    meaningful = [line for line in lines if line]
    if len(meaningful) < 3:
        return False
    return is_separator_comment_line(meaningful[0]) and is_separator_comment_line(meaningful[-1])


def has_only_annotations(segment):
    i = 0
    while True:
        while i < len(segment) and segment[i].isspace():
            i += 1
        if i >= len(segment):
            return True
        if segment[i] != "@":
            return False
        m = re.match(r"@[\w.]+", segment[i:])
        if not m:
            return False
        i += m.end()
        while i < len(segment) and segment[i].isspace():
            i += 1
        if i < len(segment) and segment[i] == "(":
            end = find_matching(segment, i, "(", ")")
            if end == -1:
                return False
            i = end + 1


def method_comment_first_line(text, sig_start):
    window_start = max(0, sig_start - 5000)
    window = text[window_start:sig_start]
    pattern = r"//[^\n]*(?:\n\s*//[^\n]*)*|/\*\*?.*?\*/"
    candidates = []
    for match in re.finditer(pattern, window, re.S):
        after_comment = window[match.end():]
        if has_only_annotations(after_comment):
            candidates.append(match.group(0))
    return comment_first_line(candidates[-1]) if candidates else ""


def api_annotations(text):
    cache_key = hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()
    cached = API_ANNOTATION_CACHE.get(cache_key)
    if cached is not None:
        return cached
    searchable = mask_java_comments(text)
    api_count = len(re.findall(r"@Api\b", searchable))
    skip_body = should_skip_deep_field_scan({"text": text}, [None] * api_count)
    i = 0
    out = []
    while True:
        m = re.search(r"@Api\b", searchable[i:])
        if not m:
            break
        start = i + m.start()
        j = start + len("@Api")
        paren = j
        while paren < len(searchable) and searchable[paren].isspace():
            paren += 1
        if paren < len(searchable) and searchable[paren] == "(":
            end = find_matching(searchable, paren, "(", ")")
            if end == -1:
                i = paren + 1
                continue
            args = text[paren + 1:end]
            after = end + 1
        else:
            args = ""
            after = j

        sig = re.search(r"(?:public|protected)\s+([\w<>.?]+|void)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\{", searchable[after:], re.S)
        if sig:
            sig_start = after + sig.start()
            brace = searchable.find("{", sig_start)
            body_end = brace if skip_body else find_matching(searchable, brace, "{", "}")
            if body_end == -1:
                i = brace + 1 if brace != -1 else after + 1
                continue
            out.append({
                "line": text[:start].count("\n") + 1,
                "args": args.strip(),
                "return": sig.group(1),
                "method": sig.group(2),
                "comment": method_comment_first_line(text, sig_start),
                "params": sig.group(3),
                "body": "" if skip_body else text[brace + 1:body_end],
            })
            i = brace + 1 if skip_body else body_end + 1
        else:
            i = after + 1
    if skip_body:
        API_ANNOTATION_CACHE[cache_key] = out
    return out


def parse_ann_value(args, key):
    if key == "value":
        m = re.search(r"^\s*\"([^\"]*)\"", args, re.S)
        if m:
            return m.group(1)
    m = re.search(key + r"\s*=\s*\"([^\"]*)\"", args, re.S)
    return m.group(1) if m else None


def parse_ann_enum_value(args, key):
    quoted = parse_ann_value(args, key)
    if quoted:
        return quoted.lower()
    m = re.search(key + r"\s*=\s*(?:\w+\.)?(\w+)", args)
    return m.group(1).lower() if m else None


def parse_ann_bool(args, key, default=False):
    m = re.search(key + r"\s*=\s*(true|false)", args)
    return (m.group(1) == "true") if m else default


def normalize_api_type(value):
    if not value:
        return "unknown"
    value = value.rsplit(".", 1)[-1].lower()
    return {
        "string": "string",
        "uuid": "uuid",
        "int": "int",
        "integer": "int",
        "long": "long",
        "boolean": "boolean",
        "bool": "boolean",
        "object": "object",
        "json": "object",
        "array": "array",
        "file": "file",
        "text": "text",
    }.get(value, value)


def parse_api_attributes(args, key):
    key_match = re.search(key + r"\s*=", args)
    if not key_match:
        return {}

    start = args.find("{", key_match.end())
    if start == -1:
        return {}
    end = find_matching(args, start, "{", "}")
    if end == -1:
        return {}

    block = args[start + 1:end]
    fields = {}
    for attr in re.finditer(r"@ApiAttribute\s*\((.*?)\)", block, re.S):
        raw = attr.group(1)
        name = parse_ann_value(raw, "name")
        if not name:
            continue
        type_name = parse_ann_value(raw, "type")
        if not type_name:
            type_match = re.search(r"type\s*=\s*ApiDataType\.([A-Z_]+)", raw)
            type_name = type_match.group(1) if type_match else ""
        typ = normalize_api_type(type_name)
        fields[name] = {
            "type": typ,
            "required": parse_ann_bool(raw, "required", False),
            "default": parse_ann_value(raw, "defaultValue") or "",
            "source": "API 註解",
            "description": parse_ann_value(raw, "description") or "由 API 註解宣告。",
        }
    return fields


def merge_annotation_fields(primary, fallback, allow_new_fields=None):
    if allow_new_fields is None:
        allow_new_fields = not primary
    for name, field in fallback.items():
        if name not in primary:
            if not allow_new_fields:
                continue
            primary[name] = field
            continue
        current = primary[name]
        if current.get("type") in ("", "unknown") and field.get("type") not in ("", "unknown"):
            current["type"] = field["type"]
            current["source"] = merge_source(current.get("source", ""), field.get("source", ""))
        if field.get("required") is True and current.get("required") is not True:
            current["required"] = True
            current["source"] = merge_source(current.get("source", ""), field.get("source", ""))
        elif current.get("required", "") == "" and field.get("required", "") != "":
            current["required"] = field["required"]
        if not current.get("description") and field.get("description"):
            current["description"] = field["description"]
    return primary


def merge_source(*values):
    parts = []
    for value in values:
        for part in str(value or "").split("/"):
            part = part.strip()
            if part and part not in parts:
                parts.append(part)
    return " / ".join(parts)


def request_field_description(name, typ):
    if typ == "object" or typ == "array<object>" or typ.startswith("array<"):
        if name == "data":
            return "表單資料物件；屬性依單元模型、表單欄位或執行時元資料而定。"
        if name == "form":
            return "表單設定物件；屬性依表單欄位設定或執行時元資料而定。"
        if name == "forms":
            return "多表單資料物件；屬性依單元模型、表單欄位或執行時元資料而定。"
        if name in ("options", "filter", "query", "condition"):
            return "條件/選項物件；屬性依呼叫情境、查詢設定或執行時元資料而定。"
        if typ.startswith("array<"):
            inner = typ[6:-1]
            if inner != "object":
                return "值列表；項目類型由處理器讀取邏輯推斷。"
            return "物件列表；項目屬性依處理器邏輯或執行時元資料而定。"
        return "物件欄位；屬性依處理器邏輯或執行時元資料而定。"
    return "從 request JSON 讀取。"


def response_field_description(name, typ):
    if typ == "object" or typ == "array<object>" or name in ("data", "items"):
        if name == "data":
            return "回應資料物件；屬性依單元模型、欄位設定或執行時元資料而定。"
        if name == "items":
            return "資料列表；項目屬性依單元模型、列表欄位或執行時元資料而定。"
        if typ == "array<object>":
            return "物件列表；項目屬性依處理器邏輯或執行時元資料而定。"
        return "回應物件；屬性依處理器邏輯或執行時元資料而定。"
    return "由 `ApiResult.put`/JSON 組裝推斷。"


def split_java_args(text):
    parts = []
    buf = []
    quote = None
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\":
                if i + 1 < len(text):
                    buf.append(text[i + 1])
                    i += 2
                    continue
            elif ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)
        i += 1
    part = "".join(buf).strip()
    if part:
        parts.append(part)
    return parts


def iter_put_calls(text):
    i = 0
    while True:
        m = re.search(r"\.put\s*\(", text[i:])
        if not m:
            break
        paren = i + m.end() - 1
        end = find_matching(text, paren, "(", ")")
        if end == -1:
            break
        args = split_java_args(text[paren + 1:end])
        if len(args) >= 2 and args[0].startswith('"') and args[0].endswith('"'):
            yield args[0][1:-1], args[1]
        i = end + 1


def iter_receiver_put_calls(text):
    i = 0
    while True:
        m = re.search(r"(\w+)\.put\s*\(", text[i:])
        if not m:
            break
        receiver = m.group(1)
        paren = i + m.end() - 1
        end = find_matching(text, paren, "(", ")")
        if end == -1:
            break
        args = split_java_args(text[paren + 1:end])
        if len(args) >= 2 and args[0].startswith('"') and args[0].endswith('"'):
            yield receiver, args[0][1:-1], args[1]
        i = end + 1


def pascal_name(name):
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[_\W]+", name) if part)


def simple_type_name(type_name):
    type_name = (type_name or "").strip()
    type_name = re.sub(r"<.*>", "", type_name)
    type_name = type_name.replace("[]", "")
    return type_name.rsplit(".", 1)[-1]


def java_type_to_api(type_name):
    raw = (type_name or "").strip()
    array = raw.endswith("[]")
    collection = re.match(r"(?:List|Set|Collection|DataSet|JSONArray|java\.util\.(?:List|Set|Collection))\s*<\s*([\w.]+)", raw)
    if collection:
        inner = java_type_to_api(collection.group(1))
        return f"array<{inner}>" if inner in ("string", "uuid", "int", "long", "boolean") else f"array<{simple_type_name(collection.group(1))}>"
    typ = simple_type_name(raw)
    mapped = {
        "String": "string",
        "UUID": "uuid",
        "int": "int",
        "Integer": "int",
        "long": "long",
        "Long": "long",
        "double": "number",
        "Double": "number",
        "float": "number",
        "Float": "number",
        "BigDecimal": "number",
        "boolean": "boolean",
        "Boolean": "boolean",
        "JSONObject": "object",
        "JSONArray": "array<object>",
        "JsonResult": "object",
        "XmlResult": "object",
    }.get(typ, typ)
    return f"array<{mapped}>" if array else mapped


def ts_field_type_to_api(field):
    field_type = simple_type_name(str((field or {}).get("FType") or ""))
    field_name = str((field or {}).get("FName") or "")
    if field_type in {"InputBox-Key", "EntityBox", "DepartmentBox", "UserBox"} or field_name.lower().endswith("id"):
        return "uuid"
    if field_type in {"InputBox-Integer", "InputBox-Long"}:
        return "int" if field_type == "InputBox-Integer" else "long"
    if field_type in {"InputBox-Decimal", "InputBox-Double", "InputBox-Percent", "InputBox-Money"}:
        return "number"
    if field_type in {"CheckBox", "SwitchBox"}:
        return "boolean"
    if field_type.startswith("DateBox"):
        return "string"
    if field_type in {"ImageBox", "FileBox", "AttachmentBox"}:
        return "file"
    return "string"


def field_required(value):
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def api_field_from_ts_field(field):
    description = str(field.get("FTitle") or field.get("FName") or "")
    control_type = field.get("FType")
    if control_type:
        description = (description + "；" if description else "") + f"控制類型 `{control_type}`。"
    if field.get("FSize") not in (None, "", "null"):
        description += f"長度/大小 `{field.get('FSize')}`。"
    return {
        "type": ts_field_type_to_api(field),
        "required": field_required(field.get("FRequired")),
        "source": "TsField metadata",
        "description": description or "由單元欄位 metadata 推斷。",
    }


def ts_fields_to_api_fields(fields):
    return {
        name: api_field_from_ts_field(field)
        for name, field in (fields or {}).items()
        if name and str(field.get("FVisible", "1")).strip() != "-1"
    }


def unit_ts_field_shape(unit, field_metadata):
    if not unit or not field_metadata:
        return {}
    fields = field_metadata.get("fields_by_unit_id", {}).get(unit.get("FId"), {})
    return ts_fields_to_api_fields(fields)


def resolve_java_class(type_name, current_info, java_by_fqcn, simple_java):
    typ = simple_type_name(type_name)
    if not typ or typ in {"T", "Object", "JSONObject", "JSONArray"}:
        return None
    if type_name in java_by_fqcn:
        return java_by_fqcn[type_name]
    if current_info:
        fqcn = current_info.get("imports", {}).get(typ)
        if fqcn in java_by_fqcn:
            return java_by_fqcn[fqcn]
        fqcn = (current_info.get("package", "") + "." + typ).strip(".")
        if fqcn in java_by_fqcn:
            return java_by_fqcn[fqcn]
    matches = simple_java.get(typ, [])
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_type_fqcn(type_name, current_info, java_by_fqcn, simple_java):
    info = resolve_java_source_class(type_name, current_info, java_by_fqcn, simple_java)
    if info:
        return (info.get("package", "") + "." + info.get("class", "")).strip(".")
    candidates = candidate_java_fqcns(type_name, current_info)
    return candidates[0] if candidates else simple_type_name(type_name)


def unit_model_name_candidates(unit):
    names = set()
    for key, suffix in (
        ("FHomeClassName", "Home"),
        ("FDaoClassName", "Dao"),
        ("FServiceClassName", "Service"),
        ("FActionClassName", "Action"),
        ("FApiClassName", "Api"),
    ):
        class_name = simple_type_name(str(unit.get(key) or ""))
        if not class_name:
            continue
        for impl_suffix in ("Impl", ""):
            full_suffix = suffix + impl_suffix
            if class_name.endswith(full_suffix):
                base_name = class_name[:-len(full_suffix)]
                if base_name:
                    names.add(base_name + "Model")
                break
    return names


def unit_matches_type(unit, type_fqcn, type_simple):
    candidates = {
        unit.get("FModelClassName"),
        unit.get("FHomeClassName"),
        unit.get("FDaoClassName"),
        unit.get("FServiceClassName"),
        unit.get("FActionClassName"),
        unit.get("FApiClassName"),
    }
    if type_fqcn and type_fqcn in candidates:
        return True
    unit_code_tail = simple_type_name(str(unit.get("FCode") or "").replace(".", "."))
    unit_table = str(unit.get("FTable") or "")
    expected = {
        unit_code_tail,
        unit_code_tail + "Model",
        unit_table,
        unit_table + "Model",
    }
    expected.update(unit_model_name_candidates(unit))
    return type_simple in expected


def resolve_ts_field_shape(type_name, current_info, java_by_fqcn, simple_java, unit=None, field_metadata=None):
    field_metadata = field_metadata or {}
    if not field_metadata:
        return {}
    if not type_name:
        return unit_ts_field_shape(unit, field_metadata)
    type_simple = simple_type_name(type_name)
    type_fqcn = resolve_type_fqcn(type_name, current_info, java_by_fqcn, simple_java)
    candidate_units = []
    if unit and unit_matches_type(unit, type_fqcn, type_simple):
        candidate_units.append(unit)
    for candidate in field_metadata.get("units", {}).values():
        if candidate is unit:
            continue
        if unit_matches_type(candidate, type_fqcn, type_simple):
            candidate_units.append(candidate)
    for candidate in candidate_units:
        fields = field_metadata.get("fields_by_unit_id", {}).get(candidate.get("FId"), {})
        api_fields = ts_fields_to_api_fields(fields)
        if api_fields:
            return api_fields
    return {}


def candidate_java_fqcns(type_name, current_info):
    raw = (type_name or "").strip()
    typ = simple_type_name(raw)
    candidates = []
    if "." in raw:
        candidates.append(raw)
    if current_info:
        imported = current_info.get("imports", {}).get(typ)
        if imported:
            candidates.append(imported)
        package = current_info.get("package", "")
        if package and typ:
            candidates.append(package + "." + typ)
    return list(dict.fromkeys(candidates))


def load_java_source_class(fqcn):
    if fqcn in JAVA_SOURCE_CLASS_CACHE:
        return JAVA_SOURCE_CLASS_CACHE[fqcn]
    relative = Path(*fqcn.split(".")).with_suffix(".java")
    for source_root in JAVA_SOURCE_ROOTS:
        path = source_root / relative
        if path.exists():
            project_root = source_root.parents[3] if len(source_root.parents) > 3 else source_root
            info = parse_java_class(path, project_root)
            JAVA_SOURCE_CLASS_CACHE[fqcn] = info
            return info
    JAVA_SOURCE_CLASS_CACHE[fqcn] = None
    return None


def resolve_java_source_class(type_name, current_info, java_by_fqcn, simple_java):
    info = resolve_java_class(type_name, current_info, java_by_fqcn, simple_java)
    if info:
        return info
    for fqcn in candidate_java_fqcns(type_name, current_info):
        info = load_java_source_class(fqcn)
        if info:
            return info
    return None


def literal_expr_type(expr):
    expr = (expr or "").strip()
    if expr.startswith('"'):
        return "string"
    if expr in ("true", "false"):
        return "boolean"
    if re.match(r"-?\d+[lL]?\b", expr):
        return "long" if expr[-1:] in ("l", "L") else "int"
    if re.match(r"-?\d+\.\d+[fFdD]?\b", expr):
        return "number"
    return ""


def literal_expr_value(expr):
    expr = (expr or "").strip()
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]
    if expr in ("true", "false"):
        return expr
    numeric = re.match(r"^(-?\d+(?:\.\d+)?)(?:[lLfFdD])?$", expr)
    if numeric:
        return numeric.group(1)
    return ""


def constant_reference(expr):
    expr = (expr or "").strip()
    m = re.match(r"^([\w.]+)\.([A-Za-z_][A-Za-z0-9_]*)$", expr)
    return m.groups() if m else ("", "")


def enum_constant_options(text, class_name):
    m = re.search(r"\b(?:public\s+)?enum\s+" + re.escape(class_name) + r"\b[^{]*\{", text)
    if not m:
        return []
    start = text.find("{", m.end() - 1)
    end = find_matching(text, start, "{", "}")
    if end == -1:
        return []
    constants_block = text[start + 1:end].split(";", 1)[0]
    options = []
    for part in split_java_args(constants_block):
        name = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\b", part)
        if name:
            value = name.group(1)
            args_start = part.find("(", name.end())
            if args_start != -1:
                args_end = find_matching(part, args_start, "(", ")")
                if args_end != -1:
                    args = split_java_args(part[args_start + 1:args_end])
                    if args:
                        value = literal_expr_value(args[0]) or value
            options.append((name.group(1), value))
    return options


def constant_options(expr, current_info, java_by_fqcn, simple_java):
    class_expr, const_name = constant_reference(expr)
    if not class_expr:
        return []
    cache_key = (
        current_info.get("package", "") if current_info else "",
        tuple(sorted((current_info.get("imports", {}) if current_info else {}).items())),
        class_expr,
        const_name,
    )
    if cache_key in CONSTANT_OPTIONS_CACHE:
        return CONSTANT_OPTIONS_CACHE[cache_key]
    info = resolve_java_source_class(class_expr, current_info, java_by_fqcn, simple_java)
    if not info:
        CONSTANT_OPTIONS_CACHE[cache_key] = []
        return []
    text = strip_comments(info.get("text", ""))
    class_name = info.get("class") or simple_type_name(class_expr)
    enum_options = enum_constant_options(text, class_name)
    if enum_options and any(name == const_name for name, _ in enum_options):
        options = enum_options
        CONSTANT_OPTIONS_CACHE[cache_key] = options
        return options

    ignored_option_constants = {
        "CACHE_REGION",
        "UNIT_ID",
        "VERSION",
        "SERIAL_VERSION_UID",
    }
    const_re = re.compile(
        r"\bpublic\s+(?:static\s+final|final\s+static)\s+([\w.<>\[\]]+)\s+"
        r"([A-Z][A-Z0-9_]*)\s*(?:=\s*([^;]+))?;",
        re.S,
    )
    constants = []
    selected_type = ""
    for match in const_re.finditer(text):
        typ = match.group(1)
        name = match.group(2)
        value = literal_expr_value(match.group(3) or "")
        if name == const_name:
            selected_type = typ
        constants.append((typ, name, value))
    if not selected_type:
        CONSTANT_OPTIONS_CACHE[cache_key] = []
        return []
    selected_api_type = java_type_to_api(selected_type)
    options = [
        (name, value)
        for typ, name, value in constants
        if name not in ignored_option_constants
        if typ == selected_type or java_type_to_api(typ) == selected_api_type
    ]
    options = options[:30]
    CONSTANT_OPTIONS_CACHE[cache_key] = options
    return options


def constant_expr_value(expr, current_info, java_by_fqcn, simple_java):
    class_expr, const_name = constant_reference(expr)
    if not class_expr:
        return ""
    info = resolve_java_source_class(class_expr, current_info, java_by_fqcn, simple_java)
    if not info:
        return ""
    text = strip_comments(info.get("text", ""))
    class_name = info.get("class") or simple_type_name(class_expr)
    for name, value in enum_constant_options(text, class_name):
        if name == const_name:
            return value

    pattern = re.compile(
        r"\bpublic\s+(?:static\s+final|final\s+static)\s+[\w.<>\[\]]+\s+"
        + re.escape(const_name)
        + r"\s*(?:=\s*([^;]+))?;",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return literal_expr_value(match.group(1) or "")


def display_default_value(expr, current_info=None, java_by_fqcn=None, simple_java=None):
    value = constant_expr_value(expr, current_info, java_by_fqcn or {}, simple_java or {})
    return value or expr


def append_constant_options_description(description, expr, current_info=None, java_by_fqcn=None, simple_java=None):
    options = constant_options(expr, current_info, java_by_fqcn or {}, simple_java or {})
    if not options:
        return description
    rendered = []
    for name, value in options:
        display = value or name
        if display not in rendered:
            rendered.append(display)
    suffix = "可能值：" + "、".join(code(value) for value in rendered) + "。"
    if suffix in description:
        return description
    return (description.rstrip("。") + "；" if description else "") + suffix


def constant_expr_type(expr, current_info, java_by_fqcn, simple_java):
    expr = (expr or "").strip()
    class_expr, const_name = constant_reference(expr)
    if not class_expr:
        return ""
    cache_key = (
        current_info.get("package", "") if current_info else "",
        tuple(sorted((current_info.get("imports", {}) if current_info else {}).items())),
        class_expr,
        const_name,
    )
    if cache_key in CONSTANT_TYPE_CACHE:
        return CONSTANT_TYPE_CACHE[cache_key]
    info = resolve_java_source_class(class_expr, current_info, java_by_fqcn, simple_java)
    if not info:
        CONSTANT_TYPE_CACHE[cache_key] = ""
        return ""
    text = strip_comments(info.get("text", ""))
    pattern = re.compile(
        r"\bpublic\s+(?:static\s+final|final\s+static)\s+([\w.<>\[\]]+)\s+"
        + re.escape(const_name)
        + r"\s*(?:=\s*([^;]+))?;",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        CONSTANT_TYPE_CACHE[cache_key] = ""
        return ""
    typ = java_type_to_api(match.group(1))
    if typ in ("Object", "object", "unknown") and match.group(2):
        typ = literal_expr_type(match.group(2)) or typ
    CONSTANT_TYPE_CACHE[cache_key] = typ
    return typ


def possible_superclass_fqcns(info, java_by_fqcn, simple_java):
    info_fqcn = (info.get("package", "") + "." + info.get("class", "")).strip(".")
    if info_fqcn in SUPERCLASS_CHAIN_CACHE:
        return list(SUPERCLASS_CHAIN_CACHE[info_fqcn])
    out = []
    current = info
    seen_candidates = set()
    seen_classes = set()
    while current and current.get("extends"):
        current_fqcn = (current.get("package", "") + "." + current.get("class", "")).strip(".")
        if current_fqcn in seen_classes:
            break
        seen_classes.add(current_fqcn)
        extends = current["extends"]
        candidates = []
        if "." in extends:
            candidates.append(extends)
        typ = simple_type_name(extends)
        imported = current.get("imports", {}).get(typ)
        if imported:
            candidates.append(imported)
        if current.get("package"):
            candidates.append(current["package"] + "." + typ)
        for candidate in candidates:
            if candidate and candidate not in seen_candidates:
                seen_candidates.add(candidate)
                out.append(candidate)
        parent = resolve_java_class(extends, current, java_by_fqcn, simple_java)
        if not parent or parent is current:
            break
        current = parent
    SUPERCLASS_CHAIN_CACHE[info_fqcn] = tuple(out)
    return out


def product_prefix_from_api_fqcn(fqcn):
    parts = fqcn.split(".")
    lowered = [part.lower() for part in parts]
    if "quicksilver" in lowered:
        return "Qs"
    if len(parts) >= 3 and parts[0] in {"com", "org", "net", "cn"}:
        product = parts[2]
        return product[:1].upper() + product[1:]
    if parts:
        product = parts[0]
        return product[:1].upper() + product[1:]
    return "Qs"


def inferred_unit_from_api_fqcn(api_fqcn):
    class_name = api_fqcn.rsplit(".", 1)[-1]
    unit_name = class_name.removesuffix("ApiImpl")
    return {
        "FCode": f"{product_prefix_from_api_fqcn(api_fqcn)}.{unit_name}",
        "FApiEnabled": "0",
        "_source": f"inferred from API class path `{api_fqcn}`",
    }


def superclass_chain(info, java_by_fqcn, simple_java, fallback_entity=None):
    chain = []
    current = info
    seen = set()
    while current and current.get("extends"):
        parent = resolve_java_class(current["extends"], current, java_by_fqcn, simple_java)
        if not parent and simple_type_name(current["extends"]) == "EntityApiImpl":
            parent = fallback_entity
        if not parent:
            break
        fqcn = (parent.get("package", "") + "." + parent.get("class", "")).strip(".")
        key = fqcn or str(parent.get("path", ""))
        if key in seen:
            break
        seen.add(key)
        chain.append(parent)
        current = parent
    return chain


def inherited_api_annotations(info, java_by_fqcn, simple_java, fallback_entity=None):
    inherited = []
    seen_suffixes = set()
    for parent in superclass_chain(info, java_by_fqcn, simple_java, fallback_entity):
        for ann in api_annotations(parent["text"]):
            suffix = parse_ann_value(ann["args"], "value") or parse_ann_value(ann["args"], "path") or ann["method"]
            if suffix in seen_suffixes:
                continue
            seen_suffixes.add(suffix)
            inherited.append({
                "suffix": suffix,
                "ann": ann,
                "source_class": parent["class"],
                "source_info": parent,
            })
    return inherited


def add_fallback_api_bases(java_by_fqcn, simple_java):
    template_dir = SCRIPT_DIR.parent / "assets/templates/api-discovery/java"
    for name in ("BaseApiImpl", "EntityApiImpl", "BusinessEntityApiImpl", "TreeEntityApiImpl"):
        path = template_dir / f"{name}.java"
        if not path.exists():
            continue
        info = parse_java_class(path, SCRIPT_DIR.parent)
        fqcn = (info["package"] + "." + info["class"]).strip(".")
        if fqcn in java_by_fqcn:
            continue
        java_by_fqcn[fqcn] = info
        simple_java.setdefault(info["class"], []).append(info)


def add_java_info(info, java_by_fqcn, simple_java):
    fqcn = (info["package"] + "." + info["class"]).strip(".")
    java_by_fqcn[fqcn] = info
    simple_java.setdefault(info["class"], []).append(info)
    return fqcn


def class_shape(type_name, current_info, java_by_fqcn, simple_java, depth=0):
    if depth > 1:
        return {}
    info = resolve_java_class(type_name, current_info, java_by_fqcn, simple_java)
    if not info:
        return {}
    text = strip_comments(info["text"])
    fields = {}
    field_re = re.compile(
        r"\b(?:private|protected|public)\s+(?!static\b)(?:final\s+)?([\w.<>\[\]]+)\s+(\w+)\s*(?:=|;)",
        re.S,
    )
    for m in field_re.finditer(text):
        java_type, name = m.group(1), m.group(2)
        if name in {"serialVersionUID", "logger"}:
            continue
        typ = java_type_to_api(java_type)
        field = {
            "type": typ,
            "required": "",
            "source": simple_type_name(type_name),
            "description": "由 Java 類欄位推斷。",
        }
        fields[name] = field
    return fields


def type_arg_from_class_literal(expr):
    m = re.search(r"([\w.]+)\.class\b", expr or "")
    return m.group(1) if m else ""


def model_class_from_api(info):
    if not info:
        return ""
    m = re.search(r"super\s*\([^;]*,\s*([\w.]+)\.class", info.get("text", ""))
    if m:
        return m.group(1)
    m = re.search(r"<\s*([\w.]+Model)\s*>", info.get("extends_raw", ""))
    return m.group(1) if m else ""


def model_type_for_unit(unit, current_info=None):
    class_arg = model_class_from_api(current_info)
    if class_arg:
        return simple_type_name(class_arg)
    model_class = simple_type_name(str((unit or {}).get("FModelClassName") or ""))
    if model_class:
        return model_class
    candidates = sorted(unit_model_name_candidates(unit or {}))
    return candidates[0] if candidates else ""


def object_detail_title(field_name, field_type):
    if field_type.startswith("array<") and field_type.endswith(">"):
        inner = field_type[6:-1]
        return inner if inner != "object" else pascal_name(field_name)
    return field_type if field_type not in ("object", "array<object>") else pascal_name(field_name)


def is_exception_type(type_name):
    typ = simple_type_name(type_name)
    return typ in {"Exception", "Throwable", "RuntimeException"} or typ.endswith(("Exception", "Error"))


def java_expr_type(name, expr, var_types, current_info=None, java_by_fqcn=None, simple_java=None):
    expr = expr.strip()
    if name in ("items", "identities"):
        return "array<object>" if name == "identities" else "array"
    if name == "user":
        return "object"
    if re.search(r"(?:^|[A-Z_])(count|size|total)$|(?:Count|Size|Total)$|^pageCount$", name):
        return "int"
    if re.search(r"(?:^|[A-Z_])id$|Id$", name):
        return "uuid"
    if expr.startswith('"'):
        return "string"
    if expr in ("true", "false"):
        return "boolean"
    if re.match(r"-?\d+\b", expr):
        return "int"
    constant_type = constant_expr_type(expr, current_info, java_by_fqcn or {}, simple_java or {})
    if constant_type:
        return constant_type
    if expr.startswith("new JSONObject") or expr.startswith("JsonUtil.toJsonObject"):
        return "object"
    if expr.startswith("new JSONArray") or expr.startswith("JsonUtil.toJsonArray"):
        return "array"
    numeric_method = re.search(r"\.(getPageCount|totalSize|size|count|length)\s*\(\s*\)", expr)
    if numeric_method:
        return "int"
    var = re.match(r"(\w+)$", expr)
    if var and var.group(1) in var_types:
        return {
            "String": "string",
            "UUID": "uuid",
            "int": "int",
            "Integer": "int",
            "long": "long",
            "Long": "long",
            "boolean": "boolean",
            "Boolean": "boolean",
            "JSONObject": "object",
            "JSONArray": "array",
        }.get(var_types[var.group(1)], "object")
    getter = re.search(r"\.get(\w+)\s*\(", expr)
    if getter:
        prop = getter.group(1)
        receiver = re.search(r"\b(\w+)\.get" + re.escape(prop) + r"\s*\(", expr)
        if prop in ("Message", "StackTrace") and receiver and is_exception_type(var_types.get(receiver.group(1), "")):
            return "string"
        if prop in ("Id", "TokenId") or prop.endswith("Id"):
            return "uuid"
        if prop in ("Name", "Text", "Code", "Key") or prop.endswith(("Name", "Text", "Code", "Key")):
            return "string"
        if prop.startswith(("Is", "Has")):
            return "boolean"
        if prop in ("Identities",):
            return "array<object>"
    return "unknown"


def field_from_response_expr(name, expr, var_types, source="處理器程式碼", required="", current_info=None, java_by_fqcn=None, simple_java=None):
    typ = java_expr_type(name, expr, var_types, current_info, java_by_fqcn, simple_java)
    return {
        "type": typ,
        "required": required,
        "source": source,
        "description": append_constant_options_description(
            response_field_description(name, typ),
            expr,
            current_info,
            java_by_fqcn,
            simple_java,
        ),
    }


def response_ts_field_shape(expr, unit, field_metadata, current_info=None):
    expr = expr or ""
    if re.search(r"\bFormHome\s*\.\s*getService\s*\(\s*\)\s*\.\s*getDataJson\s*\(", expr):
        return model_type_for_unit(unit, current_info) or "object", unit_ts_field_shape(unit, field_metadata)
    if re.search(r"\bListHome\s*\.\s*getService\s*\(\s*\)\s*\.\s*getDataJson\s*\(", expr):
        model_type = model_type_for_unit(unit, current_info)
        return f"array<{model_type}>" if model_type else "array<object>", unit_ts_field_shape(unit, field_metadata)
    return "", {}


def parse_json_object_fields(expr, var_types, current_info=None, java_by_fqcn=None, simple_java=None):
    fields = {}
    m = re.match(r"JsonUtil\.toJsonObject\s*\((.*)\)\s*$", expr.strip(), re.S)
    if m:
        args = split_java_args(m.group(1))
        for i in range(0, len(args) - 1, 2):
            key = args[i].strip()
            if key.startswith('"') and key.endswith('"'):
                name = key[1:-1]
                fields[name] = field_from_response_expr(name, args[i + 1], var_types, required=True, current_info=current_info, java_by_fqcn=java_by_fqcn, simple_java=simple_java)
        return fields
    if "new JSONObject" in expr:
        for name, value in iter_put_calls(expr):
            fields[name] = field_from_response_expr(name, value, var_types, required=True, current_info=current_info, java_by_fqcn=java_by_fqcn, simple_java=simple_java)
    return fields


def response_type(record):
    ret = record["ann"]["return"]
    if record["full"]:
        return "servlet"
    if ret == "FileResult":
        return "file/binary"
    if ret == "TextResult":
        return "text"
    if ret == "XmlResult":
        return "xml"
    if ret == "JsonResult" or record["resp"]:
        return "json"
    if ret == "void":
        return "servlet"
    return "empty body / framework status only"


def analysis_status(record, available):
    if not available:
        return "unavailable（API 已發現，但目前設定下不可用）"
    unit = record["unit"]
    if unit.get("_source") and record.get("source"):
        return "confirmed（已確認）"
    return "inferred（根據繼承、設定或命名規則推斷）"


def token_requirement_text(record):
    if record["full"]:
        return "不適用（`@Api.isFullPowers=true`，開發者自行解析 request 並使用 response 回應）"
    if record.get("token_from_code"):
        if record.get("token_annotation") is False:
            return "true（處理器程式碼呼叫 `ApiContext` 參數的 `getTokenId()`；覆蓋 `@Api.isTokenRequired=false`）"
        return "true（處理器程式碼呼叫 `ApiContext` 參數的 `getTokenId()`）"
    return "true" if record["token"] else "false"


def formdata_note(record):
    if record.get("request_format") != "multipart/form-data":
        return ""
    if any(field.get("type") == "array<file>" for field in record.get("req", {}).values()):
        file_note = "可附加多個檔案欄位，後端透過 `ApiContext.getFileItems()` 讀取。"
    else:
        file_note = "可附加一個或多個檔案欄位，欄位名依 QS 上傳解析約定，後端透過 `ApiContext.getFileItem()` 讀取第一個檔案。"
    return "前端使用 `FormData`；普通參數建議放入 `args` JSON 字串，也可直接 `append`。" + file_note


def basic_info_row(label, value):
    if label.strip() in BASIC_INFO_SOURCE_LABELS:
        return None
    if value is None or value == "":
        return None
    return f"| {label} | {value} |"


def list_query_util_fields(model_type=""):
    source = "處理器程式碼 / ListQueryUtil"
    return {
        "fieldNames": {
            "type": "array<string>",
            "required": False,
            "default": "",
            "source": source,
            "description": "指定列表回傳欄位；由 `EntityApiImpl.getList` 與 `ListQueryUtil.getSelect` 讀取。",
        },
        "listId": {
            "type": "uuid",
            "required": False,
            "default": "null",
            "source": source,
            "description": "列表設定 ID；未提供時使用單元預設列表。",
        },
        "schemaId": {
            "type": "uuid",
            "required": False,
            "default": "null",
            "source": source,
            "description": "查詢方案 ID；用於套用查詢條件或排序。",
        },
        "keyword": {
            "type": "string",
            "required": False,
            "default": "null",
            "source": source,
            "description": "關鍵字查詢文字。",
        },
        "masterEntityId": {
            "type": "uuid",
            "required": False,
            "default": "null",
            "source": source,
            "description": "主單元資料 ID；與 `relationId` 搭配取得關聯資料。",
        },
        "relationId": {
            "type": "uuid",
            "required": False,
            "default": "null",
            "source": source,
            "description": "關聯設定 ID；與 `masterEntityId` 搭配取得關聯資料。",
        },
        "entityBoxFieldId": {
            "type": "uuid",
            "required": False,
            "default": "null",
            "source": source,
            "description": "選擇框欄位 ID；用於套用選擇列表固定條件。",
        },
        "listFilterCode": {
            "type": "string",
            "required": False,
            "default": "null",
            "source": source,
            "description": "列表過濾器代碼；用於套用自訂列表過濾器。",
        },
        "filtered": {
            "type": "boolean",
            "required": False,
            "default": "true",
            "source": source,
            "description": "是否套用單元業務過濾條件。",
        },
        "conditions": {
            "type": "array<object>",
            "required": False,
            "default": "",
            "source": source,
            "description": "查詢條件列表；由 `ConditionModel` 轉換為查詢條件。",
        },
        "includeSelf": {
            "type": "boolean",
            "required": False,
            "default": "false",
            "source": source,
            "description": "關聯查詢時是否包含自身資料。",
        },
        "includeIndirectSub": {
            "type": "boolean",
            "required": False,
            "default": "false",
            "source": source,
            "description": "關聯查詢時是否包含間接下級資料。",
        },
        "forms": {
            "type": model_type or "object",
            "required": False,
            "default": "",
            "source": source,
            "description": "選擇列表固定條件所需的目前單元模型資料物件；由 `ListQueryUtil.getFilter` 讀取。",
        },
        "listFilterArgs": {
            "type": "array<object>",
            "required": False,
            "default": "",
            "source": source,
            "description": "列表過濾器參數列表。",
        },
        "order": {
            "type": "array<string>",
            "required": False,
            "default": "",
            "source": source,
            "description": "客戶端排序欄位列表；每項通常為 `field asc` 或 `field desc`。",
        },
    }


def merge_code_inferred_fields(fields, extra_fields):
    for name, field in extra_fields.items():
        if name not in fields:
            fields[name] = field
            continue
        current = fields[name]
        if current.get("type") in ("", "unknown", "array") and field.get("type"):
            current["type"] = field["type"]
        if current.get("required", "") == "" and field.get("required", "") != "":
            current["required"] = field["required"]
        if current.get("default", "") == "" and field.get("default", "") != "":
            current["default"] = field["default"]
        current["source"] = merge_source(current.get("source", ""), field.get("source", ""))
        if field.get("description") and (
            not current.get("description")
            or current.get("description") in {
                "從 request JSON 讀取。",
                "值列表；項目類型由處理器讀取邏輯推斷。",
                "物件列表；項目屬性依處理器邏輯或執行時元資料而定。",
            }
        ):
            current["description"] = field["description"]


def extract_fields(body, current_info=None, java_by_fqcn=None, simple_java=None, unit=None, field_metadata=None):
    java_by_fqcn = java_by_fqcn or {}
    simple_java = simple_java or {}
    body_nc = strip_comments(body)
    req_var = None
    m = re.search(r"JSONObject\s+(\w+)\s*=\s*\w+\.getRequestJson\s*\(", body_nc)
    if m:
        req_var = m.group(1)

    var_types = {}
    type_re = r"[\w.]+(?:<[\w.?,\s]+>)?(?:\[\])?"
    for m in re.finditer(r"\b(" + type_re + r")\s+(\w+)\s*(?:=|;)", body_nc):
        var_types[m.group(2)] = m.group(1)
    for m in re.finditer(r"\bcatch\s*\(\s*(" + type_re + r")\s+(\w+)\s*\)", body_nc):
        var_types[m.group(2)] = m.group(1)
    result_vars = {
        name
        for name, typ in var_types.items()
        if typ in ("JsonResult", "XmlResult")
    }
    for m in re.finditer(r"\b(JsonResult|XmlResult)\s+(\w+)\s*(?:=|;)", body_nc):
        var_types[m.group(2)] = m.group(1)
        result_vars.add(m.group(2))

    fields = {}
    req_objects = {}
    if re.search(r"\.\s*getFileItems\s*\(", body_nc):
        fields["files"] = {
            "type": "array<file>",
            "required": True,
            "default": "",
            "source": "處理器程式碼 / ApiContext",
            "description": "由 `ApiContext.getFileItems()` 讀取的上傳檔案集合；請以 `multipart/form-data` 傳入。",
        }
    elif re.search(r"\.\s*getFileItem\s*\(", body_nc):
        fields["file"] = {
            "type": "file",
            "required": True,
            "default": "",
            "source": "處理器程式碼 / ApiContext",
            "description": "由 `ApiContext.getFileItem()` 讀取的上傳檔案；請以 `multipart/form-data` 傳入。",
        }
    if req_var:
        helper_types = {
            "String": "string",
            "Uuid": "uuid",
            "UUID": "uuid",
            "Int": "int",
            "Integer": "int",
            "Long": "long",
            "Boolean": "boolean",
            "Bool": "boolean",
            "Object": "object",
            "JSONObject": "object",
            "JSONArray": "array",
            "ObjectArray": "array<object>",
            "StringArray": "array<string>",
            "UuidArray": "array<uuid>",
            "UUIDArray": "array<uuid>",
            "IntArray": "array<int>",
        }
        for m in re.finditer(r"JsonUtil\.(get|opt)(\w+)\s*\(\s*" + req_var + r"\s*,\s*\"([^\"]+)\"([^)]*)\)", body_nc):
            required = m.group(1) == "get"
            typ = helper_types.get(m.group(2), m.group(2).lower())
            extra = m.group(4)
            default = ""
            if "Array" in m.group(2):
                bm = re.search(r",\s*(true|false)\s*$", extra.strip())
                if bm:
                    required = bm.group(1) == "true"
            elif extra.strip().startswith(","):
                required = False
                default = extra.strip()[1:].strip()
                if "(" in default or ")" in default:
                    default = ""
            if m.group(2) in ("Object", "JSONObject") and extra.strip().startswith(","):
                args_tail = extra.strip()[1:].strip()
                if not args_tail.startswith("null"):
                    required = True
                    default = ""
                else:
                    required = False
                    default = "null"
            field_name = m.group(3)
            field_type = typ
            default_expr = default
            default = display_default_value(default_expr, current_info, java_by_fqcn, simple_java)
            class_arg = type_arg_from_class_literal(extra)
            if class_arg and m.group(2) in ("Object", "JSONObject", "ObjectArray"):
                cls_name = simple_type_name(class_arg)
                field_type = f"array<{cls_name}>" if m.group(2) == "ObjectArray" else cls_name
            elif "getModelClass" in extra and m.group(2) in ("Object", "JSONObject", "ObjectArray"):
                model_type = model_type_for_unit(unit, current_info)
                if model_type:
                    field_type = f"array<{model_type}>" if m.group(2) == "ObjectArray" else model_type
            fields[field_name] = {
                "type": field_type,
                "required": required,
                "default": default,
                "source": "處理器程式碼",
                "description": append_constant_options_description(
                    request_field_description(field_name, typ),
                    default_expr,
                    current_info,
                    java_by_fqcn,
                    simple_java,
                ),
            }
            if class_arg:
                shape = resolve_ts_field_shape(class_arg, current_info, java_by_fqcn, simple_java, unit, field_metadata)
                if not shape:
                    shape = class_shape(class_arg, current_info, java_by_fqcn, simple_java)
                if shape:
                    req_objects[field_name] = {
                        "title": object_detail_title(field_name, field_type),
                        "fields": shape,
                    }

        for m in re.finditer(req_var + r"\.(get|opt)(String|Int|Long|Boolean|JSONObject|JSONArray)\s*\(\s*\"([^\"]+)\"([^)]*)\)", body_nc):
            typ = {
                "String": "string",
                "Int": "int",
                "Long": "long",
                "Boolean": "boolean",
                "JSONObject": "object",
                "JSONArray": "array",
            }[m.group(2)]
            required = m.group(1) == "get"
            default = ""
            if m.group(4).strip().startswith(","):
                required = False
                default = m.group(4).strip()[1:].strip()
                if "(" in default or ")" in default:
                    default = ""
            default_expr = default
            default = display_default_value(default_expr, current_info, java_by_fqcn, simple_java)
            fields[m.group(3)] = {
                "type": typ,
                "required": required,
                "default": default,
                "source": "處理器程式碼",
                "description": append_constant_options_description(
                    request_field_description(m.group(3), typ),
                    default_expr,
                    current_info,
                    java_by_fqcn,
                    simple_java,
                ),
            }

    if req_var:
        for m in re.finditer(r"JsonUtil\.(getObject|getObjectArray)\s*\(\s*" + req_var + r"\s*,\s*\"([^\"]+)\"(.*?)\)", body_nc, re.S):
            helper, field_name, tail = m.group(1), m.group(2), m.group(3)
            class_arg = type_arg_from_class_literal(tail)
            if not class_arg and "getModelClass" in tail:
                class_arg = model_class_from_api(current_info)
            uses_current_unit_model = "getModelClass" in tail and not class_arg
            if not class_arg and not uses_current_unit_model:
                continue
            cls_name = simple_type_name(class_arg)
            if uses_current_unit_model:
                model_type = model_type_for_unit(unit, current_info)
                if model_type:
                    field_type = f"array<{model_type}>" if helper == "getObjectArray" else model_type
                else:
                    field_type = "array<object>" if helper == "getObjectArray" else "object"
                fields.setdefault(field_name, {
                    "type": field_type,
                    "required": "null," not in tail,
                    "default": "null" if "null," in tail else "",
                    "source": "處理器程式碼",
                    "description": request_field_description(field_name, field_type),
                })
                shape = resolve_ts_field_shape(class_arg, current_info, java_by_fqcn, simple_java, unit, field_metadata)
                if shape:
                    req_objects[field_name] = {
                        "title": object_detail_title(field_name, field_type),
                        "fields": shape,
                    }
                continue
            field_type = f"array<{cls_name}>" if helper == "getObjectArray" and cls_name else cls_name
            fields.setdefault(field_name, {
                "type": field_type,
                "required": "null," not in tail,
                "default": "null" if "null," in tail else "",
                "source": "處理器程式碼",
                "description": request_field_description(field_name, "array<object>" if helper == "getObjectArray" else "object"),
            })
            fields[field_name]["type"] = field_type
            shape = resolve_ts_field_shape(class_arg, current_info, java_by_fqcn, simple_java, unit, field_metadata)
            if not shape:
                shape = class_shape(class_arg, current_info, java_by_fqcn, simple_java)
            if shape:
                req_objects[field_name] = {
                    "title": object_detail_title(field_name, field_type),
                    "fields": shape,
                }

    if re.search(r"\bgetListDataSet\s*\(", body_nc) or re.search(r"\bListQueryUtil\s*\.\s*get(?:Select|Filter|Order)\s*\(", body_nc):
        model_type = model_type_for_unit(unit, current_info)
        merge_code_inferred_fields(fields, list_query_util_fields(model_type))
        forms_shape = unit_ts_field_shape(unit, field_metadata)
        if model_type and forms_shape:
            req_objects["forms"] = {
                "title": model_type,
                "fields": forms_shape,
            }

    object_details_by_var = {}
    for m in re.finditer(r"JSONObject\s+(\w+)\s*=\s*(new\s+JSONObject\s*\(\).*?);", body_nc, re.S):
        details = parse_json_object_fields(m.group(2), var_types, current_info, java_by_fqcn, simple_java)
        if details:
            object_details_by_var[m.group(1)] = details
    for var in [v for v, t in var_types.items() if t == "JSONObject"]:
        chunks = []
        for m in re.finditer(r"\b" + re.escape(var) + r"\.put\s*\(", body_nc):
            paren = m.end() - 1
            end = find_matching(body_nc, paren, "(", ")")
            if end != -1:
                chunks.append(".put(" + body_nc[paren + 1:end] + ")")
        if chunks:
            object_details_by_var.setdefault(var, {})
            for name, value in iter_put_calls("".join(chunks)):
                object_details_by_var[var][name] = field_from_response_expr(name, value, var_types, required=True, current_info=current_info, java_by_fqcn=java_by_fqcn, simple_java=simple_java)

    responses = {}
    resp_objects = {}
    for receiver, name, expr in iter_receiver_put_calls(body_nc):
        if result_vars and receiver not in result_vars:
            continue
        details = {}
        inferred_response_type = ""
        expr = expr.strip()
        if expr in object_details_by_var:
            details = object_details_by_var[expr]
        elif expr.startswith("JsonUtil.toJsonObject") or expr.startswith("new JSONObject"):
            details = parse_json_object_fields(expr, var_types, current_info, java_by_fqcn, simple_java)
        else:
            inferred_response_type, details = response_ts_field_shape(expr, unit, field_metadata, current_info)
        field = field_from_response_expr(name, expr, var_types, current_info=current_info, java_by_fqcn=java_by_fqcn, simple_java=simple_java)
        if details:
            field["type"] = inferred_response_type or (pascal_name(name) or "object")
            field["description"] = response_field_description(name, field["type"])
            resp_objects[name] = {
                "title": object_detail_title(name, field["type"]),
                "fields": details,
            }
        else:
            var = re.match(r"(\w+)$", expr)
            if var and var.group(1) in var_types:
                java_type = var_types[var.group(1)]
                shape = class_shape(java_type, current_info, java_by_fqcn, simple_java)
                if shape:
                    field["type"] = java_type_to_api(java_type)
                    field["description"] = f"{simple_type_name(java_type)} 物件。"
                    resp_objects[name] = {
                        "title": object_detail_title(name, field["type"]),
                        "fields": shape,
                    }
        responses[name] = field

    params = {}
    for m in re.finditer(r"getParameter\s*\(\s*\"([^\"]+)\"\s*\)", body_nc):
        params[m.group(1)] = {
            "type": "string",
            "required": False,
            "default": "",
            "source": "處理器程式碼",
            "description": "由 `request.getParameter` 讀取。",
        }

    headers = {}
    for m in re.finditer(r"getHeader\s*\(\s*\"([^\"]+)\"\s*\)", body_nc):
        headers[m.group(1)] = {
            "type": "string",
            "required": False,
            "default": "",
            "source": "處理器程式碼",
            "description": "由 `request.getHeader` 讀取。",
        }

    return fields, req_objects, responses, params, headers, resp_objects


def unit_field_signature(unit, field_metadata):
    if not unit or not field_metadata:
        return ""
    fields = field_metadata.get("fields_by_unit_id", {}).get(unit.get("FId"), {})
    return "|".join(
        f"{name}:{field.get('FTitle', '')}:{field.get('FType', '')}:{field.get('FRequired', '')}:{field.get('FSize', '')}"
        for name, field in sorted(fields.items())
    )


def cached_extract_fields(record, current_info=None, java_by_fqcn=None, simple_java=None, unit=None, field_metadata=None):
    body = record.get("body", "")
    if len(body) > DEEP_FIELD_SCAN_MAX_METHOD_BODY_SIZE:
        return empty_field_extraction()
    current_key = ""
    if current_info:
        current_key = "|".join([
            current_info.get("package", ""),
            current_info.get("class", ""),
            current_info.get("extends_raw", ""),
            repr(sorted(current_info.get("imports", {}).items())),
            model_class_from_api(current_info),
        ])
    body_key = hashlib.sha1(body.encode("utf-8", "ignore")).hexdigest()
    key = (body_key, len(body), current_key, unit_field_signature(unit, field_metadata))
    if key not in FIELD_EXTRACTION_CACHE:
        FIELD_EXTRACTION_CACHE[key] = extract_fields(body, current_info, java_by_fqcn, simple_java, unit, field_metadata)
    req, req_objects, resp, params, headers, resp_objects = FIELD_EXTRACTION_CACHE[key]
    return dict(req), dict(req_objects), dict(resp), dict(params), dict(headers), dict(resp_objects)


def inferred_request_format(ann_args, req):
    request_format = parse_ann_enum_value(ann_args, "requestFormat") or "default"
    if request_format in ("default", "json") and any(field.get("type") in {"file", "array<file>"} for field in req.values()):
        return "multipart/form-data"
    return request_format


def token_required_from_code(ann):
    params = strip_comments(ann.get("params", ""))
    body = strip_comments(ann.get("body", ""))
    api_context_params = {
        match.group(1)
        for match in re.finditer(r"\bApiContext\s+(\w+)\b", params)
    }
    return any(
        re.search(rf"\b{re.escape(var)}\s*\.\s*getTokenId\s*\(", body)
        for var in api_context_params
    )


def inferred_http_method(record):
    request_format = record.get("request_format") or "default"
    if request_format == "multipart/form-data":
        return "POST"
    if record.get("req"):
        return "POST"
    if request_format not in ("default", ""):
        return "POST"
    if record.get("params"):
        return "GET"
    if response_type(record) == "file/binary":
        return "GET"
    return "POST"


def empty_field_extraction():
    return {}, {}, {}, {}, {}, {}


def should_skip_deep_field_scan(info, annotations):
    text_size = len(info.get("text", "")) if info else 0
    return len(annotations) > DEEP_FIELD_SCAN_MAX_API_COUNT or text_size > DEEP_FIELD_SCAN_MAX_TEXT_SIZE


def compact_annotation(ann):
    return {
        "method": ann.get("method", ""),
        "return": ann.get("return", ""),
        "description": parse_ann_value(ann.get("args", ""), "description") or "",
        "since": parse_ann_value(ann.get("args", ""), "since") or "",
        "comment": ann.get("comment", ""),
    }


def human_unit_name(unit):
    name = (unit or {}).get("FName") or ""
    if name:
        return name
    code_value = (unit or {}).get("FCode") or ""
    if "." in code_value:
        return code_value.rsplit(".", 1)[-1]
    return code_value


def split_identifier_words(value):
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value or "")
    parts = [part.lower() for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    known_compounds = {
        "bindemployee": ["bind", "employee"],
        "callstatus": ["call", "status"],
        "chatmessage": ["chat", "message"],
        "chatworkgroup": ["chat", "work", "group"],
        "contactlabel": ["contact", "label"],
        "downloadfax": ["download", "fax"],
        "extensioncall": ["extension", "call"],
        "extenstioncall": ["extension", "call"],
        "expresschat": ["express", "chat"],
        "servicerequest": ["service", "request"],
        "timereport": ["time", "report"],
        "timereportdetail": ["time", "report", "detail"],
        "transferfax": ["transfer", "fax"],
        "workingdays": ["working", "days"],
    }
    words = []
    for part in parts:
        words.extend(known_compounds.get(part, [part]))
    return words


def api_usage_evidence_words(record):
    suffix = record.get("suffix") or ""
    path = record.get("path") or ""
    method = record.get("ann", {}).get("method") or ""
    words = []
    words.extend(split_identifier_words(method))
    for segment in re.split(r"[/_.-]+", suffix + "/" + path):
        if not segment or segment in {"openapi", "qs"} or segment.startswith("{"):
            continue
        words.extend(split_identifier_words(segment))
    return words


def has_any(words, candidates):
    word_set = set(words)
    return any(candidate in word_set for candidate in candidates)


def translate_path_target(parts):
    word_map = {
        "captcha": "驗證碼",
        "id": "ID",
        "image": "圖片",
        "key": "金鑰",
        "login": "登入",
        "role": "角色",
        "token": "Token",
        "user": "員工",
    }
    translated = [word_map.get(part) for part in parts]
    if not translated or any(part is None for part in translated):
        return ""
    text = ""
    for part in translated:
        if text and re.fullmatch(r"[A-Z0-9]+", part):
            text += " "
        text += part
    return text


def usage_target_from_suffix(parts):
    ignored = {"api", "ecp", "gpt", "mk", "openapi", "qs"}
    action_words = {
        "add", "apply", "assign", "bind", "create", "deal", "delete", "discard", "execute",
        "download", "fetch", "finish", "item", "new", "revise", "save", "send", "start",
        "status", "stop", "submit", "transfer", "update", "upgrade",
    }
    target_words = []
    for part in parts:
        words = split_identifier_words(part)
        if not words or all(word in ignored for word in words):
            continue
        if all(word in action_words for word in words):
            continue
        target_words.extend(words)
    return translate_business_words(target_words)


def translate_business_words(parts):
    word_map = {
        "account": "帳號",
        "add": "新增",
        "agent": "客服",
        "answer": "答案",
        "api": "API",
        "app": "應用",
        "activity": "活動",
        "attachment": "附件",
        "avatar": "頭像",
        "auth": "驗證",
        "batch": "批次",
        "binded": "綁定",
        "bot": "機器人",
        "captcha": "驗證碼",
        "ccfax": "傳真",
        "catalog": "目錄",
        "call": "通話",
        "channel": "渠道",
        "chat": "聊天",
        "comment": "評論",
        "config": "設定",
        "contact": "聯絡人",
        "copilot": "Copilot",
        "content": "內容",
        "data": "資料",
        "department": "部門",
        "dev": "開發",
        "days": "天數",
        "employee": "員工",
        "entity": "資料",
        "extension": "分機",
        "extenstion": "分機",
        "express": "快速",
        "fans": "粉絲",
        "fax": "傳真",
        "file": "檔案",
        "form": "表單",
        "function": "功能",
        "gateway": "Gateway",
        "group": "群組",
        "icon": "頭像",
        "id": "ID",
        "image": "圖片",
        "info": "資訊",
        "item": "項目",
        "key": "金鑰",
        "knowledge": "知識",
        "limits": "限制",
        "list": "列表",
        "login": "登入",
        "media": "媒體",
        "member": "會員",
        "message": "消息",
        "note": "備註",
        "notification": "通知",
        "offline": "離線",
        "original": "原始",
        "page": "頁面",
        "password": "密碼",
        "post": "貼文",
        "prompt": "提示詞",
        "privilege": "權限",
        "question": "問題",
        "queue": "佇列",
        "report": "報表",
        "request": "請求",
        "reply": "回覆",
        "role": "角色",
        "room": "聊天室",
        "score": "評分",
        "service": "服務",
        "search": "搜尋",
        "setting": "設定",
        "status": "狀態",
        "summary": "摘要",
        "survey": "問卷",
        "tag": "標籤",
        "tenant": "租戶",
        "test": "測試",
        "token": "Token",
        "transfer": "轉發",
        "type": "類型",
        "unit": "單元",
        "user": "使用者",
        "workflow": "流程",
        "work": "工作",
        "time": "時間",
        "video": "視訊",
        "web": "網頁",
        "working": "工作",
    }
    translated = []
    for part in parts:
        if not part:
            continue
        translated.append(word_map.get(part, part))
    text = ""
    for part in translated:
        if text and re.fullmatch(r"[A-Z0-9]+", part):
            text += " "
        text += part
    return text


def route_words(parts):
    words = []
    for part in parts:
        words.extend(split_identifier_words(part))
    return words


def route_target_words(words, action_words):
    ignored = {"api", "ecp", "gpt", "mk", "openapi", "qs"}
    return [word for word in words if word not in ignored and word not in action_words]


def route_usage_description(suffix_parts, path_parts):
    words = route_words(suffix_parts + path_parts)
    word_set = set(words)
    if not words:
        return ""

    if "download" in word_set:
        target = translate_business_words(route_target_words(words, {"download"}))
        if target == "傳真":
            return "下載傳真檔案。"
        if target:
            return f"下載{target}。"

    if "transfer" in word_set:
        target = translate_business_words(route_target_words(words, {"transfer"}))
        if target:
            return f"轉發{target}。"

    if "status" in word_set:
        target = translate_business_words(route_target_words(words, {"status"}))
        if target:
            return f"查詢{target}狀態。"

    return ""


def method_name_description(method_name, fallback_target=""):
    words = split_identifier_words(method_name)
    if not words:
        return ""
    verb_map = {
        "add": "新增",
        "append": "追加",
        "apply": "申請",
        "assign": "指派",
        "bind": "綁定",
        "cancel": "取消",
        "change": "修改",
        "check": "檢查",
        "clear": "清除",
        "close": "關閉",
        "create": "建立",
        "delete": "刪除",
        "discard": "放棄",
        "disable": "停用",
        "do": "執行",
        "download": "下載",
        "edit": "編輯",
        "enable": "啟用",
        "execute": "執行",
        "deal": "處理",
        "find": "查詢",
        "finish": "完成",
        "generate": "產生",
        "get": "取得",
        "has": "判斷是否存在",
        "ask": "詢問",
        "import": "匯入",
        "insert": "新增",
        "invite": "邀請",
        "is": "判斷是否",
        "list": "查詢",
        "load": "載入",
        "new": "新增",
        "query": "查詢",
        "prepare": "準備",
        "register": "註冊",
        "remove": "移除",
        "reset": "重設",
        "revise": "修訂",
        "save": "儲存",
        "score": "評分",
        "search": "搜尋",
        "send": "發送",
        "set": "設定",
        "start": "啟動",
        "stop": "停止",
        "submit": "提交",
        "sync": "同步",
        "transfer": "轉發",
        "unbind": "解除綁定",
        "update": "更新",
        "upload": "上傳",
        "upgrade": "升級",
        "validate": "驗證",
        "verify": "驗證",
    }
    verb_index = 0
    if words[0] not in verb_map:
        for i, word in enumerate(words[1:], start=1):
            if word in verb_map:
                verb_index = i
                break
        else:
            if words[-1] == "status":
                target = translate_business_words(words[:-1])
                return f"查詢{target}狀態。" if target else ""
            target = translate_business_words(words) or fallback_target
            return f"處理{target}。" if target else ""
    verb = words[verb_index]
    action = verb_map.get(verb)
    if not action:
        return ""
    prefix = translate_business_words(words[:verb_index])
    target = translate_business_words(words[verb_index + 1:])
    if not target and prefix and verb != "is":
        target = prefix
    if not target:
        target = fallback_target
    if not target:
        return ""
    if verb == "is" and prefix:
        return f"判斷{prefix}是否{target}。"
    return f"{action}{target}。"


def participates_in_usage_target(record):
    if "entity_api" in record:
        return record["entity_api"]
    entity_api_from_unit = unit_participates_in_usage_target(record.get("unit", {}))
    return True if entity_api_from_unit is None else entity_api_from_unit


def unit_participates_in_usage_target(unit):
    edit_id = str((unit or {}).get("FEditId") or "").strip().lower()
    if edit_id in ENTITY_EDIT_IDS:
        return True
    if edit_id in NON_ENTITY_EDIT_IDS:
        return False
    return None


def unit_supports_workflow(unit):
    return str((unit or {}).get("FSupportWorkflow") or "").strip().lower() in {"1", "true", "yes"}


def should_export_inherited_api(unit, suffix):
    if suffix in WORKFLOW_API_SUFFIXES and not unit_supports_workflow(unit):
        return False
    return True


def api_usage_description(record):
    annotation_description = (record.get("ann", {}).get("description") or "").strip()
    method_comment = (record.get("ann", {}).get("comment") or "").strip()
    if annotation_description:
        return annotation_description
    if method_comment:
        return method_comment
    unit_name = human_unit_name(record.get("unit", {}))
    suffix = (record.get("suffix") or "").strip("/").lower()
    path = (record.get("path") or "").strip("/").lower()
    suffix_parts = [part for part in suffix.split("/") if part]
    path_parts = [part for part in path.split("/") if part]
    method = (record.get("ann", {}).get("method") or "").strip()
    method_lower = method.lower()
    evidence_words = api_usage_evidence_words(record)
    evidence_word_set = set(evidence_words)
    target = unit_name if participates_in_usage_target(record) else ""
    path_target = translate_path_target([part for part in suffix_parts if part != "misc"])
    route_target = usage_target_from_suffix(suffix_parts) or usage_target_from_suffix(path_parts)
    method_description = method_name_description(method, target or path_target or route_target)
    route_description = route_usage_description(suffix_parts, path_parts)

    if {"token", "apply"}.issubset(evidence_word_set) or method_lower in {"applytoken", "tokenapply"}:
        return "申請並取得 API Token。"
    if {"token", "refresh"}.issubset(evidence_word_set) or method_lower in {"refreshtoken", "tokenrefresh"}:
        return "刷新 API Token。"
    if {"token", "revoke"}.issubset(evidence_word_set) or method_lower in {"revoketoken", "tokenrevoke"}:
        return "撤銷 API Token。"
    if route_description:
        return route_description
    if "upload" in evidence_word_set or method_lower in {"upload", "uploadfile"}:
        if target:
            return f"上傳{target}相關檔案。"
    if "download" in evidence_word_set or method_lower in {"download", "downloadfile"}:
        if target:
            return f"下載{target}相關檔案。"
    if method_lower.startswith(("get", "fetch", "load")):
        get_target = path_target or target
        if get_target:
            return f"取得{get_target}。"
    if record.get("ann", {}).get("return") == "FileResult" and path_target:
        return f"取得{path_target}。"
    if "password" in evidence_word_set and has_any(evidence_words, {"modify", "change", "update"}):
        return "修改帳號密碼。"
    if "password" in evidence_word_set and "reset" in evidence_word_set:
        return "重設帳號密碼。"
    if has_any(evidence_words, {"login", "signin"}):
        return "執行登入驗證。"
    if has_any(evidence_words, {"logout", "signout"}):
        return "登出並結束目前登入狀態。"
    if "import" in evidence_word_set:
        if target:
            return f"匯入{target}資料。"
    if "export" in evidence_word_set:
        if target:
            return f"匯出{target}資料。"
    if method_description:
        return method_description
    return ""


def clear_runtime_caches():
    API_ANNOTATION_CACHE.clear()
    FIELD_EXTRACTION_CACHE.clear()
    SUPERCLASS_CHAIN_CACHE.clear()
    JAVA_SOURCE_CLASS_CACHE.clear()
    CONSTANT_TYPE_CACHE.clear()
    CONSTANT_OPTIONS_CACHE.clear()
    gc.collect()


def route_for(prefix, suffix):
    suffix = (suffix or "").strip()
    if suffix.startswith("/"):
        return "openapi/" + suffix.lstrip("/").replace("*", "{path}")
    if suffix:
        return "openapi/" + prefix.strip("/") + "/" + suffix.strip("/")
    return "openapi/" + prefix.strip("/")


def module_name_for_path(path, modules):
    path = Path(path)
    for module in modules:
        try:
            path.relative_to(module)
            return module.name
        except ValueError:
            continue
    return ""


def unit_prefix(code):
    token = code.lower().replace(".", "_")
    if "_" in token:
        left, right = token.split("_", 1)
        return left + "/" + right
    return token


def derive_project_name(root, modules):
    names = [p.name for p in modules]
    prefixes = []
    for name in names:
        if "-module-" in name:
            prefixes.append(name.split("-module-", 1)[0])
    prefixes.extend(
        p.name.rsplit("-", 1)[0]
        for p in root.iterdir()
        if p.is_dir() and (p.name.endswith("-run") or p.name.endswith("-build"))
    )
    uniq = sorted(set(prefixes))
    return uniq[0] if len(uniq) == 1 else root.name


def discover_modules(root):
    modules = []
    settings = root / "settings.gradle"
    included = []
    if settings.exists():
        text = read(settings)
        included = re.findall(r"include\s+['\"]([^'\"]+-module-[^'\"]+)['\"]", text)
    for name in included:
        p = root / name
        if p.exists():
            modules.append(p)
    for p in sorted(root.iterdir()):
        if p.is_dir() and "-module-" in p.name and p not in modules:
            modules.append(p)
    return sorted(
        [m for m in modules if (m / "build.gradle").exists() or (m / "src/main/java").exists() or (m / "src/main/resources/QS-MODULE").exists()],
        key=lambda p: p.name,
    )


def resolve_project_root(path):
    root = Path(path).resolve()
    if discover_modules(root):
        return root
    if "-module-" in root.name and (
        (root / "build.gradle").exists()
        or (root / "src/main/java").exists()
        or (root / "src/main/resources/QS-MODULE").exists()
    ):
        parent = root.parent
        if discover_modules(parent):
            return parent
    return root


def build_records(root):
    global JAVA_SOURCE_ROOTS
    modules = discover_modules(root)
    JAVA_SOURCE_ROOTS = [module / "src/main/java" for module in modules if (module / "src/main/java").exists()]
    java_by_fqcn = {}
    for module in modules:
        src_root = module / "src/main/java"
        if not src_root.exists():
            continue
        for path in src_root.rglob("*ApiImpl.java"):
            if "/api/impl/" not in str(path):
                continue
            info = parse_java_class(path, root)
            add_java_info(info, java_by_fqcn, {})
    simple_java = {}
    for info in java_by_fqcn.values():
        simple_java.setdefault(info["class"], []).append(info)
    add_fallback_api_bases(java_by_fqcn, simple_java)

    units = {}
    fields_by_unit_id = {}
    module_sql_metadata = {}
    for module in modules:
        metadata = parse_module_sql_metadata(module)
        module_sql_metadata[module.name] = metadata
        units.update(parse_units(module, metadata))
        for unit_id, fields in parse_fields(module, metadata).items():
            fields_by_unit_id.setdefault(unit_id, {}).update(fields)
    field_metadata = {
        "units": units,
        "fields_by_unit_id": fields_by_unit_id,
    }

    units_by_api = {}
    units_by_home = {}
    for unit in units.values():
        if unit.get("FApiClassName"):
            units_by_api.setdefault(unit["FApiClassName"], []).append(unit)
        if unit.get("FHomeClassName"):
            units_by_home[unit["FHomeClassName"]] = unit

    fallback_entity = java_by_fqcn.get("com.jeedsoft.quicksilver.base.api.impl.EntityApiImpl")

    records = {}
    for fqcn, info in sorted(java_by_fqcn.items()):
        if "/api/impl/" not in str(info["path"]) or not info["class"].endswith("ApiImpl"):
            continue
        if info["class"] in TOP_LEVEL_API_BASE_CLASSES:
            continue

        anns = api_annotations(info["text"])
        skip_deep_scan = should_skip_deep_field_scan(info, anns)
        bound_units = units_by_api.get(fqcn, [])
        if not bound_units:
            for parent_fqcn in possible_superclass_fqcns(info, java_by_fqcn, simple_java):
                bound_units = units_by_api.get(parent_fqcn, [])
                if bound_units:
                    break
                base_unit = find_base_unit_by_api(parent_fqcn)
                if base_unit:
                    units[base_unit.get("FId") or base_unit.get("FCode") or parent_fqcn] = base_unit
                    if base_unit.get("FApiClassName"):
                        units_by_api.setdefault(base_unit["FApiClassName"], []).append(base_unit)
                    if base_unit.get("FHomeClassName"):
                        units_by_home[base_unit["FHomeClassName"]] = base_unit
                    bound_units = [base_unit]
                    break
        if not bound_units:
            for m in re.finditer(r"super\s*\(\s*([A-Za-z0-9_]+Home)\.UNIT_ID", info["text"]):
                simple_home = m.group(1)
                for home_fqcn, unit in units_by_home.items():
                    if home_fqcn.endswith("." + simple_home):
                        bound_units = [unit]
                        break
        if not bound_units:
            simple = info["class"].removesuffix("ApiImpl")
            for unit in units.values():
                if unit.get("FApiClassName") == fqcn or (unit.get("FCode") or "").lower().endswith("." + simple.lower()):
                    bound_units.append(unit)

        superclass_fqcns = possible_superclass_fqcns(info, java_by_fqcn, simple_java)
        entity_api_from_class = any(simple_type_name(parent_fqcn) == "EntityApiImpl" for parent_fqcn in superclass_fqcns)
        inferred_api_fqcn = superclass_fqcns[0] if superclass_fqcns else fqcn
        inferred_unit = inferred_unit_from_api_fqcn(inferred_api_fqcn)
        module_name = module_name_for_path(info["path"], modules)
        for unit in bound_units or [inferred_unit]:
            entity_api_from_unit = unit_participates_in_usage_target(unit)
            entity_api = entity_api_from_class if entity_api_from_unit is None else entity_api_from_unit
            prefix = unit_prefix(unit.get("FCode") or inferred_unit["FCode"])
            for ann in anns:
                suffix = parse_ann_value(ann["args"], "value") or parse_ann_value(ann["args"], "path") or ann["method"]
                path = route_for(prefix, suffix)
                if skip_deep_scan:
                    req, req_objects, resp, params, headers, resp_objects = empty_field_extraction()
                else:
                    req, req_objects, resp, params, headers, resp_objects = cached_extract_fields(ann, info, java_by_fqcn, simple_java, unit, field_metadata)
                merge_annotation_fields(req, parse_api_attributes(ann["args"], "input"))
                merge_annotation_fields(resp, parse_api_attributes(ann["args"], "output"))
                full = parse_ann_bool(ann["args"], "isFullPowers", False)
                token_annotation = parse_ann_bool(ann["args"], "isTokenRequired", True)
                token_from_code = token_required_from_code(ann)
                records[path] = {
                    "path": path,
                    "fqcn": fqcn,
                    "ann": compact_annotation(ann),
                    "unit": unit,
                    "module_name": module_name,
                    "entity_api": entity_api,
                    "inherited": False,
                    "source": f"{info['rel']}:{ann['line']}",
                    "suffix": suffix,
                    "req": req,
                    "req_objects": req_objects,
                    "resp": resp,
                    "resp_objects": resp_objects,
                    "params": params,
                    "headers": headers,
                    "token": False if full else (token_annotation or token_from_code),
                    "token_annotation": token_annotation,
                    "token_from_code": False if full else token_from_code,
                    "always": parse_ann_bool(ann["args"], "isAlwaysEnabled", False),
                    "full": full,
                    "request_format": inferred_request_format(ann["args"], req),
                    "response_format": parse_ann_enum_value(ann["args"], "responseFormat") or "default",
                }

            inherited = inherited_api_annotations(info, java_by_fqcn, simple_java, fallback_entity)
            if inherited and str(unit.get("FApiEnabled")) == "1":
                concrete_suffixes = {
                    parse_ann_value(a["args"], "value") or parse_ann_value(a["args"], "path") or a["method"]
                    for a in anns
                }
                for inherited_api in inherited:
                    suffix = inherited_api["suffix"]
                    ann = inherited_api["ann"]
                    if suffix in concrete_suffixes:
                        continue
                    if not should_export_inherited_api(unit, suffix):
                        continue
                    path = route_for(prefix, suffix)
                    if skip_deep_scan:
                        req, req_objects, resp, params, headers, resp_objects = empty_field_extraction()
                    else:
                        req, req_objects, resp, params, headers, resp_objects = cached_extract_fields(ann, info, java_by_fqcn, simple_java, unit, field_metadata)
                    merge_annotation_fields(req, parse_api_attributes(ann["args"], "input"))
                    merge_annotation_fields(resp, parse_api_attributes(ann["args"], "output"))
                    full = parse_ann_bool(ann["args"], "isFullPowers", False)
                    token_annotation = parse_ann_bool(ann["args"], "isTokenRequired", True)
                    token_from_code = token_required_from_code(ann)
                    records.setdefault(path, {
                        "path": path,
                        "fqcn": fqcn,
                        "ann": compact_annotation(ann),
                        "unit": unit,
                        "module_name": module_name,
                        "entity_api": entity_api,
                        "inherited": True,
                        "inherited_from": inherited_api["source_class"],
                        "source": f"{inherited_api['source_info']['rel']}:{ann['line']}",
                        "suffix": suffix,
                        "req": req,
                        "req_objects": req_objects,
                        "resp": resp,
                        "resp_objects": resp_objects,
                        "params": params,
                        "headers": headers,
                        "token": False if full else (token_annotation or token_from_code),
                        "token_annotation": token_annotation,
                        "token_from_code": False if full else token_from_code,
                        "always": parse_ann_bool(ann["args"], "isAlwaysEnabled", False),
                        "full": full,
                        "request_format": inferred_request_format(ann["args"], req),
                        "response_format": parse_ann_enum_value(ann["args"], "responseFormat") or "default",
                    })
    clear_runtime_caches()
    return modules, records, module_sql_metadata


def yes_no(value):
    if value == "":
        return ""
    return "true" if value else "false"


def code(value):
    if value is None or value == "":
        return ""
    return f"`{value}`"


def display_type(value):
    value = str(value or "")
    while True:
        rendered = re.sub(r"array<([^<>]+)>", lambda m: f"{m.group(1)}[]", value)
        if rendered == value:
            return rendered
        value = rendered


def markdown_cell(value):
    return display_type(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def referenced_type_name(field_type, object_titles):
    displayed = display_type(field_type)
    if displayed.endswith("[]"):
        displayed = displayed[:-2]
    return displayed if displayed in object_titles else ""


def append_reference_descriptions(fields, object_titles):
    if not fields or not object_titles:
        return fields
    updated = {}
    for name, field in fields.items():
        copied = dict(field)
        ref_type = referenced_type_name(copied.get("type", ""), object_titles)
        if ref_type:
            suffix = f"請參考下文的 {ref_type} 欄位表。"
            description = copied.get("description", "")
            if suffix not in description:
                copied["description"] = (description.rstrip("。") + "；" if description else "") + suffix
        updated[name] = copied
    return updated


def field_row(name, field, include_default=True):
    cells = [
        code(name),
        markdown_cell(field.get("type", "unknown")),
        yes_no(field.get("required", "")),
    ]
    if include_default:
        cells.append(code(field.get("default", "")))
    cells += [
        field.get("source", ""),
        field.get("description", ""),
    ]
    return "| " + " | ".join(cells) + " |"


def add_field_table(lines, fields, include_default=True):
    if include_default:
        lines += [
            "| 欄位 | 類型 | 是否必填 | 預設值 | 來源 | 說明 |",
            "|---|---|---|---|---|---|",
        ]
    else:
        lines += [
            "| 欄位 | 類型 | 是否必填 | 來源 | 說明 |",
            "|---|---|---|---|---|",
        ]
    for name, field in sorted(fields.items()):
        lines.append(field_row(name, field, include_default))


def add_object_tables(lines, objects, include_default=False, rendered_titles=None):
    rendered_titles = rendered_titles if rendered_titles is not None else set()
    for name, detail in sorted((objects or {}).items()):
        if "fields" in detail:
            title = detail.get("title") or pascal_name(name)
            fields = detail["fields"]
        else:
            title = pascal_name(name)
            fields = detail
        if not fields:
            continue
        if title in rendered_titles:
            continue
        rendered_titles.add(title)
        lines += ["", f"### {title}", ""]
        add_field_table(lines, fields, include_default=include_default)


def object_detail_titles(*object_maps):
    titles = set()
    for objects in object_maps:
        for name, detail in (objects or {}).items():
            fields = detail.get("fields") if isinstance(detail, dict) and "fields" in detail else detail
            if fields:
                titles.add((detail.get("title") if isinstance(detail, dict) else "") or pascal_name(name))
    return titles


def url_composition_lines():
    return [
        "完整 URL = `{服務根位址}/{API 路徑}`。",
        "",
        "- `{服務根位址}` 需包含協定、網域或 IP、連接埠，以及部署 Context Path（如有），例如 `http://localhost:6080/quicksilver`。",
        "- `{API 路徑}` 即下方各 API 區塊標題中 HTTP 方法後面的路徑，例如 `POST openapi/qs/user/token/apply` 中的 `openapi/qs/user/token/apply`。",
        "- 以上述範例拼接，完整 URL 為 `http://localhost:6080/quicksilver/openapi/qs/user/token/apply`。",
    ]


def render_report(root, modules, records, module_sql_metadata=None):
    module_sql_metadata = module_sql_metadata or {}
    project_name = derive_project_name(root, modules)
    init_versions = []
    for module in modules:
        metadata = module_sql_metadata.get(module.name, {})
        if metadata.get("init_version"):
            init_versions.append(f"`{module.name}`={metadata['init_version']}")
    lines = [
        "# 報告摘要",
        "",
        f"- 專案根目錄：`{project_name}`",
        f"- 掃描模組：{', '.join('`' + m.name + '`' for m in modules)}",
        f"- SQL 初始化基線：{', '.join(init_versions) if init_versions else '未在 `init.xml` 中確認'}",
        f"- API 總數：{len(records)}",
        "- 格式：`路徑優先精簡 API 參考`",
        "",
        "# 完整 URL 拼接",
        "",
    ]
    lines.extend(url_composition_lines())
    lines.append("")

    groups = [(title, paths) for title, paths in grouped_record_paths(records) if paths]
    for group_index, (title, paths) in enumerate(groups):
        lines += [f"# {title}", ""]
        for path in paths:
            lines.extend(render_record_block(path, records[path]))
        if group_index < len(groups) - 1:
            lines.append("")
    return "\n".join(lines)


def render_report_header(root, modules, api_count, module_sql_metadata=None):
    module_sql_metadata = module_sql_metadata or {}
    project_name = derive_project_name(root, modules)
    init_versions = []
    for module in modules:
        metadata = module_sql_metadata.get(module.name, {})
        if metadata.get("init_version"):
            init_versions.append(f"`{module.name}`={metadata['init_version']}")
    return [
        "# 報告摘要",
        "",
        f"- 專案根目錄：`{project_name}`",
        f"- 掃描模組：{', '.join('`' + m.name + '`' for m in modules)}",
        f"- SQL 初始化基線：{', '.join(init_versions) if init_versions else '未在 `init.xml` 中確認'}",
        f"- API 總數：{api_count}",
        "- 格式：`路徑優先精簡 API 參考`",
        "",
        "# 完整 URL 拼接",
        "",
    ] + url_composition_lines() + [""]


def is_token_api(path, record):
    unit = record.get("unit", {})
    parts = [
        path.lower(),
        str(unit.get("FCode") or "").lower(),
        str(unit.get("FName") or "").lower(),
        str(record.get("fqcn") or "").lower(),
        str(record.get("ann", {}).get("method") or "").lower(),
    ]
    return any(
        part == "token"
        or part.endswith(".token")
        or "/token/" in part
        or part.endswith("/token")
        or "tokenapiimpl" in part
        for part in parts
    )


def grouped_record_paths(records):
    paths = sorted(list(records))
    token_paths = [path for path in paths if is_token_api(path, records[path])]
    token_path_set = set(token_paths)
    general_paths = [path for path in paths if path not in token_path_set]
    return [("Token API", token_paths), ("一般 API", general_paths)]


def indented_paragraph_lines(text, indent="　　"):
    return [indent + line for line in str(text or "").splitlines()]


def render_record_block(path, record):
    r = record
    unit = r["unit"]
    available = str(unit.get("FApiEnabled")) == "1" or r["always"]
    status = analysis_status(r, available)
    resp_type = response_type(r)
    handler = f"`{r['ann']['method']}`"
    inherited_from = r.get("inherited_from", "EntityApiImpl")
    if r["inherited"]:
        handler += f"（繼承自 `{inherited_from}`）"
    http_method = r.get("http_method") or inferred_http_method(r)
    usage_description = api_usage_description(r)
    lines = [
        "---",
        "",
        f"## `{http_method} {path}`",
        "",
    ]
    if usage_description:
        lines.extend(indented_paragraph_lines(usage_description) + [""])
    lines.extend([
        "**基本資訊**",
        "",
        "| 項目 | 內容 |",
        "|---|---|",
    ])
    basic_info_rows = [
        ("項目名稱", f"`{r.get('module_name')}`" if r.get("module_name") else "未確認"),
        ("是否可用", f"{'true' if available else 'false'}" + ("（`@Api.isAlwaysEnabled=true`）" if r["always"] else "")),
        ("分析狀態", status),
        ("單元 ID", f"`{unit.get('FId')}`" if unit.get("FId") else "未確認"),
        ("單元編碼", f"`{unit.get('FCode', '推斷')}`"),
        ("單元名稱", unit.get("FName") or "未在 SQL 中確認"),
        ("API 提供類", f"`{r['fqcn']}`"),
        ("入口類型", f"繼承 `{inherited_from}`" if r["inherited"] else "具體 `@Api` handler"),
        ("HTTP 方法", f"`{http_method}`"),
        ("是否需要 Token", token_requirement_text(r)),
        ("起始版本", f"`{r['ann']['since']}`" if r["ann"].get("since") else ""),
        ("返回值類型", f"`{r['ann']['return']}`"),
        ("響應類型", resp_type),
        ("處理器", handler),
    ]
    lines.extend(row for row in (basic_info_row(label, value) for label, value in basic_info_rows) if row)
    if r["request_format"] not in ("default", "json"):
        row = basic_info_row("請求格式", f"`{r['request_format']}`")
        if row:
            lines.append(row)
        row = basic_info_row("FormData 傳參", formdata_note(r))
        if row:
            lines.append(row)
    if r["response_format"] not in ("default", "json"):
        row = basic_info_row("回應格式", f"`{r['response_format']}`")
        if row:
            lines.append(row)
    if r["always"]:
        row = basic_info_row("`@Api.isAlwaysEnabled`", "true")
        if row:
            lines.append(row)
    if r["full"]:
        row = basic_info_row("`@Api.isFullPowers`", "true；處理器可能直接操作 servlet request/response。")
        if row:
            lines.append(row)

    if "{path}" in path:
        lines += [
            "",
            "**路徑參數**",
            "",
            "| 欄位 | 類型 | 是否必填 | 預設值 | 來源 | 說明 |",
            "|---|---|---|---|---|---|",
            "| `path` | string | true |  | wildcard `*` | 由 wildcard `*` 推斷；請依處理器中 `ApiContext.getPath()` 的實際用法傳入。 |",
        ]
    if r["params"]:
        lines += ["", "**請求參數**", ""]
        add_field_table(lines, r["params"], include_default=True)

    headers = dict(r["headers"])
    if r["token"]:
        headers.setdefault("Authorization", {
            "type": "string",
            "required": True,
            "default": "Bearer {tokenId}",
            "source": "Token 需求",
            "description": "Bearer Token 驗證標頭；也可用請求參數 tokenId={tokenId} 傳入。",
        })
    if headers:
        lines += ["", "**請求標頭**", ""]
        add_field_table(lines, headers, include_default=True)

    object_titles = object_detail_titles(r.get("req_objects"), r.get("resp_objects"))
    req_fields = append_reference_descriptions(r["req"], object_titles)
    resp_fields = append_reference_descriptions(r["resp"], object_titles)

    if req_fields:
        lines += ["", "**請求內容**", ""]
        add_field_table(lines, req_fields, include_default=True)

    if resp_fields:
        lines += ["", "**回應內容**", ""]
        add_field_table(lines, resp_fields, include_default=False)

    rendered_object_titles = set()
    add_object_tables(lines, r.get("req_objects"), include_default=False, rendered_titles=rendered_object_titles)
    add_object_tables(lines, r.get("resp_objects"), include_default=False, rendered_titles=rendered_object_titles)
    lines.append("")
    return lines


def write_report(root, modules, records, module_sql_metadata, output):
    with Path(output).open("w", encoding="utf-8") as out:
        out.write("\n".join(render_report_header(root, modules, len(records), module_sql_metadata)))
        out.write("\n")
        groups = [(title, paths) for title, paths in grouped_record_paths(records) if paths]
        for group_index, (title, paths) in enumerate(groups):
            out.write(f"# {title}\n\n")
            for index, path in enumerate(paths):
                record = records.pop(path)
                out.write("\n".join(render_record_block(path, record)))
                if index < len(paths) - 1:
                    out.write("\n")
                record.clear()
            if group_index < len(groups) - 1:
                out.write("\n")
    clear_runtime_caches()


def main():
    parser = argparse.ArgumentParser(description="Export a fast QS API Markdown reference.")
    parser.add_argument("project_root", help="QS parent project root")
    parser.add_argument("output", nargs="?", help="Output markdown path")
    args = parser.parse_args()

    root = resolve_project_root(args.project_root)
    modules, records, module_sql_metadata = build_records(root)
    if not modules:
        raise SystemExit(f"No QS module projects found under {root}")

    project_name = derive_project_name(root, modules)
    output = Path(args.output).resolve() if args.output else root / "docs" / f"{project_name}-api-discovery.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_report(root, modules, records, module_sql_metadata, output)
    print(output)


if __name__ == "__main__":
    main()
