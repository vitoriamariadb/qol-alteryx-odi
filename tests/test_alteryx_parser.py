"""
Testes para o modulo AlteryxParser.
Verifica parsing de XML, extracao de nodes, connections e propriedades.
"""
import tempfile
from pathlib import Path

import pytest

from src.core.alteryx_parser import AlteryxParser, AlteryxWorkflow


SAMPLE_ALTERYX_XML = """<?xml version="1.0"?>
<AlteryxDocument yxmdVer="2024.1">
  <Properties>
    <MetaInfo>
      <Name>TestWorkflow</Name>
      <Description>Workflow de teste para validacao do parser</Description>
      <Author>Tester</Author>
    </MetaInfo>
    <EngineSettings Macro="2024.1"/>
  </Properties>
  <Nodes>
    <Node ToolID="1">
      <GuiSettings Plugin="AlteryxBasePluginsGui.DbFileInput.DbFileInput">
        <Position x="100" y="200"/>
      </GuiSettings>
      <Configuration>
        <File>data/input.csv</File>
        <FormatType>CSV</FormatType>
      </Configuration>
      <Annotation>
        <DefaultAnnotationText>Input de dados</DefaultAnnotationText>
      </Annotation>
    </Node>
    <Node ToolID="2">
      <GuiSettings Plugin="AlteryxBasePluginsGui.Filter.Filter">
        <Position x="300" y="200"/>
      </GuiSettings>
      <Configuration>
        <Expression>[Campo] &gt; 0</Expression>
      </Configuration>
      <Annotation>
        <DefaultAnnotationText>Filtrar registros validos</DefaultAnnotationText>
      </Annotation>
    </Node>
    <Node ToolID="3">
      <GuiSettings Plugin="AlteryxBasePluginsGui.DbFileOutput.DbFileOutput">
        <Position x="500" y="200"/>
      </GuiSettings>
      <Configuration>
        <File>output/result.csv</File>
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


@pytest.fixture
def sample_yxmd_file(tmp_path: Path) -> Path:
    """Cria um arquivo .yxmd temporario para testes."""
    filepath = tmp_path / "test_workflow.yxmd"
    filepath.write_text(SAMPLE_ALTERYX_XML, encoding="utf-8")
    return filepath


@pytest.fixture
def parser() -> AlteryxParser:
    """Retorna instancia do parser."""
    return AlteryxParser()


class TestAlteryxParser:
    """Testes do parser Alteryx."""

    def test_parse_valid_file(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica parsing de arquivo valido."""
        workflow = parser.parse(sample_yxmd_file)
        assert workflow is not None
        assert workflow.name == "test_workflow"
        assert workflow._parsed is True

    def test_parse_node_count(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica contagem de nodes."""
        workflow = parser.parse(sample_yxmd_file)
        assert workflow.node_count == 3

    def test_parse_connection_count(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica contagem de conexoes."""
        workflow = parser.parse(sample_yxmd_file)
        assert workflow.connection_count == 2

    def test_parse_properties(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica extracao de propriedades."""
        workflow = parser.parse(sample_yxmd_file)
        assert "meta_Name" in workflow.properties
        assert workflow.properties["meta_Name"] == "TestWorkflow"
        assert "meta_Description" in workflow.properties

    def test_parse_nodes_data(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica dados dos nodes extraidos."""
        workflow = parser.parse(sample_yxmd_file)
        tool_ids = [n["tool_id"] for n in workflow.nodes]
        assert "1" in tool_ids
        assert "2" in tool_ids
        assert "3" in tool_ids

    def test_parse_node_annotations(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica extracao de anotacoes."""
        workflow = parser.parse(sample_yxmd_file)
        annotations = {n["tool_id"]: n["annotation"] for n in workflow.nodes}
        assert annotations["1"] == "Input de dados"
        assert annotations["2"] == "Filtrar registros validos"

    def test_parse_connections_data(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica dados das conexoes extraidas."""
        workflow = parser.parse(sample_yxmd_file)
        conn = workflow.connections[0]
        assert conn["origin_tool_id"] == "1"
        assert conn["dest_tool_id"] == "2"

    def test_parse_file_not_found(self, parser: AlteryxParser) -> None:
        """Verifica erro ao parsear arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/inexistente/arquivo.yxmd"))

    def test_parse_unsupported_extension(self, parser: AlteryxParser, tmp_path: Path) -> None:
        """Verifica erro ao parsear extensao nao suportada."""
        filepath = tmp_path / "arquivo.txt"
        filepath.write_text("conteudo")
        with pytest.raises(ValueError):
            parser.parse(filepath)

    def test_cache_hit(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica que cache retorna mesmo objeto."""
        workflow1 = parser.parse(sample_yxmd_file)
        workflow2 = parser.parse(sample_yxmd_file)
        assert workflow1 is workflow2

    def test_clear_cache(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica limpeza de cache."""
        parser.parse(sample_yxmd_file)
        parser.clear_cache()
        assert len(parser._cache) == 0

    def test_find_node_by_tool_id(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica busca de node por ToolID."""
        workflow = parser.parse(sample_yxmd_file)
        node = parser.find_node_by_tool_id(workflow, "2")
        assert node is not None
        assert node.get("ToolID") == "2"

    def test_find_node_nonexistent(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica busca de node inexistente."""
        workflow = parser.parse(sample_yxmd_file)
        node = parser.find_node_by_tool_id(workflow, "999")
        assert node is None

    def test_parse_from_string(self, parser: AlteryxParser) -> None:
        """Verifica parsing a partir de string XML."""
        workflow = parser.parse_from_string(SAMPLE_ALTERYX_XML)
        assert workflow.node_count == 3
        assert workflow.connection_count == 2

    def test_find_nodes_by_type(self, parser: AlteryxParser, sample_yxmd_file: Path) -> None:
        """Verifica busca de nodes por tipo de plugin."""
        workflow = parser.parse(sample_yxmd_file)
        input_nodes = parser.find_nodes_by_type(
            workflow,
            "AlteryxBasePluginsGui.DbFileInput.DbFileInput",
        )
        assert len(input_nodes) == 1


# "Testa cedo, testa frequentemente." - Kent Beck
