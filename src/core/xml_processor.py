"""
XML Processor Module
Processamento cirurgico de arquivos Alteryx workflow (.yxmd).
Usa XML parsing para modificar APENAS Tool IDs especificos, preservando demais dados.
"""
import logging
import re
from pathlib import Path
from typing import Callable, Optional, Tuple
from xml.etree import ElementTree as ET

from src.core.parser import RegexCache

logger = logging.getLogger(__name__)

_regex_cache = RegexCache()


RULES: dict[str, dict] = {
    "gerar-fechamento-diario.yxmd": {
        "name": "gerar-fechamento-diario",
        "date_nodes": {
            "tool_ids": ["16", "17"],
        },
        "server_nodes": [],
    },
    "tratar-mailing.yxmd": {
        "name": "tratar-mailing",
        "date_nodes": {
            "tool_ids": ["132", "38"],
        },
        "server_nodes": [],
    },
    "base-funil.yxmd": {
        "name": "base-funil",
        "date_nodes": {
            "tool_ids": ["2877", "2878", "1695", "1698", "1843"],
        },
        "server_nodes": ["2916", "2914", "2978"],
    },
}


FILE_MAPPING: dict[str, str] = {
    "gerar-fechamento-diario.yxmd": "GERAR FECHAMENTO REPROC",
    "tratar-mailing.yxmd": "Tratar Mailing_Enriquecimento_v2",
    "base-funil.yxmd": "Base Funil_v9.2",
}


def find_node_by_tool_id(root: ET.Element, tool_id: str) -> Optional[ET.Element]:
    """Encontra um Node element pelo atributo ToolID."""
    for node in root.iter("Node"):
        if node.get("ToolID") == tool_id:
            return node
    return None


def find_nodes_by_annotation_text(root: ET.Element, annotation_text: str) -> list[ET.Element]:
    """Encontra todos os nodes que contem texto de anotacao especificado."""
    matching: list[ET.Element] = []
    for node in root.iter("Node"):
        for text_elem in node.iter("Text"):
            if text_elem.text and annotation_text in text_elem.text:
                matching.append(node)
                break
    return matching


