"""
Search and Replace Dialog Module
Dialogo de busca e substituicao para conteudo XML em workflows.
Suporta texto simples e expressoes regulares.
"""
import logging
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

logger = logging.getLogger(__name__)

DRACULA_BG = "#282a36"
DRACULA_CURRENT = "#44475a"
DRACULA_FG = "#f8f8f2"
DRACULA_COMMENT = "#6272a4"
DRACULA_CYAN = "#8be9fd"
DRACULA_GREEN = "#50fa7b"
DRACULA_ORANGE = "#ffb86c"
DRACULA_PURPLE = "#bd93f9"
DRACULA_RED = "#ff5555"
DRACULA_YELLOW = "#f1fa8c"


class SearchReplaceDialog(tk.Toplevel):
    """Dialogo de busca e substituicao com suporte a regex."""

    def __init__(self, parent: tk.Tk, content: str = "") -> None:
        super().__init__(parent)

        self.title("Busca e Substituicao")
        self.geometry("600x500")
        self.configure(bg=DRACULA_BG)
        self.resizable(False, False)

        self._content = content
        self._original_content = content
        self._match_count = 0
        self._on_apply_callback: Optional[Callable[[str], None]] = None

        self._setup_ui()
        logger.info("Search/Replace aberto")

    def _setup_ui(self) -> None:
        """Configura os componentes da interface."""
        self._create_search_fields()
        self._create_options()
        self._create_buttons()
        self._create_preview()
        self._create_status()

    def _create_search_fields(self) -> None:
        """Cria campos de busca e substituicao."""
        fields_frame = tk.Frame(self, bg=DRACULA_BG)
        fields_frame.pack(fill="x", padx=20, pady=(20, 10))

        search_label = tk.Label(
            fields_frame,
            text="Buscar:",
            font=("Segoe UI", 11),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
        )
        search_label.pack(anchor="w")

        self.search_entry = tk.Entry(
            fields_frame,
            font=("Consolas", 11),
            bg=DRACULA_CURRENT,
            fg=DRACULA_FG,
            insertbackground=DRACULA_GREEN,
            relief="flat",
            highlightthickness=2,
            highlightbackground=DRACULA_COMMENT,
            highlightcolor=DRACULA_PURPLE,
        )
        self.search_entry.pack(fill="x", ipady=8, pady=(5, 10))

        replace_label = tk.Label(
            fields_frame,
            text="Substituir por:",
            font=("Segoe UI", 11),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
        )
        replace_label.pack(anchor="w")

        self.replace_entry = tk.Entry(
            fields_frame,
            font=("Consolas", 11),
            bg=DRACULA_CURRENT,
            fg=DRACULA_FG,
            insertbackground=DRACULA_GREEN,
            relief="flat",
            highlightthickness=2,
            highlightbackground=DRACULA_COMMENT,
            highlightcolor=DRACULA_PURPLE,
        )
        self.replace_entry.pack(fill="x", ipady=8, pady=(5, 0))

    def _create_options(self) -> None:
        """Cria opcoes de busca."""
        options_frame = tk.Frame(self, bg=DRACULA_BG)
        options_frame.pack(fill="x", padx=20, pady=10)

        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)

        case_cb = tk.Checkbutton(
            options_frame,
            text="Sensivel a maiusculas",
            variable=self.case_sensitive_var,
            font=("Segoe UI", 10),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
            selectcolor=DRACULA_CURRENT,
            activebackground=DRACULA_BG,
            activeforeground=DRACULA_FG,
        )
        case_cb.pack(side="left", padx=(0, 15))

        regex_cb = tk.Checkbutton(
            options_frame,
            text="Expressao regular",
            variable=self.regex_var,
            font=("Segoe UI", 10),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
            selectcolor=DRACULA_CURRENT,
            activebackground=DRACULA_BG,
            activeforeground=DRACULA_FG,
        )
        regex_cb.pack(side="left", padx=(0, 15))

        word_cb = tk.Checkbutton(
            options_frame,
            text="Palavra inteira",
            variable=self.whole_word_var,
            font=("Segoe UI", 10),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
            selectcolor=DRACULA_CURRENT,
            activebackground=DRACULA_BG,
            activeforeground=DRACULA_FG,
        )
        word_cb.pack(side="left")

    def _create_buttons(self) -> None:
        """Cria botoes de acao."""
        button_frame = tk.Frame(self, bg=DRACULA_BG)
        button_frame.pack(fill="x", padx=20, pady=10)

        find_btn = tk.Button(
            button_frame,
            text="Buscar",
            font=("Segoe UI", 10),
            bg=DRACULA_CYAN,
            fg=DRACULA_BG,
            activebackground=DRACULA_PURPLE,
            relief="flat",
            command=self._find,
            padx=15,
            pady=6,
        )
        find_btn.pack(side="left", padx=(0, 10))

        replace_btn = tk.Button(
            button_frame,
            text="Substituir Tudo",
            font=("Segoe UI", 10, "bold"),
            bg=DRACULA_GREEN,
            fg=DRACULA_BG,
            activebackground=DRACULA_CYAN,
            relief="flat",
            command=self._replace_all,
            padx=15,
            pady=6,
        )
        replace_btn.pack(side="left", padx=(0, 10))

        reset_btn = tk.Button(
            button_frame,
            text="Restaurar Original",
            font=("Segoe UI", 10),
            bg=DRACULA_ORANGE,
            fg=DRACULA_BG,
            activebackground=DRACULA_RED,
            relief="flat",
            command=self._reset,
            padx=15,
            pady=6,
        )
        reset_btn.pack(side="left", padx=(0, 10))

        apply_btn = tk.Button(
            button_frame,
            text="Aplicar",
            font=("Segoe UI", 10),
            bg=DRACULA_PURPLE,
            fg=DRACULA_FG,
            activebackground=DRACULA_CYAN,
            relief="flat",
            command=self._apply,
            padx=15,
            pady=6,
        )
        apply_btn.pack(side="right")

    def _create_preview(self) -> None:
        """Cria area de preview."""
        preview_frame = tk.Frame(self, bg=DRACULA_BG)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        preview_label = tk.Label(
            preview_frame,
            text="Preview:",
            font=("Segoe UI", 10),
            bg=DRACULA_BG,
            fg=DRACULA_COMMENT,
        )
        preview_label.pack(anchor="w", pady=(0, 5))

        self.preview_text = tk.Text(
            preview_frame,
            font=("Consolas", 9),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
            relief="flat",
            wrap="none",
            state="disabled",
            padx=8,
            pady=8,
            highlightthickness=1,
            highlightbackground=DRACULA_COMMENT,
        )
        self.preview_text.pack(fill="both", expand=True)

        self.preview_text.tag_configure("match", background=DRACULA_YELLOW, foreground=DRACULA_BG)
        self.preview_text.tag_configure("replaced", background=DRACULA_GREEN, foreground=DRACULA_BG)

    def _create_status(self) -> None:
        """Cria barra de status."""
        self.status_label = tk.Label(
            self,
            text="Pronto",
            font=("Segoe UI", 10),
            bg=DRACULA_CURRENT,
            fg=DRACULA_FG,
            anchor="w",
            padx=10,
            pady=5,
        )
        self.status_label.pack(fill="x", side="bottom")

    def _build_pattern(self, search_text: str) -> Optional[re.Pattern]:
        """Constroi o padrao de busca baseado nas opcoes."""
        if not search_text:
            return None

        flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE

        if self.regex_var.get():
            try:
                return re.compile(search_text, flags)
            except re.error as exc:
                self.status_label.configure(text=f"Regex invalido: {exc}")
                return None

        escaped = re.escape(search_text)
        if self.whole_word_var.get():
            escaped = rf"\b{escaped}\b"

        return re.compile(escaped, flags)

    def _find(self) -> None:
        """Executa busca e destaca ocorrencias no preview."""
        search_text = self.search_entry.get()
        pattern = self._build_pattern(search_text)

        if pattern is None:
            return

        matches = list(pattern.finditer(self._content))
        self._match_count = len(matches)

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)

        if self._match_count == 0:
            self.preview_text.insert("1.0", self._content[:2000])
            self.status_label.configure(text="Nenhuma ocorrencia encontrada")
        else:
            preview_content = self._content[:5000]
            self.preview_text.insert("1.0", preview_content)

            for match in pattern.finditer(preview_content):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.preview_text.tag_add("match", start_idx, end_idx)

            self.status_label.configure(
                text=f"{self._match_count} ocorrencia(s) encontrada(s)"
            )

        self.preview_text.configure(state="disabled")

    def _replace_all(self) -> None:
        """Executa substituicao em todo o conteudo."""
        search_text = self.search_entry.get()
        replace_text = self.replace_entry.get()
        pattern = self._build_pattern(search_text)

        if pattern is None:
            return

        new_content, count = pattern.subn(replace_text, self._content)
        self._content = new_content
        self._match_count = count

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", new_content[:5000])
        self.preview_text.configure(state="disabled")

        self.status_label.configure(
            text=f"{count} substituicao(oes) realizada(s)"
        )

        logger.info("Search/Replace: %d substituicoes", count)

    def _reset(self) -> None:
        """Restaura o conteudo original."""
        self._content = self._original_content
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", self._content[:5000])
        self.preview_text.configure(state="disabled")
        self.status_label.configure(text="Conteudo restaurado ao original")

    def _apply(self) -> None:
        """Aplica as alteracoes e fecha o dialogo."""
        if self._on_apply_callback:
            self._on_apply_callback(self._content)
        self.destroy()

    def set_content(self, content: str) -> None:
        """Define o conteudo a ser manipulado."""
        self._content = content
        self._original_content = content
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", content[:5000])
        self.preview_text.configure(state="disabled")

    def set_on_apply(self, callback: Callable[[str], None]) -> None:
        """Define callback chamado ao aplicar alteracoes."""
        self._on_apply_callback = callback


# "Buscar e a natureza do espirito." - Blaise Pascal

