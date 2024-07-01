#!/usr/bin/env python3
"""
QoL Alteryx-ODI Tools
Main entry point - Orchestrator
"""
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Ponto de entrada principal da aplicacao."""
    logger.info("QoL Alteryx-ODI Tools iniciando...")
    logger.info("Diretorio raiz: %s", ROOT_DIR)


if __name__ == "__main__":
    main()

# "O inicio e a parte mais importante do trabalho." - Platao
