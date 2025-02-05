"""
Validation Module
Regras de validacao para workflows Alteryx e packages ODI.
Verifica integridade, conexoes orfas, nodes desconectados e padroes incorretos.
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from src.core.alteryx_parser import AlteryxParser, AlteryxWorkflow
from src.core.odi_parser import OdiParser, OdiPackage

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Representa um problema encontrado durante validacao."""
    severity: str
    code: str
    message: str
    node_id: str = ""
    details: str = ""

    def __str__(self) -> str:
        prefix = f"[{self.severity.upper()}] {self.code}"
        if self.node_id:
            prefix += f" (Node {self.node_id})"
        return f"{prefix}: {self.message}"


@dataclass
class ValidationResult:
    """Resultado completo da validacao."""
    filepath: Path
    issues: list[ValidationIssue] = field(default_factory=list)
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "info")

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "error":
            self.passed = False


HARDCODED_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
HARDCODED_SERVER_PATTERN = re.compile(r"\b\w+\.\w+\.\w+:\d+/\w+\b")
EMPTY_ANNOTATION_THRESHOLD = 0.5


class WorkflowValidator:
    """Validador de workflows Alteryx."""

    def __init__(self) -> None:
        self._parser = AlteryxParser()

    def validate(self, filepath: Path) -> ValidationResult:
        """Executa todas as regras de validacao em um workflow."""
        result = ValidationResult(filepath=filepath)

        try:
            workflow = self._parser.parse(filepath)
        except Exception as exc:
            result.add_issue(ValidationIssue(
                severity="error",
                code="PARSE_ERROR",
                message=f"Falha ao parsear: {exc}",
            ))
            return result

        self._check_orphan_nodes(workflow, result)
        self._check_disconnected_outputs(workflow, result)
        self._check_hardcoded_dates(workflow, result)
        self._check_hardcoded_servers(workflow, result)
        self._check_missing_annotations(workflow, result)
        self._check_duplicate_tool_ids(workflow, result)
        self._check_empty_configurations(workflow, result)

        logger.info(
            "Validacao %s: %d erros, %d avisos",
            filepath.name,
            result.error_count,
            result.warning_count,
        )
        return result

    def _check_orphan_nodes(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica nodes sem nenhuma conexao (orfaos)."""
        connected_ids: set[str] = set()
        for conn in workflow.connections:
            connected_ids.add(conn["origin_tool_id"])
            connected_ids.add(conn["dest_tool_id"])

        for node in workflow.nodes:
            tool_id = node["tool_id"]
            if tool_id and tool_id not in connected_ids:
                result.add_issue(ValidationIssue(
                    severity="warning",
                    code="ORPHAN_NODE",
                    message="Node sem conexoes detectado",
                    node_id=tool_id,
                ))

    def _check_disconnected_outputs(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica nodes de output sem conexao de entrada."""
        dest_ids = {conn["dest_tool_id"] for conn in workflow.connections}
        output_plugins = {
            "AlteryxBasePluginsGui.DbFileOutput.DbFileOutput",
            "AlteryxBasePluginsGui.Output.Output",
        }

        for node in workflow.nodes:
            plugin = node.get("gui_settings", {}).get("Plugin", "")
            if plugin in output_plugins and node["tool_id"] not in dest_ids:
                result.add_issue(ValidationIssue(
                    severity="error",
                    code="DISCONNECTED_OUTPUT",
                    message="Node de output sem conexao de entrada",
                    node_id=node["tool_id"],
                ))

    def _check_hardcoded_dates(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica datas hardcoded nos nodes."""
        if workflow.root is None:
            return

        for node in workflow.root.iter("Node"):
            tool_id = node.get("ToolID", "")
            for elem in node.iter():
                if elem.text and HARDCODED_DATE_PATTERN.search(elem.text):
                    result.add_issue(ValidationIssue(
                        severity="info",
                        code="HARDCODED_DATE",
                        message=f"Data hardcoded detectada em <{elem.tag}>",
                        node_id=tool_id,
                        details=elem.text[:80],
                    ))
                    break

    def _check_hardcoded_servers(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica servidores hardcoded nos nodes."""
        if workflow.root is None:
            return

        for node in workflow.root.iter("Node"):
            tool_id = node.get("ToolID", "")
            for elem in node.iter():
                if elem.text and HARDCODED_SERVER_PATTERN.search(elem.text):
                    result.add_issue(ValidationIssue(
                        severity="info",
                        code="HARDCODED_SERVER",
                        message=f"Servidor hardcoded detectado em <{elem.tag}>",
                        node_id=tool_id,
                    ))
                    break

    def _check_missing_annotations(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica nodes sem anotacao descritiva."""
        if not workflow.nodes:
            return

        missing = sum(1 for n in workflow.nodes if not n.get("annotation"))
        ratio = missing / len(workflow.nodes) if workflow.nodes else 0

        if ratio > EMPTY_ANNOTATION_THRESHOLD:
            result.add_issue(ValidationIssue(
                severity="warning",
                code="MISSING_ANNOTATIONS",
                message=f"{missing}/{len(workflow.nodes)} nodes sem anotacao ({ratio:.0%})",
            ))

    def _check_duplicate_tool_ids(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica Tool IDs duplicados."""
        seen: dict[str, int] = {}
        for node in workflow.nodes:
            tid = node["tool_id"]
            seen[tid] = seen.get(tid, 0) + 1

        for tid, count in seen.items():
            if count > 1:
                result.add_issue(ValidationIssue(
                    severity="error",
                    code="DUPLICATE_TOOL_ID",
                    message=f"ToolID duplicado ({count} ocorrencias)",
                    node_id=tid,
                ))

    def _check_empty_configurations(self, workflow: AlteryxWorkflow, result: ValidationResult) -> None:
        """Verifica nodes com configuracao vazia."""
        for node in workflow.nodes:
            if not node.get("properties"):
                plugin = node.get("gui_settings", {}).get("Plugin", "")
                if plugin:
                    result.add_issue(ValidationIssue(
                        severity="warning",
                        code="EMPTY_CONFIG",
                        message=f"Configuracao vazia para {plugin}",
                        node_id=node["tool_id"],
                    ))


class PackageValidator:
    """Validador de packages ODI."""

    def __init__(self) -> None:
        self._parser = OdiParser()

    def validate(self, filepath: Path) -> ValidationResult:
        """Executa validacao em um package ODI."""
        result = ValidationResult(filepath=filepath)

        try:
            package = self._parser.parse(filepath)
        except Exception as exc:
            result.add_issue(ValidationIssue(
                severity="error",
                code="PARSE_ERROR",
                message=f"Falha ao parsear ODI: {exc}",
            ))
            return result

        self._check_empty_steps(package, result)
        self._check_broken_flow(package, result)
        self._check_missing_scenarios(package, result)

        logger.info(
            "Validacao ODI %s: %d erros, %d avisos",
            filepath.name,
            result.error_count,
            result.warning_count,
        )
        return result

    def _check_empty_steps(self, package: OdiPackage, result: ValidationResult) -> None:
        """Verifica steps vazios no package."""
        for step in package.steps:
            if not step.command and not step.target_scenario:
                result.add_issue(ValidationIssue(
                    severity="warning",
                    code="EMPTY_STEP",
                    message=f"Step '{step.name}' sem comando ou cenario",
                ))

    def _check_broken_flow(self, package: OdiPackage, result: ValidationResult) -> None:
        """Verifica fluxo quebrado entre steps."""
        step_names = {s.name for s in package.steps}

        for step in package.steps:
            if step.on_success and step.on_success not in step_names:
                result.add_issue(ValidationIssue(
                    severity="error",
                    code="BROKEN_FLOW",
                    message=f"Step '{step.name}' referencia '{step.on_success}' inexistente",
                ))

            if step.on_failure and step.on_failure not in step_names:
                result.add_issue(ValidationIssue(
                    severity="error",
                    code="BROKEN_FAILURE_FLOW",
                    message=f"Step '{step.name}' fallback '{step.on_failure}' inexistente",
                ))

    def _check_missing_scenarios(self, package: OdiPackage, result: ValidationResult) -> None:
        """Verifica steps que referenciam cenarios nao listados."""
        scenario_names = {s.name for s in package.scenarios}

        for step in package.steps:
            if step.target_scenario and step.target_scenario not in scenario_names:
                result.add_issue(ValidationIssue(
                    severity="warning",
                    code="MISSING_SCENARIO",
                    message=f"Step '{step.name}' referencia cenario '{step.target_scenario}' nao listado",
                ))


# "Confiar, mas verificar." - Proverbio russo

