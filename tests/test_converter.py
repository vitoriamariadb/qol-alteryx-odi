"""
Testes para o modulo Converter.
Verifica conversao bidirecional entre Alteryx e ODI, mapeamento de tools/steps
e integridade do XML gerado.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from src.core.converter import (
    AlteryxToOdiConverter,
    ConversionResult,
    OdiToAlteryxConverter,
    TOOL_TO_STEP_MAP,
    STEP_TO_TOOL_MAP,
)


SAMPLE_ALTERYX_XML = """<?xml version="1.0"?>
<AlteryxDocument yxmdVer="2024.1">
  <Properties>
    <MetaInfo>
      <Name>ConvertTest</Name>
    </MetaInfo>
  </Properties>
  <Nodes>
    <Node ToolID="1">
      <GuiSettings Plugin="AlteryxBasePluginsGui.DbFileInput.DbFileInput">
        <Position x="100" y="200"/>
      </GuiSettings>
      <Configuration>
        <File>input.csv</File>
      </Configuration>
      <Annotation>
        <DefaultAnnotationText>Input</DefaultAnnotationText>
      </Annotation>
    </Node>
    <Node ToolID="2">
      <GuiSettings Plugin="AlteryxBasePluginsGui.Filter.Filter">
        <Position x="300" y="200"/>
      </GuiSettings>
      <Configuration>
        <Expression>[Field] &gt; 0</Expression>
      </Configuration>
      <Annotation>
        <DefaultAnnotationText>Filtro</DefaultAnnotationText>
      </Annotation>
    </Node>
    <Node ToolID="3">
      <GuiSettings Plugin="AlteryxBasePluginsGui.DbFileOutput.DbFileOutput">
        <Position x="500" y="200"/>
      </GuiSettings>
      <Configuration>
        <File>output.csv</File>
      </Configuration>
    </Node>
  </Nodes>
  <Connections>
    <Connection>
      <Origin ToolID="1" Connection="Output"/>
      <Destination ToolID="2" Connection="Input"/>
    </Connection>
    <Connection>
      <Origin ToolID="2" Connection="True"/>
      <Destination ToolID="3" Connection="Input"/>
    </Connection>
  </Connections>
</AlteryxDocument>"""

SAMPLE_ODI_XML = """<?xml version="1.0"?>
<OdiPackage Name="PKG_TEST" Version="1.0">
  <Description>Package de teste para conversao</Description>
  <Steps>
    <Step Name="Extrair" Type="DataStoreCommand">
      <Command>SELECT * FROM tabela</Command>
      <OnSuccess NextStep="Transformar"/>
    </Step>
    <Step Name="Transformar" Type="ProcedureCommand">
      <Command>CALL proc()</Command>
      <OnSuccess NextStep="Carregar"/>
    </Step>
    <Step Name="Carregar" Type="DataStoreCommand">
      <Command>INSERT INTO destino SELECT * FROM origem</Command>
    </Step>
  </Steps>
  <Scenarios>
    <Scenario Name="SCN_TEST" Version="001"/>
  </Scenarios>
