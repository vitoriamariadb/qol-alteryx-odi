"""
Auto Update Module
Verificacao de atualizacoes e comparacao de versoes.
Suporta repositorios Git e endpoints HTTP para distribuicao de releases.
"""
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)

CURRENT_VERSION = "1.0.0"
VERSION_FILE = "version.json"
UPDATE_CHECK_URL = ""


@dataclass
class VersionInfo:
    """Informacoes de uma versao."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __gt__(self, other: "VersionInfo") -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __ge__(self, other: "VersionInfo") -> bool:
        return self == other or self > other


@dataclass
class UpdateCheckResult:
    """Resultado da verificacao de atualizacao."""
    update_available: bool
    current_version: str
    latest_version: str = ""
    download_url: str = ""
    changelog: str = ""
    error: str = ""


def parse_version(version_str: str) -> VersionInfo:
    """Parseia uma string de versao no formato semver."""
    version_str = version_str.strip().lstrip("v")
    parts = version_str.split(".")

    if len(parts) != 3:
        raise ValueError(f"Formato de versao invalido: {version_str}")

    try:
        return VersionInfo(
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2]),
        )
    except ValueError as exc:
        raise ValueError(f"Componente de versao nao numerico: {version_str}") from exc


def compare_versions(current: str, latest: str) -> int:
    """
    Compara duas versoes.
    Retorna: -1 se current < latest, 0 se iguais, 1 se current > latest.
    """
    current_v = parse_version(current)
    latest_v = parse_version(latest)

    if current_v > latest_v:
        return 1
    if latest_v > current_v:
        return -1
    return 0


class AutoUpdater:
    """Gerenciador de atualizacoes automaticas."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or Path(__file__).parent.parent.parent
        self._current_version = self._load_current_version()

    def _load_current_version(self) -> str:
        """Carrega a versao atual do projeto."""
        version_path = self._root_dir / VERSION_FILE
        if version_path.exists():
            try:
                with open(version_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("version", CURRENT_VERSION)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Erro ao ler version.json: %s", exc)
        return CURRENT_VERSION

    def check_for_updates(self, url: str = "") -> UpdateCheckResult:
        """Verifica se ha atualizacoes disponiveis."""
        check_url = url or UPDATE_CHECK_URL
        result = UpdateCheckResult(
            update_available=False,
            current_version=self._current_version,
        )

        if not check_url:
            result.error = "URL de verificacao nao configurada"
            logger.info("Verificacao de atualizacao ignorada: URL nao configurada")
            return result

        try:
            req = Request(check_url, headers={"User-Agent": "QoL-Alteryx-ODI-Updater/1.0"})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            latest_version = data.get("version", "")
            if not latest_version:
                result.error = "Resposta sem campo 'version'"
                return result

            result.latest_version = latest_version
            result.download_url = data.get("download_url", "")
            result.changelog = data.get("changelog", "")

            comparison = compare_versions(self._current_version, latest_version)
            result.update_available = comparison < 0

            if result.update_available:
                logger.info(
                    "Atualizacao disponivel: %s -> %s",
                    self._current_version,
                    latest_version,
                )
            else:
                logger.info("Versao atual (%s) esta atualizada", self._current_version)

        except URLError as exc:
            result.error = f"Erro de conexao: {exc.reason}"
            logger.warning("Falha ao verificar atualizacoes: %s", exc.reason)

        except json.JSONDecodeError as exc:
            result.error = f"Resposta invalida: {exc}"
            logger.warning("Resposta JSON invalida do servidor de atualizacao")

        except Exception as exc:
            result.error = f"Erro inesperado: {exc}"
            logger.exception("Erro ao verificar atualizacoes")

        return result

    def check_git_updates(self) -> UpdateCheckResult:
        """Verifica atualizacoes via git (para desenvolvimento)."""
        result = UpdateCheckResult(
            update_available=False,
            current_version=self._current_version,
        )

        try:
            fetch_result = subprocess.run(
                ["git", "fetch", "--dry-run"],
                cwd=str(self._root_dir),
                capture_output=True,
                text=True,
                timeout=15,
            )

            if fetch_result.returncode != 0:
                result.error = "Repositorio git nao encontrado ou sem remote"
                return result

            status_result = subprocess.run(
                ["git", "status", "-uno", "--porcelain"],
                cwd=str(self._root_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )

            log_result = subprocess.run(
                ["git", "log", "HEAD..origin/main", "--oneline"],
                cwd=str(self._root_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if log_result.stdout.strip():
                result.update_available = True
                result.changelog = log_result.stdout.strip()
                commits = log_result.stdout.strip().split("\n")
                result.latest_version = f"{self._current_version}+{len(commits)}"

                logger.info("Atualizacoes git disponiveis: %d commits", len(commits))

        except subprocess.TimeoutExpired:
            result.error = "Timeout ao verificar repositorio git"
            logger.warning("Timeout ao verificar git updates")

        except FileNotFoundError:
            result.error = "Git nao encontrado no sistema"
            logger.warning("Git nao instalado")

        return result

    def save_version(self, version: str) -> None:
        """Salva a versao atual no version.json."""
        version_path = self._root_dir / VERSION_FILE
        data = {
            "version": version,
            "project": "QoL-Alteryx-ODI",
        }
        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Versao salva: %s", version)

    @property
    def current_version(self) -> str:
        return self._current_version


# "Nao tenha medo de melhorar lentamente, tenha medo de ficar parado." - Proverbio chines
