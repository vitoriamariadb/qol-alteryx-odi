"""
CLI Module
Interface de linha de comando com subcomandos para operacoes de parsing,
conversao, validacao e processamento em lote de workflows XML.
"""
import argparse
import json
import logging
from pathlib import Path

from src.core.logger import AppLogger, Verbosity

logger = logging.getLogger(__name__)

VERSION = "0.1.0"


def _build_parser() -> argparse.ArgumentParser:
    """Constroi o parser principal com todos os subcomandos."""
    parser = argparse.ArgumentParser(
        prog="qol-alteryx-odi",
        description="Ferramenta CLI para parsing e conversao de workflows Alteryx/ODI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Aumenta verbosidade (-v verbose, -vv debug)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcomandos disponiveis")

    _add_parse_command(subparsers)
    _add_convert_command(subparsers)
    _add_template_command(subparsers)
    _add_validate_command(subparsers)
    _add_batch_command(subparsers)

    return parser


def _add_parse_command(subparsers: argparse._SubParsersAction) -> None:
    """Adiciona subcomando parse."""
    cmd = subparsers.add_parser("parse", help="Parseia workflow ou package XML")
    cmd.add_argument("filepath", type=Path, help="Caminho do arquivo XML")
    cmd.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Formato de saida (padrao: text)",
    )


def _add_convert_command(subparsers: argparse._SubParsersAction) -> None:
    """Adiciona subcomando convert."""
    cmd = subparsers.add_parser("convert", help="Converte entre formatos Alteryx e ODI")
    cmd.add_argument("input", type=Path, help="Arquivo de entrada")
    cmd.add_argument("--output", type=Path, default=None, help="Arquivo de saida")
    cmd.add_argument(
        "--direction",
        choices=["a2o", "o2a"],
        required=True,
        help="Direcao da conversao: a2o (Alteryx->ODI) ou o2a (ODI->Alteryx)",
    )


def _add_template_command(subparsers: argparse._SubParsersAction) -> None:
    """Adiciona subcomando template."""
    cmd = subparsers.add_parser("template", help="Processa template com substituicao de datas")
    cmd.add_argument("filepath", type=Path, help="Caminho do template XML")
    cmd.add_argument("--month", type=int, required=True, help="Mes alvo (1-12)")
    cmd.add_argument("--year", type=int, required=True, help="Ano alvo (ex: 2025)")
    cmd.add_argument("--server", type=str, default="", help="String de conexao do servidor")


def _add_validate_command(subparsers: argparse._SubParsersAction) -> None:
    """Adiciona subcomando validate."""
    cmd = subparsers.add_parser("validate", help="Valida workflow ou package XML")
    cmd.add_argument("filepath", type=Path, help="Caminho do arquivo XML")
    cmd.add_argument(
        "--severity",
        choices=["error", "warning", "info"],
        default="warning",
        help="Nivel minimo de severidade para exibir (padrao: warning)",
    )


def _add_batch_command(subparsers: argparse._SubParsersAction) -> None:
    """Adiciona subcomando batch."""
    cmd = subparsers.add_parser("batch", help="Processamento em lote de diretorio")
    cmd.add_argument("input_dir", type=Path, help="Diretorio de entrada")
    cmd.add_argument("--output-dir", type=Path, default=None, help="Diretorio de saida")
    cmd.add_argument(
        "--operation",
        choices=["parse", "convert_a2o", "convert_o2a", "template"],
        default="parse",
        help="Operacao a executar (padrao: parse)",
    )
    cmd.add_argument("--recursive", action="store_true", help="Busca recursiva")


def _run_parse(args: argparse.Namespace) -> int:
    """Executa subcomando parse."""
    filepath = args.filepath
    suffix = filepath.suffix.lower()

    if suffix in {".yxmd", ".yxmc", ".yxwz"}:
        from src.core.alteryx_parser import AlteryxParser
        parser = AlteryxParser()
        workflow = parser.parse(filepath)
        data = {
            "name": workflow.name,
            "nodes": workflow.node_count,
            "connections": workflow.connection_count,
            "properties": workflow.properties,
        }
    else:
        from src.core.odi_parser import OdiParser
        parser = OdiParser()
        package = parser.parse(filepath)
        data = {
            "name": package.name,
            "steps": package.step_count,
            "scenarios": package.scenario_count,
            "description": package.description,
        }

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")

    return 0


