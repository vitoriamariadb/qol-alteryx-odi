"""
Testes para o modulo OdiParser.
Verifica parsing de XML ODI, extracao de steps, scenarios e interfaces.
"""
from pathlib import Path

import pytest

from src.core.odi_parser import OdiParser, OdiPackage


SAMPLE_ODI_XML = """<?xml version="1.0"?>
<OdiPackage Name="PKG_ETL_VENDAS" Version="2.0">
  <Description>Package de ETL para vendas mensais</Description>
  <Project>Projeto_DW</Project>
  <Folder>Vendas</Folder>
  <Steps>
    <Step Name="Extrair_Fonte" Type="DataStoreCommand">
      <Command>SELECT * FROM vendas_raw</Command>
      <OnSuccess NextStep="Transformar_Dados"/>
      <OnFailure NextStep="Log_Erro"/>
    </Step>
    <Step Name="Transformar_Dados" Type="ProcedureCommand">
      <Command>CALL proc_transform_vendas()</Command>
      <ScenarioRef Name="SCN_TRANSFORM"/>
      <OnSuccess NextStep="Carregar_DW"/>
      <OnFailure NextStep="Log_Erro"/>
    </Step>
    <Step Name="Carregar_DW" Type="DataStoreCommand">
      <Command>INSERT INTO dw_vendas SELECT * FROM stg_vendas</Command>
      <OnSuccess NextStep="Notificar"/>
    </Step>
    <Step Name="Notificar" Type="OdiCommand">
      <Command>SEND_NOTIFICATION</Command>
    </Step>
    <Step Name="Log_Erro" Type="OdiCommand">
      <Command>LOG_ERROR</Command>
    </Step>
  </Steps>
  <Scenarios>
    <Scenario Name="SCN_TRANSFORM" Version="001">
      <Description>Cenario de transformacao de vendas</Description>
      <Folder>Transformacoes</Folder>
      <Variable Name="V_DATA_REF"/>
      <Variable Name="V_SCHEMA"/>
    </Scenario>
    <Scenario Name="SCN_LOAD" Version="002">
      <Description>Cenario de carga</Description>
    </Scenario>
  </Scenarios>
  <Interfaces>
    <Interface Name="INT_VENDAS_STG">
      <Source Schema="SRC" Table="VENDAS_RAW"/>
      <Target Schema="STG" Table="STG_VENDAS"/>
      <IntegrationType>IKM Oracle Incremental Update</IntegrationType>
      <Mappings>
        <Mapping SourceColumn="ID" TargetColumn="VENDA_ID" Expression="ID"/>
        <Mapping SourceColumn="VALOR" TargetColumn="VALOR_VENDA" Expression="VALOR * 1.0"/>
      </Mappings>
    </Interface>
  </Interfaces>
  <Variables>
    <Variable Name="V_DATA_REF" Type="DATE" Default="2024-01-01"/>
    <Variable Name="V_SCHEMA" Type="STRING" Default="DW_PROD"/>
  </Variables>
</OdiPackage>"""


@pytest.fixture
def sample_odi_file(tmp_path: Path) -> Path:
    """Cria um arquivo ODI XML temporario para testes."""
    filepath = tmp_path / "package_etl.xml"
    filepath.write_text(SAMPLE_ODI_XML, encoding="utf-8")
    return filepath


@pytest.fixture
def parser() -> OdiParser:
    """Retorna instancia do parser ODI."""
    return OdiParser()


class TestOdiParser:
    """Testes do parser ODI."""

    def test_parse_valid_file(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica parsing de arquivo ODI valido."""
        package = parser.parse(sample_odi_file)
        assert package is not None
        assert package.name == "package_etl"

    def test_parse_step_count(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica contagem de steps."""
        package = parser.parse(sample_odi_file)
        assert package.step_count == 5

    def test_parse_scenario_count(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica contagem de cenarios."""
        package = parser.parse(sample_odi_file)
        assert package.scenario_count == 2

    def test_parse_description(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica extracao de descricao."""
        package = parser.parse(sample_odi_file)
        assert "vendas mensais" in package.description

    def test_parse_project(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica extracao de projeto."""
        package = parser.parse(sample_odi_file)
        assert package.project == "Projeto_DW"

    def test_parse_steps_data(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica dados dos steps extraidos."""
        package = parser.parse(sample_odi_file)
        step_names = [s.name for s in package.steps]
        assert "Extrair_Fonte" in step_names
        assert "Transformar_Dados" in step_names
        assert "Carregar_DW" in step_names

    def test_parse_step_flow(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica fluxo de sucesso/falha entre steps."""
        package = parser.parse(sample_odi_file)
        step = next(s for s in package.steps if s.name == "Extrair_Fonte")
        assert step.on_success == "Transformar_Dados"
        assert step.on_failure == "Log_Erro"

    def test_parse_step_scenario_ref(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica referencia a cenario no step."""
        package = parser.parse(sample_odi_file)
        step = next(s for s in package.steps if s.name == "Transformar_Dados")
        assert step.target_scenario == "SCN_TRANSFORM"

    def test_parse_scenarios(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica extracao de cenarios."""
        package = parser.parse(sample_odi_file)
        scenario_names = [s.name for s in package.scenarios]
        assert "SCN_TRANSFORM" in scenario_names
        assert "SCN_LOAD" in scenario_names

    def test_parse_scenario_variables(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica variaveis dos cenarios."""
        package = parser.parse(sample_odi_file)
        scenario = next(s for s in package.scenarios if s.name == "SCN_TRANSFORM")
        assert "V_DATA_REF" in scenario.variables
        assert "V_SCHEMA" in scenario.variables

    def test_parse_interfaces(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica extracao de interfaces."""
        package = parser.parse(sample_odi_file)
        assert len(package.interfaces) == 1
        iface = package.interfaces[0]
        assert iface.name == "INT_VENDAS_STG"
        assert iface.source_schema == "SRC"
        assert iface.target_table == "STG_VENDAS"

    def test_parse_interface_mappings(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica mappings da interface."""
        package = parser.parse(sample_odi_file)
        iface = package.interfaces[0]
        assert len(iface.mappings) == 2
        assert iface.mappings[0]["source_col"] == "ID"
        assert iface.mappings[0]["target_col"] == "VENDA_ID"

    def test_parse_variables(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica extracao de variaveis globais."""
        package = parser.parse(sample_odi_file)
        assert "V_DATA_REF" in package.variables
        assert package.variables["V_DATA_REF"]["type"] == "DATE"
        assert package.variables["V_DATA_REF"]["default"] == "2024-01-01"

    def test_parse_file_not_found(self, parser: OdiParser) -> None:
        """Verifica erro ao parsear arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/inexistente/package.xml"))

    def test_cache_hit(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica cache."""
        pkg1 = parser.parse(sample_odi_file)
        pkg2 = parser.parse(sample_odi_file)
        assert pkg1 is pkg2

    def test_clear_cache(self, parser: OdiParser, sample_odi_file: Path) -> None:
        """Verifica limpeza de cache."""
        parser.parse(sample_odi_file)
        parser.clear_cache()
        assert len(parser._cache) == 0

    def test_parse_from_string(self, parser: OdiParser) -> None:
        """Verifica parsing a partir de string."""
        package = parser.parse_from_string(SAMPLE_ODI_XML)
        assert package.step_count == 5
        assert package.scenario_count == 2


# "Sem testes, o codigo e apenas uma opiniao." - Desconhecido

