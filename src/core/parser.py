"""
Parser Utilities Module
Cache centralizado de regex compiladas para otimizar parsing de XML.
Evita recompilacao repetida de padroes frequentes.
"""
import re
from typing import ClassVar


DATE_PATTERNS: dict[str, str] = {
    "YYYY_MM_DD": r"\d{4}-\d{2}-\d{2}",
    "YYYY_MM": r"\d{4}-\d{2}(?!-\d)",
    "DD_MM_YYYY": r"\d{2}/\d{2}/\d{4}",
    "MM_YYYY_SLASH": r"(?<!\d)(\d{2})/(\d{4})(?!\d)",
    "MM_YYYY_DASH": r"(?<!\d)(\d{2})-(\d{4})(?!\d)",
}


class RegexCache:
    """Cache singleton de regex compiladas para reuso entre modulos."""

    _instance: ClassVar["RegexCache | None"] = None
    _cache: dict[str, re.Pattern]
    _initialized: bool

    def __new__(cls) -> "RegexCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._precompile_date_patterns()
        self._initialized = True

    def _precompile_date_patterns(self) -> None:
        """Pre-compila todos os padroes de data conhecidos."""
        for key, pattern in DATE_PATTERNS.items():
            self._cache[key] = re.compile(pattern)

    def get_compiled(self, pattern_key: str) -> re.Pattern:
        """Retorna regex compilada por chave de padrao."""
        compiled = self._cache.get(pattern_key)
        if compiled is None:
            raise KeyError(f"Padrao nao encontrado no cache: {pattern_key}")
        return compiled

    def compile_and_cache(
        self,
        key: str,
        pattern: str,
        flags: int = 0,
    ) -> re.Pattern:
        """Compila e armazena um padrao customizado no cache."""
        if key not in self._cache:
            self._cache[key] = re.compile(pattern, flags)
        return self._cache[key]

    def has_pattern(self, key: str) -> bool:
        """Verifica se um padrao existe no cache."""
        return key in self._cache

    def clear_cache(self) -> None:
        """Limpa todo o cache e reinicializa padroes de data."""
        self._cache.clear()
        self._precompile_date_patterns()

    def pattern_count(self) -> int:
        """Retorna quantidade de padroes no cache."""
        return len(self._cache)

    @classmethod
    def reset(cls) -> None:
        """Reseta o singleton para estado inicial."""
        if cls._instance is not None:
            cls._instance._cache.clear()
            cls._instance._initialized = False
            cls._instance = None


# "O tempo e o recurso mais escasso e, se nao for gerenciado, nada mais pode ser gerenciado." - Peter Drucker
