"""
Documentation Exporter Module
Exporta documentacao de workflows e packages em formato Markdown e texto.
Gera relatorios detalhados com metadados, fluxo de execucao e dependencias.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.workflow_extractor import WorkflowExtractor, WorkflowMetadata
from src.core.package_extractor import PackageExtractor, PackageMetadata
from src.core.validation import WorkflowValidator, PackageValidator, ValidationResult

logger = logging.getLogger(__name__)


class DocumentationExporter:
    """Exportador de documentacao para workflows e packages."""

    def __init__(self) -> None:
        self._workflow_extractor = WorkflowExtractor()
        self._package_extractor = PackageExtractor()
        self._workflow_validator = WorkflowValidator()
        self._package_validator = PackageValidator()

    def export_workflow_doc(
        self,
        filepath: Path,
        output_dir: Path,
        include_validation: bool = True,
    ) -> Path:
        """Exporta documentacao de um workflow Alteryx."""
        metadata = self._workflow_extractor.extract(filepath)
        validation = None
        if include_validation:
            validation = self._workflow_validator.validate(filepath)

        output_dir.mkdir(parents=True, exist_ok=True)
        doc_path = output_dir / f"{metadata.name}_doc.md"

        content = self._build_workflow_markdown(metadata, validation)

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("Documentacao exportada: %s", doc_path)
        return doc_path

    def export_package_doc(
        self,
        filepath: Path,
        output_dir: Path,
        include_validation: bool = True,
    ) -> Path:
        """Exporta documentacao de um package ODI."""
        metadata = self._package_extractor.extract(filepath)
        validation = None
        if include_validation:
            validation = self._package_validator.validate(filepath)

        output_dir.mkdir(parents=True, exist_ok=True)
        doc_path = output_dir / f"{metadata.name}_doc.md"

        content = self._build_package_markdown(metadata, validation)

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("Documentacao ODI exportada: %s", doc_path)
        return doc_path

    def _build_workflow_markdown(
        self,
        metadata: WorkflowMetadata,
        validation: Optional[ValidationResult] = None,
    ) -> str:
        """Constroi documentacao Markdown para workflow Alteryx."""
        lines: list[str] = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines.append(f"# Workflow: {metadata.name}")
        lines.append("")
        lines.append(f"Gerado em: {timestamp}")
        lines.append("")

        lines.append("## Informacoes Gerais")
        lines.append("")
        lines.append(f"- **Arquivo**: `{metadata.filepath.name}`")
        lines.append(f"- **Versao**: {metadata.version or 'N/A'}")
        lines.append(f"- **Descricao**: {metadata.description or 'Sem descricao'}")
        lines.append(f"- **Autor**: {metadata.author or 'N/A'}")
        lines.append("")

        lines.append("## Estatisticas")
        lines.append("")
        lines.append(f"| Metrica | Valor |")
        lines.append(f"|---------|-------|")
        lines.append(f"| Total de Tools | {metadata.tool_count} |")
        lines.append(f"| Total de Conexoes | {metadata.connection_count} |")
        lines.append(f"| Tools de Input | {len(metadata.input_tools)} |")
        lines.append(f"| Tools de Output | {len(metadata.output_tools)} |")
        lines.append(f"| Macros | {len(metadata.macro_tools)} |")
        lines.append("")

        if metadata.input_tools:
            lines.append("## Inputs")
            lines.append("")
            for tool in metadata.input_tools:
                lines.append(f"- **ID {tool.tool_id}**: {tool.annotation or tool.plugin_name}")
            lines.append("")

        if metadata.output_tools:
            lines.append("## Outputs")
            lines.append("")
            for tool in metadata.output_tools:
                lines.append(f"- **ID {tool.tool_id}**: {tool.annotation or tool.plugin_name}")
            lines.append("")

        if metadata.constants:
            lines.append("## Constantes")
            lines.append("")
            for name, value in metadata.constants.items():
                lines.append(f"- `{name}` = `{value}`")
            lines.append("")

        if metadata.tools:
            lines.append("## Tools")
            lines.append("")
            lines.append("| ID | Plugin | Anotacao |")
            lines.append("|----|--------|----------|")
            for tool in metadata.tools[:50]:
                ann = tool.annotation[:40] if tool.annotation else "-"
                plugin = tool.plugin_name.split(".")[-1] if tool.plugin_name else "-"
                lines.append(f"| {tool.tool_id} | {plugin} | {ann} |")
            if len(metadata.tools) > 50:
                lines.append(f"| ... | ({len(metadata.tools) - 50} mais) | ... |")
            lines.append("")

        if validation:
            lines.extend(self._build_validation_section(validation))

        lines.append("---")
        lines.append("")
        lines.append(f"Documento gerado automaticamente pelo QoL Alteryx-ODI Tools")

        return "\n".join(lines)

    def _build_package_markdown(
        self,
        metadata: PackageMetadata,
        validation: Optional[ValidationResult] = None,
    ) -> str:
        """Constroi documentacao Markdown para package ODI."""
        lines: list[str] = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines.append(f"# Package ODI: {metadata.name}")
        lines.append("")
        lines.append(f"Gerado em: {timestamp}")
        lines.append("")

        lines.append("## Informacoes Gerais")
        lines.append("")
        lines.append(f"- **Arquivo**: `{metadata.filepath.name}`")
        lines.append(f"- **Versao**: {metadata.version or 'N/A'}")
        lines.append(f"- **Projeto**: {metadata.project or 'N/A'}")
        lines.append(f"- **Pasta**: {metadata.folder or 'N/A'}")
        lines.append(f"- **Descricao**: {metadata.description or 'Sem descricao'}")
        lines.append("")

        lines.append("## Estatisticas")
        lines.append("")
        lines.append(f"| Metrica | Valor |")
        lines.append(f"|---------|-------|")
        lines.append(f"| Total de Steps | {metadata.total_steps} |")
        lines.append(f"| Total de Cenarios | {metadata.total_scenarios} |")
        lines.append(f"| Total de Interfaces | {metadata.total_interfaces} |")
        lines.append(f"| Fontes de Dados | {len(metadata.data_sources)} |")
        lines.append(f"| Destinos de Dados | {len(metadata.data_targets)} |")
        lines.append("")

        if metadata.data_sources:
            lines.append("## Fontes de Dados")
            lines.append("")
            for source in metadata.data_sources:
                lines.append(f"- `{source}`")
            lines.append("")

        if metadata.data_targets:
            lines.append("## Destinos de Dados")
            lines.append("")
            for target in metadata.data_targets:
                lines.append(f"- `{target}`")
            lines.append("")

        if metadata.execution_flow and metadata.execution_flow.steps_order:
            lines.append("## Fluxo de Execucao")
            lines.append("")
            for idx, step_name in enumerate(metadata.execution_flow.steps_order, 1):
                lines.append(f"{idx}. `{step_name}`")
            lines.append("")

        if metadata.variables:
            lines.append("## Variaveis")
            lines.append("")
            lines.append("| Nome | Tipo | Default |")
            lines.append("|------|------|---------|")
            for name, info in metadata.variables.items():
                lines.append(f"| {name} | {info.get('type', '-')} | {info.get('default', '-')} |")
            lines.append("")

        if validation:
            lines.extend(self._build_validation_section(validation))

        lines.append("---")
        lines.append("")
        lines.append(f"Documento gerado automaticamente pelo QoL Alteryx-ODI Tools")

        return "\n".join(lines)

    def _build_validation_section(self, validation: ValidationResult) -> list[str]:
        """Constroi secao de validacao para documentacao."""
        lines: list[str] = []
        lines.append("## Validacao")
        lines.append("")

        status = "Aprovado" if validation.passed else "Reprovado"
        lines.append(f"**Status**: {status}")
        lines.append(f"- Erros: {validation.error_count}")
        lines.append(f"- Avisos: {validation.warning_count}")
        lines.append(f"- Info: {validation.info_count}")
        lines.append("")

        if validation.issues:
            lines.append("### Problemas Encontrados")
            lines.append("")
            for issue in validation.issues:
                severity_map = {"error": "ERRO", "warning": "AVISO", "info": "INFO"}
                sev = severity_map.get(issue.severity, issue.severity.upper())
                lines.append(f"- [{sev}] `{issue.code}`: {issue.message}")
            lines.append("")

        return lines


# "Documentar e explicar o que deveria ser obvio." - Desconhecido
