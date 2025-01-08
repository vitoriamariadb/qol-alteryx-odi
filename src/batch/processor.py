"""
Batch Processor Module
Processamento em lote de multiplos arquivos XML de workflow.
Suporta workflows Alteryx e packages ODI simultaneamente.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from src.core.alteryx_parser import AlteryxParser
from src.core.odi_parser import OdiParser
from src.core.converter import AlteryxToOdiConverter, OdiToAlteryxConverter
from src.core.xml_processor import process_template

logger = logging.getLogger(__name__)

ALTERYX_EXTENSIONS = {".yxmd", ".yxmc", ".yxwz"}
ODI_EXTENSIONS = {".xml"}


@dataclass
class BatchResult:
    """Resultado do processamento em lote."""
    total_files: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.processed / self.total_files) * 100


@dataclass
class BatchConfig:
    """Configuracao para processamento em lote."""
    input_dir: Path
    output_dir: Path
    operation: str = "parse"
    recursive: bool = False
    file_pattern: str = "*.yxmd"
    target_year: int = 2024
    target_month: int = 1
    server: str = ""
    max_files: int = 0


class BatchProcessor:
    """Processador de arquivos em lote."""

    def __init__(self) -> None:
        self._alteryx_parser = AlteryxParser()
        self._odi_parser = OdiParser()
        self._a2o_converter = AlteryxToOdiConverter()
        self._o2a_converter = OdiToAlteryxConverter()

    def process(
        self,
        config: BatchConfig,
        progress_fn: Optional[Callable[[float], None]] = None,
        log_fn: Optional[Callable[[str, str], None]] = None,
    ) -> BatchResult:
        """Executa processamento em lote conforme configuracao."""
        result = BatchResult()

        files = self._collect_files(config)
        result.total_files = len(files)

        if result.total_files == 0:
            if log_fn:
                log_fn("Nenhum arquivo encontrado para processar", "warning")
            return result

        if log_fn:
            log_fn(f"Encontrados {result.total_files} arquivo(s)", "info")

        config.output_dir.mkdir(parents=True, exist_ok=True)

        for idx, filepath in enumerate(files):
            try:
                if log_fn:
                    log_fn(f"Processando [{idx + 1}/{result.total_files}]: {filepath.name}", "info")

                file_result = self._process_single(filepath, config, log_fn)
                result.results.append(file_result)
                result.processed += 1

            except Exception as exc:
                error_msg = f"Erro em {filepath.name}: {exc}"
                result.errors.append(error_msg)
                result.failed += 1
                if log_fn:
                    log_fn(error_msg, "error")
                logger.exception("Erro ao processar %s", filepath.name)

            if progress_fn:
                progress_fn((idx + 1) / result.total_files)

        if log_fn:
            log_fn(
                f"Lote concluido: {result.processed} ok, {result.failed} falhas, "
                f"{result.skipped} ignorados",
                "success" if result.failed == 0 else "warning",
            )

        return result

    def _collect_files(self, config: BatchConfig) -> list[Path]:
        """Coleta arquivos para processar baseado na configuracao."""
        if config.recursive:
            files = sorted(config.input_dir.rglob(config.file_pattern))
        else:
            files = sorted(config.input_dir.glob(config.file_pattern))

        if config.max_files > 0:
            files = files[: config.max_files]

        return files

    def _process_single(
        self,
        filepath: Path,
        config: BatchConfig,
        log_fn: Optional[Callable] = None,
    ) -> dict:
        """Processa um unico arquivo."""
        result_data: dict = {
            "filepath": str(filepath),
            "status": "ok",
            "operation": config.operation,
        }

        if config.operation == "parse":
            result_data.update(self._parse_file(filepath))

        elif config.operation == "convert_a2o":
            output_path = config.output_dir / f"{filepath.stem}_odi.xml"
            conv_result = self._a2o_converter.convert(filepath, output_path)
            result_data["output"] = str(output_path)
            result_data["stats"] = conv_result.stats
            result_data["warnings"] = conv_result.warnings

        elif config.operation == "convert_o2a":
            output_path = config.output_dir / f"{filepath.stem}_alteryx.yxmd"
            conv_result = self._o2a_converter.convert(filepath, output_path)
            result_data["output"] = str(output_path)
            result_data["stats"] = conv_result.stats

        elif config.operation == "template":
            content, stats = process_template(
                filepath,
                config.server,
                config.target_year,
                config.target_month,
                log_fn=log_fn,
            )
            output_path = config.output_dir / filepath.name
            with open(output_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
            result_data["output"] = str(output_path)
            result_data["stats"] = stats

        return result_data

    def _parse_file(self, filepath: Path) -> dict:
        """Parseia um arquivo e retorna metadados basicos."""
        suffix = filepath.suffix.lower()

        if suffix in ALTERYX_EXTENSIONS:
            workflow = self._alteryx_parser.parse(filepath)
            return {
                "type": "alteryx",
                "nodes": workflow.node_count,
                "connections": workflow.connection_count,
            }

        if suffix in ODI_EXTENSIONS:
            package = self._odi_parser.parse(filepath)
            return {
                "type": "odi",
                "steps": package.step_count,
                "scenarios": package.scenario_count,
            }

        return {"type": "unknown", "status": "skipped"}

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        operation: str = "parse",
        log_fn: Optional[Callable] = None,
    ) -> BatchResult:
        """Atalho para processar um diretorio inteiro."""
        config = BatchConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            operation=operation,
        )
        return self.process(config, log_fn=log_fn)


# "A perfeicao e alcancada nao quando nao ha mais nada a acrescentar, mas quando nao ha mais nada a retirar." - Saint-Exupery

