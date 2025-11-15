"""
Converter Module
Conversao entre formatos Alteryx (.yxmd) e ODI XML.
Mapeia estruturas de workflow para package e vice-versa.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from src.core.alteryx_parser import AlteryxParser, AlteryxWorkflow
from src.core.odi_parser import OdiParser, OdiPackage
from src.core.parser import RegexCache

logger = logging.getLogger(__name__)


TOOL_TO_STEP_MAP = {
    "AlteryxBasePluginsGui.DbFileInput.DbFileInput": "DataStoreCommand",
    "AlteryxBasePluginsGui.DbFileOutput.DbFileOutput": "DataStoreCommand",
    "AlteryxBasePluginsGui.Filter.Filter": "ProcedureCommand",
    "AlteryxBasePluginsGui.Formula.Formula": "ProcedureCommand",
    "AlteryxBasePluginsGui.Join.Join": "ProcedureCommand",
    "AlteryxBasePluginsGui.Sort.Sort": "ProcedureCommand",
    "AlteryxBasePluginsGui.Summarize.Summarize": "ProcedureCommand",
    "AlteryxBasePluginsGui.Union.Union": "ProcedureCommand",
}

STEP_TO_TOOL_MAP = {
    "DataStoreCommand": "AlteryxBasePluginsGui.DbFileInput.DbFileInput",
    "ProcedureCommand": "AlteryxBasePluginsGui.Formula.Formula",
    "OdiCommand": "AlteryxBasePluginsGui.RunCommand.RunCommand",
    "VariableStep": "AlteryxBasePluginsGui.Formula.Formula",
}

_KNOWN_TOOL_PLUGINS = frozenset(TOOL_TO_STEP_MAP.keys())
_KNOWN_STEP_TYPES = frozenset(STEP_TO_TOOL_MAP.keys())


@dataclass
class ConversionResult:
    """Resultado de uma conversao entre formatos."""
    success: bool
    output_path: Optional[Path] = None
    xml_content: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class AlteryxToOdiConverter:
    """Converte workflows Alteryx para formato ODI XML."""

    def __init__(self) -> None:
        self._parser = AlteryxParser()

    def convert(self, input_path: Path, output_path: Optional[Path] = None) -> ConversionResult:
        """Converte um workflow Alteryx para ODI XML."""
        result = ConversionResult(success=False)

        try:
            workflow = self._parser.parse(input_path)
        except Exception as exc:
            result.errors.append(f"Falha ao parsear Alteryx: {exc}")
            return result

        if workflow.root is None:
            result.errors.append("Workflow sem root element")
            return result

        odi_root = ET.Element("OdiPackage")
        odi_root.set("Name", workflow.name)
        odi_root.set("Version", "1.0")

        desc = ET.SubElement(odi_root, "Description")
        desc.text = f"Convertido de workflow Alteryx: {workflow.name}"

        steps_elem = ET.SubElement(odi_root, "Steps")
        converted_count = 0
        skipped_count = 0

        for node_data in workflow.nodes:
            plugin = node_data.get("gui_settings", {}).get("Plugin", "")
            step_type = TOOL_TO_STEP_MAP.get(plugin)

            if step_type:
                step = ET.SubElement(steps_elem, "Step")
                step.set("Name", f"Step_{node_data['tool_id']}")
                step.set("Type", step_type)

                if node_data.get("annotation"):
                    ann = ET.SubElement(step, "Annotation")
                    ann.text = node_data["annotation"]

                config = ET.SubElement(step, "Configuration")
                for key, value in node_data.get("properties", {}).items():
                    prop = ET.SubElement(config, key)
                    prop.text = value

                converted_count += 1
            else:
                skipped_count += 1
                if plugin:
                    result.warnings.append(
                        f"Tool sem mapeamento ODI: {plugin} (ID: {node_data['tool_id']})"
                    )

        connections_elem = ET.SubElement(odi_root, "Connections")
        for conn in workflow.connections:
            flow = ET.SubElement(connections_elem, "Flow")
            flow.set("From", f"Step_{conn['origin_tool_id']}")
            flow.set("To", f"Step_{conn['dest_tool_id']}")

        result.xml_content = ET.tostring(odi_root, encoding="unicode", xml_declaration=True)
        result.stats = {
            "tools_converted": converted_count,
            "tools_skipped": skipped_count,
            "connections": len(workflow.connections),
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.xml_content)
            result.output_path = output_path
            logger.info("Salvo ODI XML em: %s", output_path)

        result.success = True
        logger.info(
            "Conversao Alteryx->ODI: %d convertidos, %d ignorados",
            converted_count,
            skipped_count,
        )
        return result


class OdiToAlteryxConverter:
    """Converte packages ODI para formato Alteryx XML."""

    def __init__(self) -> None:
        self._parser = OdiParser()

    def convert(self, input_path: Path, output_path: Optional[Path] = None) -> ConversionResult:
        """Converte um package ODI para workflow Alteryx XML."""
        result = ConversionResult(success=False)

        try:
            package = self._parser.parse(input_path)
        except Exception as exc:
            result.errors.append(f"Falha ao parsear ODI: {exc}")
            return result

        alteryx_root = ET.Element("AlteryxDocument")
        alteryx_root.set("yxmdVer", "2024.1")

        properties = ET.SubElement(alteryx_root, "Properties")
        meta = ET.SubElement(properties, "MetaInfo")
        name_elem = ET.SubElement(meta, "Name")
        name_elem.text = package.name
        desc_elem = ET.SubElement(meta, "Description")
        desc_elem.text = f"Convertido de package ODI: {package.name}"

        nodes = ET.SubElement(alteryx_root, "Nodes")
        converted_count = 0
        skipped_count = 0

        for idx, step in enumerate(package.steps):
            tool_plugin = STEP_TO_TOOL_MAP.get(step.step_type)

            if tool_plugin:
                node = ET.SubElement(nodes, "Node")
                node.set("ToolID", str(idx + 1))

                gui = ET.SubElement(node, "GuiSettings")
                gui.set("Plugin", tool_plugin)

                pos = ET.SubElement(gui, "Position")
                pos.set("x", str(150 + idx * 200))
                pos.set("y", str(200))

                if step.name:
                    ann = ET.SubElement(node, "Annotation")
                    text = ET.SubElement(ann, "DefaultAnnotationText")
                    text.text = step.name

                converted_count += 1
            else:
                skipped_count += 1
                result.warnings.append(
                    f"Step sem mapeamento Alteryx: {step.step_type} ({step.name})"
                )

        connections = ET.SubElement(alteryx_root, "Connections")
        for idx in range(len(package.steps) - 1):
            conn = ET.SubElement(connections, "Connection")
            origin = ET.SubElement(conn, "Origin")
            origin.set("ToolID", str(idx + 1))
            origin.set("Connection", "Output")
            dest = ET.SubElement(conn, "Destination")
            dest.set("ToolID", str(idx + 2))
            dest.set("Connection", "Input")

        result.xml_content = ET.tostring(alteryx_root, encoding="unicode", xml_declaration=True)
        result.stats = {
            "steps_converted": converted_count,
            "steps_skipped": skipped_count,
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8-sig") as f:
                f.write(result.xml_content)
            result.output_path = output_path
            logger.info("Salvo Alteryx XML em: %s", output_path)

        result.success = True
        logger.info(
            "Conversao ODI->Alteryx: %d convertidos, %d ignorados",
            converted_count,
            skipped_count,
        )
        return result


# "Medir o que e mensuravel e tornar mensuravel o que nao e." - Galileu Galilei
