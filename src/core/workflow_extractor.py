"""
Workflow Extractor Module
Extrai metadados estruturados de workflows Alteryx para analise e documentacao.
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from src.core.alteryx_parser import AlteryxParser, AlteryxWorkflow

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Informacoes de um tool individual no workflow."""
    tool_id: str
    plugin_name: str
    annotation: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
    config: dict = field(default_factory=dict)


@dataclass
class ConnectionInfo:
    """Informacoes de uma conexao entre tools."""
    origin_id: str
    destination_id: str
    origin_name: str = ""
    destination_name: str = ""
    wireless: bool = False


@dataclass
class WorkflowMetadata:
    """Metadados completos extraidos de um workflow."""
    name: str
    filepath: Path
    version: str = ""
    description: str = ""
    author: str = ""
    tools: list[ToolInfo] = field(default_factory=list)
    connections: list[ConnectionInfo] = field(default_factory=list)
    input_tools: list[ToolInfo] = field(default_factory=list)
    output_tools: list[ToolInfo] = field(default_factory=list)
    macro_tools: list[ToolInfo] = field(default_factory=list)
    constants: dict = field(default_factory=dict)

    @property
    def tool_count(self) -> int:
        return len(self.tools)

    @property
    def connection_count(self) -> int:
        return len(self.connections)


INPUT_PLUGINS = {
    "AlteryxBasePluginsGui.DbFileInput.DbFileInput",
    "AlteryxBasePluginsGui.TextInput.TextInput",
    "AlteryxBasePluginsGui.BrowseV2.BrowseV2",
}

OUTPUT_PLUGINS = {
    "AlteryxBasePluginsGui.DbFileOutput.DbFileOutput",
    "AlteryxBasePluginsGui.Output.Output",
}

MACRO_PLUGINS = {
    "AlteryxGuiToolkit.ToolContainer.ToolContainer",
    "AlteryxBasePluginsGui.MacroInput.MacroInput",
    "AlteryxBasePluginsGui.MacroOutput.MacroOutput",
}


class WorkflowExtractor:
    """Extrator de metadados de workflows Alteryx."""

    def __init__(self) -> None:
        self._parser = AlteryxParser()

    def extract(self, filepath: Path) -> WorkflowMetadata:
        """Extrai metadados completos de um workflow Alteryx."""
        workflow = self._parser.parse(filepath)
        metadata = WorkflowMetadata(
            name=workflow.name,
            filepath=filepath,
        )

        if workflow.root is None:
            logger.warning("Root element vazio para: %s", filepath.name)
            return metadata

        metadata.version = self._extract_version(workflow.root)
        metadata.description = self._extract_description(workflow.root)
        metadata.author = self._extract_author(workflow.root)
        metadata.constants = self._extract_constants(workflow.root)
        metadata.tools = self._extract_tools(workflow.root)
        metadata.connections = self._extract_connections(workflow.root)

        metadata.input_tools = [
            t for t in metadata.tools if t.plugin_name in INPUT_PLUGINS
        ]
        metadata.output_tools = [
            t for t in metadata.tools if t.plugin_name in OUTPUT_PLUGINS
        ]
        metadata.macro_tools = [
            t for t in metadata.tools if t.plugin_name in MACRO_PLUGINS
        ]

        logger.info(
            "Extraido: %s - %d tools, %d inputs, %d outputs",
            metadata.name,
            metadata.tool_count,
            len(metadata.input_tools),
            len(metadata.output_tools),
        )
        return metadata

    def _extract_version(self, root: ET.Element) -> str:
        """Extrai a versao do Alteryx usada."""
        version_elem = root.find(".//Properties/EngineSettings")
        if version_elem is not None:
            return version_elem.get("Macro", "")
        return root.get("yxmdVer", "")

    def _extract_description(self, root: ET.Element) -> str:
        """Extrai a descricao do workflow."""
        desc = root.find(".//Properties/MetaInfo/Description")
        if desc is not None and desc.text:
            return desc.text.strip()
        return ""

    def _extract_author(self, root: ET.Element) -> str:
        """Extrai o autor do workflow."""
        author = root.find(".//Properties/MetaInfo/Author")
        if author is not None and author.text:
            return author.text.strip()
        return ""

    def _extract_constants(self, root: ET.Element) -> dict:
        """Extrai constantes definidas no workflow."""
        constants: dict = {}
        for const in root.iter("Constant"):
            name = const.get("Name", "")
            value = const.get("Value", "")
            if name:
                constants[name] = value
        return constants

    def _extract_tools(self, root: ET.Element) -> list[ToolInfo]:
        """Extrai informacoes detalhadas de cada tool."""
        tools: list[ToolInfo] = []

        for node in root.iter("Node"):
            tool_id = node.get("ToolID", "")
            gui = node.find("GuiSettings")
            plugin_name = gui.get("Plugin", "") if gui is not None else ""

            position = gui.find("Position") if gui is not None else None
            pos_x = float(position.get("x", "0")) if position is not None else 0.0
            pos_y = float(position.get("y", "0")) if position is not None else 0.0

            annotation_elem = node.find(".//Annotation/DefaultAnnotationText")
            annotation = ""
            if annotation_elem is not None and annotation_elem.text:
                annotation = annotation_elem.text.strip()

            config: dict = {}
            config_elem = node.find("Configuration")
            if config_elem is not None:
                for child in config_elem:
                    if child.text:
                        config[child.tag] = child.text.strip()

            tools.append(ToolInfo(
                tool_id=tool_id,
                plugin_name=plugin_name,
                annotation=annotation,
                position_x=pos_x,
                position_y=pos_y,
                config=config,
            ))

        return tools

    def _extract_connections(self, root: ET.Element) -> list[ConnectionInfo]:
        """Extrai informacoes de conexoes entre tools."""
        connections: list[ConnectionInfo] = []

        for conn in root.iter("Connection"):
            origin = conn.find("Origin")
            dest = conn.find("Destination")

            if origin is not None and dest is not None:
                connections.append(ConnectionInfo(
                    origin_id=origin.get("ToolID", ""),
                    destination_id=dest.get("ToolID", ""),
                    origin_name=origin.get("Connection", ""),
                    destination_name=dest.get("Connection", ""),
                    wireless=conn.get("Wireless", "False").lower() == "true",
                ))

        return connections

    def extract_summary(self, filepath: Path) -> dict:
        """Extrai um resumo simplificado do workflow."""
        metadata = self.extract(filepath)
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "total_tools": metadata.tool_count,
            "total_connections": metadata.connection_count,
            "input_count": len(metadata.input_tools),
            "output_count": len(metadata.output_tools),
            "macro_count": len(metadata.macro_tools),
            "constants": metadata.constants,
        }


# "Conhece-te a ti mesmo." - Socrates
