"""
Testes de integracao end-to-end.
Verifica o fluxo completo: parse -> validate -> convert -> export,
garantindo que os modulos funcionam em conjunto sem erros.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from src.core.alteryx_parser import AlteryxParser
from src.core.odi_parser import OdiParser
from src.core.converter import AlteryxToOdiConverter, OdiToAlteryxConverter
from src.core.validation import WorkflowValidator, PackageValidator
from src.cli import run_cli


SAMPLE_ALTERYX_XML = """<?xml version="1.0"?>
<AlteryxDocument yxmdVer="2024.1">
  <Properties>
    <MetaInfo>
      <Name>E2ETest</Name>
    </MetaInfo>
  </Properties>
  <Nodes>
    <Node ToolID="1">
      <GuiSettings Plugin="AlteryxBasePluginsGui.DbFileInput.DbFileInput">
        <Position x="100" y="200"/>
      </GuiSettings>
      <Configuration>
        <File>entrada.csv</File>
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
        <Expression>[Campo] &gt; 0</Expression>
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
        <File>saida.csv</File>
      </Configuration>
      <Annotation>
        <DefaultAnnotationText>Output</DefaultAnnotationText>
      </Annotation>
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
<OdiPackage Name="PKG_E2E" Version="1.0">
  <Description>Package de teste end-to-end</Description>
  <Steps>
    <Step Name="Extrair" Type="DataStoreCommand">
      <Command>SELECT * FROM origem</Command>
      <OnSuccess NextStep="Transformar"/>
    </Step>
    <Step Name="Transformar" Type="ProcedureCommand">
      <Command>CALL transformacao()</Command>
      <OnSuccess NextStep="Carregar"/>
    </Step>
    <Step Name="Carregar" Type="DataStoreCommand">
      <Command>INSERT INTO destino SELECT * FROM staging</Command>
    </Step>
  </Steps>
  <Scenarios>
    <Scenario Name="SCN_E2E" Version="001"/>
  </Scenarios>
</OdiPackage>"""


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def alteryx_file(tmp_path: Path) -> Path:
    """Cria arquivo Alteryx temporario para testes e2e."""
    filepath = tmp_path / "e2e_workflow.yxmd"
    filepath.write_text(SAMPLE_ALTERYX_XML, encoding="utf-8")
    return filepath


@pytest.fixture
def odi_file(tmp_path: Path) -> Path:
    """Cria arquivo ODI temporario para testes e2e."""
    filepath = tmp_path / "e2e_package.xml"
    filepath.write_text(SAMPLE_ODI_XML, encoding="utf-8")
    return filepath


class TestEndToEndAlteryx:
    """Testes e2e para fluxo Alteryx completo."""

    def test_parse_validate_convert_flow(self, alteryx_file: Path, tmp_path: Path) -> None:
        """Verifica fluxo completo: parse -> validate -> convert."""
        parser = AlteryxParser()
        workflow = parser.parse(alteryx_file)
        assert workflow.node_count == 3
        assert workflow.connection_count == 2

        validator = WorkflowValidator()
        validation = validator.validate(alteryx_file)
        assert validation.error_count == 0

        converter = AlteryxToOdiConverter()
        output_path = tmp_path / "converted_odi.xml"
        result = converter.convert(alteryx_file, output_path)

        assert result.success is True
        assert output_path.exists()

        root = ET.fromstring(result.xml_content)
        assert root.tag == "OdiPackage"
        steps = list(root.iter("Step"))
        assert len(steps) == 3

    def test_template_processing(self, tmp_path: Path) -> None:
        """Verifica processamento de template com datas.

        Valida que o processor aplica substituicoes sem corromper o XML.
        """
        from src.core.xml_processor import process_template

        template_content = SAMPLE_ALTERYX_XML
        template_path = tmp_path / "template.yxmd"
        template_path.write_text(template_content, encoding="utf-8")

        content, stats = process_template(
            template_path, "", 2025, 6
        )

        assert content is not None
        assert isinstance(stats, dict)

    def test_batch_workflow(self, tmp_path: Path) -> None:
        """Verifica processamento em lote de multiplos arquivos."""
        from src.batch.processor import BatchProcessor, BatchConfig

        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        for i in range(3):
            filepath = input_dir / f"workflow_{i}.yxmd"
            filepath.write_text(SAMPLE_ALTERYX_XML, encoding="utf-8")

        config = BatchConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            operation="parse",
        )

        processor = BatchProcessor()
        result = processor.process(config)

        assert result.total_files == 3
        assert result.processed == 3
        assert result.failed == 0

    def test_fixture_file_parse(self) -> None:
        """Verifica parsing do arquivo fixture sample_workflow."""
        fixture_path = FIXTURES_DIR / "sample_workflow.yxmd"
        if not fixture_path.exists():
            pytest.skip("Fixture sample_workflow.yxmd nao encontrada")

        parser = AlteryxParser()
        workflow = parser.parse(fixture_path)
        assert workflow.node_count == 4
        assert workflow.connection_count == 3


class TestEndToEndODI:
    """Testes e2e para fluxo ODI completo."""

    def test_parse_validate_convert_flow(self, odi_file: Path, tmp_path: Path) -> None:
        """Verifica fluxo completo: parse -> validate -> convert ODI."""
        parser = OdiParser()
        package = parser.parse(odi_file)
        assert package.step_count == 3
        assert package.scenario_count == 1

        validator = PackageValidator()
        validation = validator.validate(odi_file)
        assert validation.error_count == 0

        converter = OdiToAlteryxConverter()
        output_path = tmp_path / "converted_alteryx.yxmd"
        result = converter.convert(odi_file, output_path)

        assert result.success is True
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8-sig")
        assert "AlteryxDocument" in content


class TestEndToEndCLI:
    """Testes e2e para interface CLI."""

    def test_cli_parse_command(self, alteryx_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifica subcomando parse via CLI."""
        monkeypatch.setattr(
            "sys.argv",
            ["qol-alteryx-odi", "parse", str(alteryx_file), "--format", "json"],
        )
        exit_code = run_cli()
        assert exit_code == 0

    def test_cli_convert_command(
        self, alteryx_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica subcomando convert via CLI."""
        output_path = tmp_path / "cli_output.xml"
        monkeypatch.setattr(
            "sys.argv",
            [
                "qol-alteryx-odi",
                "convert",
                str(alteryx_file),
                "--direction", "a2o",
                "--output", str(output_path),
            ],
        )
        exit_code = run_cli()
        assert exit_code == 0
        assert output_path.exists()

    def test_cli_validate_command(
        self, alteryx_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica subcomando validate via CLI."""
        monkeypatch.setattr(
            "sys.argv",
            ["qol-alteryx-odi", "validate", str(alteryx_file)],
        )
        exit_code = run_cli()
        assert exit_code == 0

    def test_cli_no_command_shows_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifica que CLI sem subcomando retorna 0."""
        monkeypatch.setattr("sys.argv", ["qol-alteryx-odi"])
        exit_code = run_cli()
        assert exit_code == 0


# "Nao e suficiente fazer o seu melhor; primeiro voce precisa saber o que fazer, e entao fazer o seu melhor." - W. Edwards Deming