def replace_dates_in_text(text: str, target_year: int, target_month: int) -> Tuple[str, int]:
    """
    Substitui padroes de data no texto pelo mes/ano alvo.
    Formatos: YYYY-MM-DD, YYYY-MM, DD/MM/YYYY, MM/YYYY, MM-YYYY
    """
    count = 0

    def _replace_yyyy_mm_dd(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f"{target_year:04d}-{target_month:02d}-01"

    text = _regex_cache.get_compiled("YYYY_MM_DD").sub(_replace_yyyy_mm_dd, text)

    def _replace_yyyy_mm(m: re.Match) -> str:
        nonlocal count
        old = m.group(0)
        if re.match(r"\d{4}-\d{2}-\d{2}", old):
            return old
        count += 1
        return f"{target_year:04d}-{target_month:02d}"

    text = _regex_cache.get_compiled("YYYY_MM").sub(_replace_yyyy_mm, text)

    def _replace_dd_mm_yyyy(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f"01/{target_month:02d}/{target_year:04d}"

    text = _regex_cache.get_compiled("DD_MM_YYYY").sub(_replace_dd_mm_yyyy, text)

    def _replace_mm_yyyy_slash(m: re.Match) -> str:
        nonlocal count
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12 and 2000 <= year <= 2099:
            count += 1
            return f"{target_month:02d}/{target_year:04d}"
        return m.group(0)

    text = _regex_cache.get_compiled("MM_YYYY_SLASH").sub(_replace_mm_yyyy_slash, text)

    def _replace_mm_yyyy_dash(m: re.Match) -> str:
        nonlocal count
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12 and 2000 <= year <= 2099:
            count += 1
            return f"{target_month:02d}-{target_year:04d}"
        return m.group(0)

    text = _regex_cache.get_compiled("MM_YYYY_DASH").sub(_replace_mm_yyyy_dash, text)

    return text, count


def update_node_dates(
    node: ET.Element,
    target_year: int,
    target_month: int,
    log_fn: Optional[Callable] = None,
) -> int:
    """Atualiza todas as referencias de data dentro de um node."""
    tool_id = node.get("ToolID", "unknown")
    total_count = 0

    for elem in node.iter():
        if elem.text and elem.text.strip():
            new_text, count = replace_dates_in_text(elem.text, target_year, target_month)
            if count > 0:
                elem.text = new_text
                total_count += count
                if log_fn:
                    log_fn(f"  ID {tool_id}: {count} data(s) em <{elem.tag}>")

        if elem.tail and elem.tail.strip():
            new_tail, count = replace_dates_in_text(elem.tail, target_year, target_month)
            if count > 0:
                elem.tail = new_tail
                total_count += count

        for attr_name, attr_value in list(elem.attrib.items()):
            new_value, count = replace_dates_in_text(attr_value, target_year, target_month)
            if count > 0:
                elem.set(attr_name, new_value)
                total_count += count
                if log_fn:
                    log_fn(f"  ID {tool_id}: {count} data(s) em @{attr_name}")

    return total_count


def update_node_server(
    node: ET.Element,
    new_server: str,
    log_fn: Optional[Callable] = None,
) -> int:
    """Atualiza string de conexao de servidor no elemento <File> de um node."""
    tool_id = node.get("ToolID", "unknown")
    total_count = 0

    for file_elem in node.iter("File"):
        if file_elem.text and "|||" in file_elem.text:
            parts = file_elem.text.split("|||", 1)
            old_connection = parts[0]
            table_name = parts[1] if len(parts) > 1 else ""

            new_text = f"{new_server}|||{table_name}"
            file_elem.text = new_text
            total_count += 1

            if log_fn:
                log_fn(f"  ID {tool_id}: Servidor '{old_connection}' -> '{new_server}'")

    return total_count


def process_template(
    template_path: Path,
    new_server: str,
    target_year: int,
    target_month: int,
    log_fn: Optional[Callable] = None,
) -> Tuple[str, dict]:
    """
    Processa um template aplicando modificacoes cirurgicas.
    Modifica apenas Tool IDs especificos conforme definido em RULES.
    """
    template_name = template_path.name
    rules = RULES.get(template_name, {})

    stats: dict = {
        "servers": 0,
        "dates": 0,
        "nodes_modified": 0,
    }

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        if log_fn:
            log_fn(f"ERRO: Falha ao parsear XML - {exc}", "error")
        return content, stats

    if log_fn:
        log_fn(f"Processando: {rules.get('name', template_name)}")

    date_rules = rules.get("date_nodes", {})

    if "tool_ids" in date_rules:
        for tool_id in date_rules["tool_ids"]:
            node = find_node_by_tool_id(root, tool_id)
            if node is not None:
                count = update_node_dates(node, target_year, target_month, log_fn)
                if count > 0:
                    stats["dates"] += count
                    stats["nodes_modified"] += 1
            else:
                if log_fn:
                    log_fn(f"  AVISO: ID {tool_id} nao encontrado", "warning")

    server_ids = rules.get("server_nodes", [])
    if server_ids and new_server:
        if log_fn:
            log_fn(f"  Atualizando servidor para: {new_server}")

        for tool_id in server_ids:
            node = find_node_by_tool_id(root, tool_id)
            if node is not None:
                count = update_node_server(node, new_server, log_fn)
                stats["servers"] += count
                if count > 0:
                    stats["nodes_modified"] += 1
            else:
                if log_fn:
                    log_fn(f"  AVISO: ID {tool_id} (servidor) nao encontrado", "warning")

    output = ET.tostring(root, encoding="unicode")

    if content.startswith("<?xml"):
        xml_decl_match = re.match(r"<\?xml[^?]*\?>\s*", content)
        if xml_decl_match:
            output = xml_decl_match.group(0) + output

    return output, stats


def get_output_filename(input_filename: str) -> str:
    """Retorna o nome do arquivo de saida baseado no template de entrada."""
    return FILE_MAPPING.get(input_filename, input_filename.replace(".yxmd", ""))


# "A natureza nao faz nada em vao." - Aristoteles
