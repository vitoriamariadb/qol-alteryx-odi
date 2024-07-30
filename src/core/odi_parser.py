"""
ODI Parser Module
Parsing de packages ODI (Oracle Data Integrator) em formato XML.
Extrai metadados de scenarios, packages, interfaces e steps.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class OdiScenario:
    """Representacao de um cenario ODI."""
    name: str
    version: str = ""
    description: str = ""
    folder: str = ""
    variables: list[str] = field(default_factory=list)


@dataclass
class OdiStep:
    """Representacao de um step dentro de um package ODI."""
    name: str
    step_type: str = ""
    command: str = ""
    target_scenario: str = ""
    on_success: str = ""
    on_failure: str = ""


@dataclass
class OdiInterface:
    """Representacao de uma interface ODI."""
    name: str
    source_schema: str = ""
    target_schema: str = ""
    source_table: str = ""
    target_table: str = ""
    integration_type: str = ""
    mappings: list[dict] = field(default_factory=list)


@dataclass
class OdiPackage:
    """Representacao estruturada de um package ODI."""
    name: str
    filepath: Path
    version: str = ""
    description: str = ""
    folder: str = ""
    project: str = ""
    steps: list[OdiStep] = field(default_factory=list)
    scenarios: list[OdiScenario] = field(default_factory=list)
    interfaces: list[OdiInterface] = field(default_factory=list)
    variables: dict = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def scenario_count(self) -> int:
        return len(self.scenarios)


class OdiParser:
    """Parser para arquivos de package ODI em formato XML."""

    SUPPORTED_TAGS = {
        "Scenario", "Package", "Interface",
        "OdiScenario", "OdiPackage", "OdiInterface",
    }

    def __init__(self) -> None:
        self._cache: dict[str, OdiPackage] = {}

    def parse(self, filepath: Path) -> OdiPackage:
        """Faz parsing de um arquivo ODI XML e retorna o package estruturado."""
        filepath = Path(filepath)
        cache_key = str(filepath.resolve())

        if cache_key in self._cache:
            logger.info("Usando cache para: %s", filepath.name)
            return self._cache[cache_key]

        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {filepath}")

        package = OdiPackage(name=filepath.stem, filepath=filepath)

        try:
            tree = ET.parse(str(filepath))
            root = tree.getroot()
        except ET.ParseError as exc:
            logger.error("Falha ao parsear ODI XML: %s - %s", filepath.name, exc)
            raise

        package.version = self._extract_attribute(root, "Version", "")
        package.description = self._extract_text(root, "Description")
        package.folder = self._extract_text(root, "Folder")
        package.project = self._extract_text(root, "Project")
        package.steps = self._extract_steps(root)
        package.scenarios = self._extract_scenarios(root)
        package.interfaces = self._extract_interfaces(root)
        package.variables = self._extract_variables(root)

        self._cache[cache_key] = package
        logger.info(
            "Parsed ODI: %s (%d steps, %d scenarios)",
            filepath.name,
            package.step_count,
            package.scenario_count,
        )
        return package

    def _extract_attribute(self, elem: ET.Element, attr: str, default: str = "") -> str:
        """Extrai um atributo de um elemento."""
        return elem.get(attr, default)

    def _extract_text(self, root: ET.Element, tag: str) -> str:
        """Extrai texto de um sub-elemento."""
        elem = root.find(f".//{tag}")
        if elem is not None and elem.text:
            return elem.text.strip()
        return ""

    def _extract_steps(self, root: ET.Element) -> list[OdiStep]:
        """Extrai steps de um package ODI."""
        steps: list[OdiStep] = []

        for step_elem in root.iter("Step"):
            step = OdiStep(
                name=step_elem.get("Name", ""),
                step_type=step_elem.get("Type", ""),
            )

            command_elem = step_elem.find("Command")
            if command_elem is not None and command_elem.text:
                step.command = command_elem.text.strip()

            scenario_ref = step_elem.find("ScenarioRef")
            if scenario_ref is not None:
                step.target_scenario = scenario_ref.get("Name", "")

            success_elem = step_elem.find("OnSuccess")
            if success_elem is not None:
                step.on_success = success_elem.get("NextStep", "")

            failure_elem = step_elem.find("OnFailure")
            if failure_elem is not None:
                step.on_failure = failure_elem.get("NextStep", "")

            steps.append(step)

        return steps

    def _extract_scenarios(self, root: ET.Element) -> list[OdiScenario]:
        """Extrai cenarios referenciados no package."""
        scenarios: list[OdiScenario] = []

        for scenario_elem in root.iter("Scenario"):
            scenario = OdiScenario(
                name=scenario_elem.get("Name", ""),
                version=scenario_elem.get("Version", ""),
            )

            desc = scenario_elem.find("Description")
            if desc is not None and desc.text:
                scenario.description = desc.text.strip()

            folder = scenario_elem.find("Folder")
            if folder is not None and folder.text:
                scenario.folder = folder.text.strip()

            for var_elem in scenario_elem.iter("Variable"):
                var_name = var_elem.get("Name", "")
                if var_name:
                    scenario.variables.append(var_name)

            scenarios.append(scenario)

        return scenarios

    def _extract_interfaces(self, root: ET.Element) -> list[OdiInterface]:
        """Extrai interfaces definidas no package."""
        interfaces: list[OdiInterface] = []

        for iface_elem in root.iter("Interface"):
            iface = OdiInterface(
                name=iface_elem.get("Name", ""),
            )

            source = iface_elem.find("Source")
            if source is not None:
                iface.source_schema = source.get("Schema", "")
                iface.source_table = source.get("Table", "")

            target = iface_elem.find("Target")
            if target is not None:
                iface.target_schema = target.get("Schema", "")
                iface.target_table = target.get("Table", "")

            iface.integration_type = self._extract_text(iface_elem, "IntegrationType")

            for mapping_elem in iface_elem.iter("Mapping"):
                mapping = {
                    "source_col": mapping_elem.get("SourceColumn", ""),
                    "target_col": mapping_elem.get("TargetColumn", ""),
                    "expression": mapping_elem.get("Expression", ""),
                }
                iface.mappings.append(mapping)

            interfaces.append(iface)

        return interfaces

    def _extract_variables(self, root: ET.Element) -> dict:
        """Extrai variaveis definidas no package."""
        variables: dict = {}
        for var_elem in root.iter("Variable"):
            name = var_elem.get("Name", "")
            default = var_elem.get("Default", "")
            var_type = var_elem.get("Type", "")
            if name:
                variables[name] = {
                    "default": default,
                    "type": var_type,
                }
        return variables

    def parse_from_string(self, xml_content: str, name: str = "memory") -> OdiPackage:
        """Faz parsing de conteudo ODI XML a partir de uma string."""
        package = OdiPackage(name=name, filepath=Path(name))

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            logger.error("Falha ao parsear ODI XML string: %s", exc)
            raise

        package.version = self._extract_attribute(root, "Version", "")
        package.description = self._extract_text(root, "Description")
        package.steps = self._extract_steps(root)
        package.scenarios = self._extract_scenarios(root)
        package.interfaces = self._extract_interfaces(root)
        package.variables = self._extract_variables(root)

        return package

    def clear_cache(self) -> None:
        """Limpa o cache de packages parseados."""
        self._cache.clear()
        logger.info("Cache ODI limpo")


# "A logica e o principio de todos os principios." - Aristoteles
