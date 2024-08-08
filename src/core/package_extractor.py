"""
Package Extractor Module
Extrai metadados estruturados de packages ODI para analise e documentacao.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.core.odi_parser import OdiParser, OdiPackage, OdiStep

logger = logging.getLogger(__name__)


@dataclass
class StepDependency:
    """Representacao de uma dependencia entre steps."""
    step_name: str
    depends_on: list[str] = field(default_factory=list)
    depended_by: list[str] = field(default_factory=list)


@dataclass
class ExecutionFlow:
    """Fluxo de execucao extraido de um package."""
    first_step: str = ""
    steps_order: list[str] = field(default_factory=list)
    success_paths: dict = field(default_factory=dict)
    failure_paths: dict = field(default_factory=dict)
    dependencies: list[StepDependency] = field(default_factory=list)


@dataclass
class PackageMetadata:
    """Metadados completos extraidos de um package ODI."""
    name: str
    filepath: Path
    version: str = ""
    description: str = ""
    project: str = ""
    folder: str = ""
    total_steps: int = 0
    total_scenarios: int = 0
    total_interfaces: int = 0
    variables: dict = field(default_factory=dict)
    execution_flow: Optional[ExecutionFlow] = None
    data_sources: list[str] = field(default_factory=list)
    data_targets: list[str] = field(default_factory=list)


class PackageExtractor:
    """Extrator de metadados de packages ODI."""

    def __init__(self) -> None:
        self._parser = OdiParser()

    def extract(self, filepath: Path) -> PackageMetadata:
        """Extrai metadados completos de um package ODI."""
        package = self._parser.parse(filepath)
        metadata = PackageMetadata(
            name=package.name,
            filepath=filepath,
            version=package.version,
            description=package.description,
            project=package.project,
            folder=package.folder,
            total_steps=package.step_count,
            total_scenarios=package.scenario_count,
            total_interfaces=len(package.interfaces),
            variables=package.variables,
        )

        metadata.execution_flow = self._build_execution_flow(package)
        metadata.data_sources = self._extract_data_sources(package)
        metadata.data_targets = self._extract_data_targets(package)

        logger.info(
            "Extraido package: %s - %d steps, %d fontes, %d destinos",
            metadata.name,
            metadata.total_steps,
            len(metadata.data_sources),
            len(metadata.data_targets),
        )
        return metadata

    def _build_execution_flow(self, package: OdiPackage) -> ExecutionFlow:
        """Constroi o fluxo de execucao a partir dos steps."""
        flow = ExecutionFlow()

        if not package.steps:
            return flow

        flow.first_step = package.steps[0].name
        step_names = {s.name for s in package.steps}

        for step in package.steps:
            flow.steps_order.append(step.name)
            if step.on_success:
                flow.success_paths[step.name] = step.on_success
            if step.on_failure:
                flow.failure_paths[step.name] = step.on_failure

        referenced_as_next = set()
        for step in package.steps:
            if step.on_success:
                referenced_as_next.add(step.on_success)

        for step_name in step_names:
            dep = StepDependency(step_name=step_name)
            for other_step in package.steps:
                if other_step.on_success == step_name:
                    dep.depends_on.append(other_step.name)
                if step.on_success == other_step.name:
                    dep.depended_by.append(other_step.name)
            flow.dependencies.append(dep)

        return flow

    def _extract_data_sources(self, package: OdiPackage) -> list[str]:
        """Extrai nomes das fontes de dados."""
        sources: list[str] = []
        for iface in package.interfaces:
            source_id = f"{iface.source_schema}.{iface.source_table}"
            if source_id not in sources and iface.source_table:
                sources.append(source_id)
        return sources

    def _extract_data_targets(self, package: OdiPackage) -> list[str]:
        """Extrai nomes dos destinos de dados."""
        targets: list[str] = []
        for iface in package.interfaces:
            target_id = f"{iface.target_schema}.{iface.target_table}"
            if target_id not in targets and iface.target_table:
                targets.append(target_id)
        return targets

    def extract_summary(self, filepath: Path) -> dict:
        """Extrai um resumo simplificado do package."""
        metadata = self.extract(filepath)
        return {
            "name": metadata.name,
            "version": metadata.version,
            "project": metadata.project,
            "total_steps": metadata.total_steps,
            "total_scenarios": metadata.total_scenarios,
            "total_interfaces": metadata.total_interfaces,
            "data_sources": metadata.data_sources,
            "data_targets": metadata.data_targets,
            "variables": list(metadata.variables.keys()),
        }

    def extract_multiple(self, filepaths: list[Path]) -> list[PackageMetadata]:
        """Extrai metadados de multiplos packages."""
        results: list[PackageMetadata] = []
        for fp in filepaths:
            try:
                metadata = self.extract(fp)
                results.append(metadata)
            except Exception as exc:
                logger.error("Falha ao extrair %s: %s", fp.name, exc)
        return results


# "A simplicidade e a sofisticacao suprema." - Leonardo da Vinci
