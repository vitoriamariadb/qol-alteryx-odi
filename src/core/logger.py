"""
Logger Module
Logger rotacionado com niveis de verbosidade e saida colorida.
Singleton para uso centralizado em toda a aplicacao.
"""
import logging
import logging.handlers
from enum import IntEnum
from pathlib import Path
from typing import ClassVar


class Verbosity(IntEnum):
    """Niveis de verbosidade da aplicacao."""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


_VERBOSITY_TO_LEVEL: dict[Verbosity, int] = {
    Verbosity.QUIET: logging.WARNING,
    Verbosity.NORMAL: logging.INFO,
    Verbosity.VERBOSE: logging.DEBUG,
    Verbosity.DEBUG: logging.DEBUG,
}

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[1;31m",
}
_RESET = "\033[0m"

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3


class ColoredFormatter(logging.Formatter):
    """Formatter com cores ANSI para saida no console."""

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        message = super().format(record)
        if color:
            return f"{color}{message}{_RESET}"
        return message


class AppLogger:
    """Logger centralizado com singleton pattern."""

    _instance: ClassVar["AppLogger | None"] = None
    _initialized: bool = False
    _root_logger: logging.Logger
    _verbosity: Verbosity

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._root_logger = logging.getLogger("qol")
        self._verbosity = Verbosity.NORMAL
        self._initialized = True

    @classmethod
    def setup(
        cls,
        verbosity: Verbosity = Verbosity.NORMAL,
        log_dir: Path | None = None,
    ) -> None:
        """Configura handlers de arquivo e console."""
        instance = cls()
        instance._verbosity = verbosity
        level = _VERBOSITY_TO_LEVEL.get(verbosity, logging.INFO)

        instance._root_logger.setLevel(logging.DEBUG)
        instance._root_logger.handlers.clear()

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(ColoredFormatter(LOG_FORMAT))
        instance._root_logger.addHandler(console_handler)

        if log_dir is not None:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "app.log"

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            instance._root_logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Retorna um child logger com o nome especificado."""
        instance = cls()
        return instance._root_logger.getChild(name)

    @classmethod
    def set_verbosity(cls, verbosity: Verbosity) -> None:
        """Altera o nivel de verbosidade em tempo de execucao."""
        instance = cls()
        instance._verbosity = verbosity
        level = _VERBOSITY_TO_LEVEL.get(verbosity, logging.INFO)
        for handler in instance._root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.handlers.RotatingFileHandler
            ):
                handler.setLevel(level)

    @classmethod
    def get_verbosity(cls) -> Verbosity:
        """Retorna o nivel de verbosidade atual."""
        instance = cls()
        return instance._verbosity

    @classmethod
    def reset(cls) -> None:
        """Reseta o logger para estado inicial."""
        if cls._instance is not None:
            cls._instance._root_logger.handlers.clear()
            cls._instance._initialized = False
            cls._instance = None


# "Quem controla o passado controla o futuro; quem controla o presente controla o passado." - George Orwell