def _run_convert(args: argparse.Namespace) -> int:
    """Executa subcomando convert."""
    input_path = args.input
    output_path = args.output

    if args.direction == "a2o":
        from src.core.converter import AlteryxToOdiConverter
        converter = AlteryxToOdiConverter()
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_odi.xml"
    else:
        from src.core.converter import OdiToAlteryxConverter
        converter = OdiToAlteryxConverter()
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_alteryx.yxmd"

    result = converter.convert(input_path, output_path)

    if result.success:
        logger.info("Conversao concluida: %s", output_path)
        print(f"Salvo em: {output_path}")
        for key, value in result.stats.items():
            print(f"  {key}: {value}")
    else:
        for err in result.errors:
            logger.error(err)
        return 1

    for warn in result.warnings:
        logger.warning(warn)

    return 0


def _run_template(args: argparse.Namespace) -> int:
    """Executa subcomando template."""
    from src.core.xml_processor import process_template, get_output_filename

    content, stats = process_template(
        args.filepath,
        args.server,
        args.year,
        args.month,
    )

    output_dir = args.filepath.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_base = get_output_filename(args.filepath.name)
    output_path = output_dir / f"{output_base}.yxmd"

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(content)

    print(f"Salvo em: {output_path}")
    print(f"Datas substituidas: {stats.get('dates', 0)}")
    print(f"Servidores substituidos: {stats.get('servers', 0)}")
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    """Executa subcomando validate."""
    filepath = args.filepath
    suffix = filepath.suffix.lower()
    severity_order = {"info": 0, "warning": 1, "error": 2}
    min_severity = severity_order.get(args.severity, 1)

    if suffix in {".yxmd", ".yxmc", ".yxwz"}:
        from src.core.validation import WorkflowValidator
        validator = WorkflowValidator()
    else:
        from src.core.validation import PackageValidator
        validator = PackageValidator()

    result = validator.validate(filepath)

    filtered = [
        issue for issue in result.issues
        if severity_order.get(issue.severity, 0) >= min_severity
    ]

    if not filtered:
        print(f"Validacao OK: {filepath.name}")
        return 0

    for issue in filtered:
        print(str(issue))

    print(f"\nResumo: {result.error_count} erros, {result.warning_count} avisos")
    return 1 if result.error_count > 0 else 0


def _run_batch(args: argparse.Namespace) -> int:
    """Executa subcomando batch."""
    from src.batch.processor import BatchProcessor, BatchConfig

    output_dir = args.output_dir or (args.input_dir / "output")

    config = BatchConfig(
        input_dir=args.input_dir,
        output_dir=output_dir,
        operation=args.operation,
        recursive=args.recursive,
    )

    processor = BatchProcessor()
    result = processor.process(config)

    print(f"Total: {result.total_files}")
    print(f"Processados: {result.processed}")
    print(f"Falhas: {result.failed}")
    print(f"Taxa de sucesso: {result.success_rate:.1f}%")

    return 1 if result.failed > 0 else 0


_COMMAND_MAP: dict[str, callable] = {
    "parse": _run_parse,
    "convert": _run_convert,
    "template": _run_template,
    "validate": _run_validate,
    "batch": _run_batch,
}


def run_cli() -> int:
    """Ponto de entrada principal do CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    verbosity_map = {0: Verbosity.NORMAL, 1: Verbosity.VERBOSE, 2: Verbosity.DEBUG}
    verbosity = verbosity_map.get(args.verbose, Verbosity.DEBUG)
    AppLogger.setup(verbosity=verbosity, log_dir=Path("logs"))

    if args.command is None:
        parser.print_help()
        return 0

    handler = _COMMAND_MAP.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except FileNotFoundError as exc:
        logger.error("Arquivo nao encontrado: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("Erro inesperado: %s", exc)
        return 1


# "A liberdade e o reconhecimento da necessidade." - Friedrich Engels
