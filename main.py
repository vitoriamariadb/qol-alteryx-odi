#!/usr/bin/env python3
"""
QoL Alteryx-ODI Tools
Main entry point - Orchestrator
"""
from pathlib import Path

from src.cli import run_cli
from src.core.logger import AppLogger
from src.core.xml_processor import process_template, get_output_filename
from src.gui.main_window import MainWindow

ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / "output"

AppLogger.setup(log_dir=ROOT_DIR / "logs")
logger = AppLogger.get_logger(__name__)


def main() -> None:
    """Ponto de entrada principal da aplicacao."""
    app = MainWindow()

    def on_execute(filepath: str, operation: str) -> None:
        """Trata a execucao de operacoes."""
        app.set_button_state(False)
        app.set_progress(0)

        try:
            input_path = Path(filepath)

            if not input_path.exists():
                app.log(f"ERRO: Arquivo nao encontrado: {filepath}", "error")
                return

            if "Processar Template" in operation:
                _process_template_operation(app, input_path)
            elif "Parsear Workflow" in operation:
                _parse_alteryx_operation(app, input_path)
            elif "Parsear Package" in operation:
                _parse_odi_operation(app, input_path)
            elif "Converter Alteryx" in operation:
                _convert_alteryx_to_odi(app, input_path)
            elif "Converter ODI" in operation:
                _convert_odi_to_alteryx(app, input_path)
            else:
                app.log(f"Operacao: {operation}", "info")

            app.set_progress(1.0)
            app.log("Operacao concluida", "success")

        except Exception as exc:
            app.log(f"ERRO: {exc}", "error")
            logger.exception("Erro durante execucao")

        finally:
            app.set_button_state(True)

    app.set_on_generate(on_execute)
    app.mainloop()


def _process_template_operation(app: MainWindow, input_path: Path) -> None:
    """Processa um template XML com substituicao de datas e servidor."""
    year, month = app.get_month_year()
    server = app.server_entry.get().strip()

    app.log(f"Processando template: {input_path.name}")
    app.log(f"Periodo: {month:02d}/{year}")

    content, stats = process_template(
        input_path, server, year, month, log_fn=app.log
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_base = get_output_filename(input_path.name)
    output_path = OUTPUT_DIR / f"{output_base}.yxmd"

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(content)

    app.log(f"Salvo em: {output_path}", "success")
    app.log(
        f"Resumo: {stats.get('dates', 0)} datas, {stats.get('servers', 0)} servidores",
        "info",
    )


def _parse_alteryx_operation(app: MainWindow, input_path: Path) -> None:
    """Parseia e exibe metadados de um workflow Alteryx."""
    from src.core.alteryx_parser import AlteryxParser

    parser = AlteryxParser()
    workflow = parser.parse(input_path)

    app.log(f"Workflow: {workflow.name}", "info")
    app.log(f"Nodes: {workflow.node_count}", "info")
    app.log(f"Conexoes: {workflow.connection_count}", "info")

    for key, value in workflow.properties.items():
        app.log(f"  {key}: {value}")


def _parse_odi_operation(app: MainWindow, input_path: Path) -> None:
    """Parseia e exibe metadados de um package ODI."""
    from src.core.odi_parser import OdiParser

    parser = OdiParser()
    package = parser.parse(input_path)

    app.log(f"Package: {package.name}", "info")
    app.log(f"Steps: {package.step_count}", "info")
    app.log(f"Cenarios: {package.scenario_count}", "info")


def _convert_alteryx_to_odi(app: MainWindow, input_path: Path) -> None:
    """Converte workflow Alteryx para ODI."""
    from src.core.converter import AlteryxToOdiConverter

    converter = AlteryxToOdiConverter()
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{input_path.stem}_odi.xml"

    result = converter.convert(input_path, output_path)

    if result.success:
        app.log(f"Convertido: {output_path}", "success")
        app.log(f"Stats: {result.stats}", "info")
    for warn in result.warnings:
        app.log(f"AVISO: {warn}", "warning")
    for err in result.errors:
        app.log(f"ERRO: {err}", "error")


def _convert_odi_to_alteryx(app: MainWindow, input_path: Path) -> None:
    """Converte package ODI para Alteryx."""
    from src.core.converter import OdiToAlteryxConverter

    converter = OdiToAlteryxConverter()
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{input_path.stem}_alteryx.yxmd"

    result = converter.convert(input_path, output_path)

    if result.success:
        app.log(f"Convertido: {output_path}", "success")
        app.log(f"Stats: {result.stats}", "info")
    for warn in result.warnings:
        app.log(f"AVISO: {warn}", "warning")
    for err in result.errors:
        app.log(f"ERRO: {err}", "error")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--gui"):
        sys.exit(run_cli())
    else:
        main()


# "O inicio e a parte mais importante do trabalho." - Platao
