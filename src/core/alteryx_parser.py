# -*- coding: utf-8 -*-
"""
Alteryx Parser Module
Parsing de arquivos de workflow Alteryx (.yxmd) em formato XML.
Extrai metadados de nodes, connections e tool configurations.
"""
import logging
import re
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class AlteryxWorkflow:
    """Representacao estruturada de um workflow Alteryx."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.root: Optional[ET.Element] = None
        self.nodes: list[dict] = []
        self.connections: list[dict] = []
        self.properties: dict = {}
        self._parsed = False

    @property
    def name(self) -> str:
        return self.filepath.stem

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def connection_count(self) -> int:
        return len(self.connections)


class AlteryxParser:
    """Parser para arquivos de workflow Alteryx (.yxmd)."""

    SUPPORTED_EXTENSIONS = {".yxmd", ".yxmc", ".yxwz"}

    def __init__(self) -> None:
        self._cache: dict[str, AlteryxWorkflow] = {}

    def parse(self, filepath: Path) -> AlteryxWorkflow:
        """Faz parsing de um arquivo Alteryx XML e retorna o workflow estruturado."""
        filepath = Path(filepath)
        cache_key = str(filepath.resolve())

        if cache_key in self._cache:
            logger.info("Usando cache para: %s", filepath.name)
            return self._cache[cache_key]

        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {filepath}")

        if filepath.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Extensao nao suportada: {filepath.suffix}")

        workflow = AlteryxWorkflow(filepath)

        try:
            tree = ET.parse(str(filepath))
            workflow.root = tree.getroot()
        except ET.ParseError as exc:
            logger.error("Falha ao parsear XML: %s - %s", filepath.name, exc)
            raise

        workflow.properties = self._extract_properties(workflow.root)
        workflow.nodes = self._extract_nodes(workflow.root)
        workflow.connections = self._extract_connections(workflow.root)
        workflow._parsed = True

        self._cache[cache_key] = workflow
        logger.info(
            "Parsed: %s (%d nodes, %d connections)",
            filepath.name,
            workflow.node_count,
            workflow.connection_count,
        )
        return workflow

    def _extract_properties(self, root: ET.Element) -> dict:
        """Extrai propriedades globais do workflow."""
        props: dict = {}
        properties_elem = root.find(".//Properties")
        if properties_elem is not None:
            for child in properties_elem:
                if child.text:
                    props[child.tag] = child.text.strip()

        meta_info = root.find(".//MetaInfo")
        if meta_info is not None:
            for child in meta_info:
                if child.text:
                    props[f"meta_{child.tag}"] = child.text.strip()

        return props

    def _extract_nodes(self, root: ET.Element) -> list[dict]:
        """Extrai todos os nodes do workflow com seus atributos."""
        nodes: list[dict] = []
        for node in root.iter("Node"):
            node_data = {
                "tool_id": node.get("ToolID", ""),
                "gui_settings": {},
                "properties": {},
                "annotation": "",
            }

            gui_settings = node.find("GuiSettings")
            if gui_settings is not None:
                node_data["gui_settings"] = dict(gui_settings.attrib)

            for prop in node.iter("Configuration"):
                for child in prop:
                    if child.text:
                        node_data["properties"][child.tag] = child.text.strip()

            annotation = node.find(".//Annotation/DefaultAnnotationText")
            if annotation is not None and annotation.text:
                node_data["annotation"] = annotation.text.strip()

            nodes.append(node_data)

        return nodes

    def _extract_connections(self, root: ET.Element) -> list[dict]:
        """Extrai todas as conexoes entre nodes."""
        connections: list[dict] = []
        for conn in root.iter("Connection"):
            origin = conn.find("Origin")
            destination = conn.find("Destination")

            if origin is not None and destination is not None:
                connections.append({
                    "origin_tool_id": origin.get("ToolID", ""),
                    "origin_connection": origin.get("Connection", ""),
                    "dest_tool_id": destination.get("ToolID", ""),
                    "dest_connection": destination.get("Connection", ""),
                })

        return connections

    def find_node_by_tool_id(self, workflow: AlteryxWorkflow, tool_id: str) -> Optional[ET.Element]:
        """Encontra um Node element pelo ToolID."""
        if workflow.root is None:
            return None
        for node in workflow.root.iter("Node"):
            if node.get("ToolID") == tool_id:
                return node
        return None

    def find_nodes_by_type(self, workflow: AlteryxWorkflow, plugin_name: str) -> list[ET.Element]:
        """Encontra todos os nodes de um tipo especifico de plugin."""
        results: list[ET.Element] = []
        if workflow.root is None:
            return results
        for node in workflow.root.iter("Node"):
            gui = node.find("GuiSettings")
            if gui is not None and gui.get("Plugin") == plugin_name:
                results.append(node)
        return results

    def clear_cache(self) -> None:
        """Limpa o cache de workflows parseados."""
        self._cache.clear()
        logger.info("Cache de parser limpo")

    def parse_from_string(self, xml_content: str, name: str = "memory") -> AlteryxWorkflow:
        """Faz parsing de conteudo XML a partir de uma string."""
        workflow = AlteryxWorkflow(Path(name))

        try:
            workflow.root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            logger.error("Falha ao parsear XML string: %s", exc)
            raise

        workflow.properties = self._extract_properties(workflow.root)
        workflow.nodes = self._extract_nodes(workflow.root)
        workflow.connections = self._extract_connections(workflow.root)
        workflow._parsed = True

        return workflow


# "A excelencia nao e um ato, mas um habito." - Aristoteles