</OdiPackage>"""


@pytest.fixture
def alteryx_file(tmp_path: Path) -> Path:
    """Cria arquivo Alteryx temporario."""
    filepath = tmp_path / "workflow.yxmd"
    filepath.write_text(SAMPLE_ALTERYX_XML, encoding="utf-8")
    return filepath


@pytest.fixture
def odi_file(tmp_path: Path) -> Path:
    """Cria arquivo ODI temporario."""
    filepath = tmp_path / "package.xml"
    filepath.write_text(SAMPLE_ODI_XML, encoding="utf-8")
    return filepath


class TestAlteryxToOdiConverter:
    """Testes de conversao Alteryx -> ODI."""

    def test_convert_success(self, alteryx_file: Path) -> None:
        """Verifica conversao bem-sucedida."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(alteryx_file)
        assert result.success is True
        assert result.xml_content

    def test_convert_generates_valid_xml(self, alteryx_file: Path) -> None:
        """Verifica que XML gerado e valido."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(alteryx_file)
        root = ET.fromstring(result.xml_content)
        assert root.tag == "OdiPackage"

    def test_convert_preserves_name(self, alteryx_file: Path) -> None:
        """Verifica que nome do workflow e preservado."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(alteryx_file)
        root = ET.fromstring(result.xml_content)
        assert root.get("Name") == "workflow"

    def test_convert_maps_tools_to_steps(self, alteryx_file: Path) -> None:
        """Verifica mapeamento de tools para steps."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(alteryx_file)
        root = ET.fromstring(result.xml_content)
        steps = list(root.iter("Step"))
        assert len(steps) == 3

    def test_convert_stats(self, alteryx_file: Path) -> None:
        """Verifica estatisticas de conversao."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(alteryx_file)
        assert result.stats["tools_converted"] == 3
        assert result.stats["connections"] == 2

    def test_convert_with_output_file(self, alteryx_file: Path, tmp_path: Path) -> None:
        """Verifica gravacao em arquivo de saida."""
        converter = AlteryxToOdiConverter()
        output_path = tmp_path / "output_odi.xml"
        result = converter.convert(alteryx_file, output_path)
        assert result.output_path == output_path
        assert output_path.exists()

    def test_convert_file_not_found(self) -> None:
        """Verifica erro com arquivo inexistente."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(Path("/nao/existe.yxmd"))
        assert result.success is False
        assert len(result.errors) > 0

    def test_convert_includes_connections(self, alteryx_file: Path) -> None:
        """Verifica que conexoes sao mapeadas."""
        converter = AlteryxToOdiConverter()
        result = converter.convert(alteryx_file)
        root = ET.fromstring(result.xml_content)
        flows = list(root.iter("Flow"))
        assert len(flows) == 2


class TestOdiToAlteryxConverter:
    """Testes de conversao ODI -> Alteryx."""

    def test_convert_success(self, odi_file: Path) -> None:
        """Verifica conversao bem-sucedida."""
        converter = OdiToAlteryxConverter()
        result = converter.convert(odi_file)
        assert result.success is True
        assert result.xml_content

    def test_convert_generates_valid_xml(self, odi_file: Path) -> None:
        """Verifica que XML Alteryx gerado e valido."""
        converter = OdiToAlteryxConverter()
        result = converter.convert(odi_file)
        root = ET.fromstring(result.xml_content)
        assert root.tag == "AlteryxDocument"

    def test_convert_maps_steps_to_nodes(self, odi_file: Path) -> None:
        """Verifica mapeamento de steps para nodes."""
        converter = OdiToAlteryxConverter()
        result = converter.convert(odi_file)
        root = ET.fromstring(result.xml_content)
        nodes = list(root.iter("Node"))
        assert len(nodes) == 3

    def test_convert_assigns_sequential_tool_ids(self, odi_file: Path) -> None:
        """Verifica atribuicao sequencial de ToolIDs."""
        converter = OdiToAlteryxConverter()
        result = converter.convert(odi_file)
        root = ET.fromstring(result.xml_content)
        tool_ids = [n.get("ToolID") for n in root.iter("Node")]
        assert tool_ids == ["1", "2", "3"]

    def test_convert_with_output_file(self, odi_file: Path, tmp_path: Path) -> None:
        """Verifica gravacao em arquivo de saida."""
        converter = OdiToAlteryxConverter()
        output_path = tmp_path / "output_alteryx.yxmd"
        result = converter.convert(odi_file, output_path)
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8-sig")
        assert "AlteryxDocument" in content

    def test_convert_stats(self, odi_file: Path) -> None:
        """Verifica estatisticas de conversao."""
        converter = OdiToAlteryxConverter()
        result = converter.convert(odi_file)
        assert result.stats["steps_converted"] == 3

    def test_convert_file_not_found(self) -> None:
        """Verifica erro com arquivo inexistente."""
        converter = OdiToAlteryxConverter()
        result = converter.convert(Path("/nao/existe.xml"))
        assert result.success is False


class TestToolStepMapping:
    """Testes dos mapeamentos tool <-> step."""

    def test_tool_to_step_map_not_empty(self) -> None:
        """Verifica que o mapa tool->step nao esta vazio."""
        assert len(TOOL_TO_STEP_MAP) > 0

    def test_step_to_tool_map_not_empty(self) -> None:
        """Verifica que o mapa step->tool nao esta vazio."""
        assert len(STEP_TO_TOOL_MAP) > 0

    def test_input_tool_maps_to_datastore(self) -> None:
        """Verifica mapeamento de input tool."""
        key = "AlteryxBasePluginsGui.DbFileInput.DbFileInput"
        assert TOOL_TO_STEP_MAP[key] == "DataStoreCommand"

    def test_datastore_maps_to_input(self) -> None:
        """Verifica mapeamento reverso de datastore."""
        assert "DataStoreCommand" in STEP_TO_TOOL_MAP

# "O valor de um teste e inversamente proporcional ao numero de bugs que ele deixa passar." - Boris Beizer
