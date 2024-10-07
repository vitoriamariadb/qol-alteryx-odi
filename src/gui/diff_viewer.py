"""
Diff Viewer Module
Visualizador side-by-side de diferencas entre arquivos XML.
Compara workflows Alteryx ou packages ODI destacando alteracoes.
"""
import difflib
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Optional

logger = logging.getLogger(__name__)

DRACULA_BG = "#282a36"
DRACULA_CURRENT = "#44475a"
DRACULA_FG = "#f8f8f2"
DRACULA_COMMENT = "#6272a4"
DRACULA_CYAN = "#8be9fd"
DRACULA_GREEN = "#50fa7b"
DRACULA_ORANGE = "#ffb86c"
DRACULA_PINK = "#ff79c6"
DRACULA_PURPLE = "#bd93f9"
DRACULA_RED = "#ff5555"
DRACULA_YELLOW = "#f1fa8c"


class DiffViewer(tk.Toplevel):
    """Janela de visualizacao de diff entre dois arquivos XML."""

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)

        self.title("Diff Viewer - Comparacao XML")
        self.geometry("1200x700")
        self.configure(bg=DRACULA_BG)

        self._left_path: Optional[Path] = None
        self._right_path: Optional[Path] = None
        self._diff_lines: list[str] = []

        self._setup_ui()
        logger.info("Diff Viewer aberto")

    def _setup_ui(self) -> None:
        """Configura a interface do diff viewer."""
        self._create_toolbar()
        self._create_panels()
        self._create_status_bar()

    def _create_toolbar(self) -> None:
        """Cria barra de ferramentas superior."""
        toolbar = tk.Frame(self, bg=DRACULA_CURRENT, height=50)
        toolbar.pack(fill="x", padx=5, pady=5)

        left_btn = tk.Button(
            toolbar,
            text="Arquivo Esquerdo",
            font=("Segoe UI", 10),
            bg=DRACULA_COMMENT,
            fg=DRACULA_FG,
            activebackground=DRACULA_PURPLE,
            activeforeground=DRACULA_FG,
            relief="flat",
            command=self._select_left_file,
            padx=10,
            pady=5,
        )
        left_btn.pack(side="left", padx=5, pady=5)

        right_btn = tk.Button(
            toolbar,
            text="Arquivo Direito",
            font=("Segoe UI", 10),
            bg=DRACULA_COMMENT,
            fg=DRACULA_FG,
            activebackground=DRACULA_PURPLE,
            activeforeground=DRACULA_FG,
            relief="flat",
            command=self._select_right_file,
            padx=10,
            pady=5,
        )
        right_btn.pack(side="left", padx=5, pady=5)

        compare_btn = tk.Button(
            toolbar,
            text="Comparar",
            font=("Segoe UI", 10, "bold"),
            bg=DRACULA_GREEN,
            fg=DRACULA_BG,
            activebackground=DRACULA_CYAN,
            activeforeground=DRACULA_BG,
            relief="flat",
            command=self._run_comparison,
            padx=15,
            pady=5,
        )
        compare_btn.pack(side="left", padx=15, pady=5)

        self.left_label = tk.Label(
            toolbar,
            text="Nenhum arquivo",
            font=("Consolas", 9),
            bg=DRACULA_CURRENT,
            fg=DRACULA_COMMENT,
        )
        self.left_label.pack(side="left", padx=5)

        self.right_label = tk.Label(
            toolbar,
            text="Nenhum arquivo",
            font=("Consolas", 9),
            bg=DRACULA_CURRENT,
            fg=DRACULA_COMMENT,
        )
        self.right_label.pack(side="right", padx=5)

    def _create_panels(self) -> None:
        """Cria paineis side-by-side para visualizacao."""
        panels_frame = tk.Frame(self, bg=DRACULA_BG)
        panels_frame.pack(fill="both", expand=True, padx=5, pady=5)

        left_frame = tk.Frame(panels_frame, bg=DRACULA_BG)
        left_frame.pack(side="left", fill="both", expand=True)

        left_header = tk.Label(
            left_frame,
            text="Original",
            font=("Segoe UI", 11, "bold"),
            bg=DRACULA_BG,
            fg=DRACULA_CYAN,
        )
        left_header.pack(anchor="w", padx=5)

        self.left_text = tk.Text(
            left_frame,
            font=("Consolas", 9),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
            insertbackground=DRACULA_FG,
            relief="flat",
            wrap="none",
            padx=8,
            pady=8,
        )
        self.left_text.pack(fill="both", expand=True, padx=2)

        separator = tk.Frame(panels_frame, bg=DRACULA_COMMENT, width=2)
        separator.pack(side="left", fill="y", padx=2)

        right_frame = tk.Frame(panels_frame, bg=DRACULA_BG)
        right_frame.pack(side="right", fill="both", expand=True)

        right_header = tk.Label(
            right_frame,
            text="Modificado",
            font=("Segoe UI", 11, "bold"),
            bg=DRACULA_BG,
            fg=DRACULA_PINK,
        )
        right_header.pack(anchor="w", padx=5)

        self.right_text = tk.Text(
            right_frame,
            font=("Consolas", 9),
            bg=DRACULA_BG,
            fg=DRACULA_FG,
            insertbackground=DRACULA_FG,
            relief="flat",
            wrap="none",
            padx=8,
            pady=8,
        )
        self.right_text.pack(fill="both", expand=True, padx=2)

        self.left_text.tag_configure("added", background="#1a3a1a", foreground=DRACULA_GREEN)
        self.left_text.tag_configure("removed", background="#3a1a1a", foreground=DRACULA_RED)
        self.left_text.tag_configure("changed", background="#3a3a1a", foreground=DRACULA_YELLOW)

        self.right_text.tag_configure("added", background="#1a3a1a", foreground=DRACULA_GREEN)
        self.right_text.tag_configure("removed", background="#3a1a1a", foreground=DRACULA_RED)
        self.right_text.tag_configure("changed", background="#3a3a1a", foreground=DRACULA_YELLOW)

        left_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.left_text.yview)
        right_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.right_text.yview)

        self.left_text.configure(yscrollcommand=self._sync_scroll)
        self.right_text.configure(yscrollcommand=self._sync_scroll)

    def _create_status_bar(self) -> None:
        """Cria barra de status inferior."""
        self.status_bar = tk.Label(
            self,
            text="Selecione dois arquivos para comparar",
            font=("Segoe UI", 10),
            bg=DRACULA_CURRENT,
            fg=DRACULA_FG,
            anchor="w",
            padx=10,
            pady=5,
        )
        self.status_bar.pack(fill="x", side="bottom")

    def _sync_scroll(self, *args) -> None:
        """Sincroniza scroll entre os dois paineis."""
        self.left_text.yview_moveto(args[0])
        self.right_text.yview_moveto(args[0])

    def _select_left_file(self) -> None:
        """Seleciona arquivo para o painel esquerdo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo original",
            filetypes=[("XML/YXMD", "*.xml *.yxmd"), ("Todos", "*.*")],
        )
        if filepath:
            self._left_path = Path(filepath)
            self.left_label.configure(text=self._left_path.name)

    def _select_right_file(self) -> None:
        """Seleciona arquivo para o painel direito."""
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo modificado",
            filetypes=[("XML/YXMD", "*.xml *.yxmd"), ("Todos", "*.*")],
        )
        if filepath:
            self._right_path = Path(filepath)
            self.right_label.configure(text=self._right_path.name)

    def _run_comparison(self) -> None:
        """Executa a comparacao entre os dois arquivos."""
        if not self._left_path or not self._right_path:
            self.status_bar.configure(text="Selecione ambos os arquivos primeiro")
            return

        try:
            with open(self._left_path, "r", encoding="utf-8") as f:
                left_lines = f.readlines()

            with open(self._right_path, "r", encoding="utf-8") as f:
                right_lines = f.readlines()

        except Exception as exc:
            self.status_bar.configure(text=f"Erro ao ler arquivos: {exc}")
            return

        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        differ = difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=self._left_path.name,
            tofile=self._right_path.name,
            lineterm="",
        )

        added_count = 0
        removed_count = 0
        changed_count = 0

        for left_line in left_lines:
            self.left_text.insert(tk.END, left_line)

        for right_line in right_lines:
            self.right_text.insert(tk.END, right_line)

        diff_result = list(difflib.ndiff(left_lines, right_lines))
        line_left = 1
        line_right = 1

        for diff_line in diff_result:
            if diff_line.startswith("- "):
                self.left_text.tag_add(
                    "removed",
                    f"{line_left}.0",
                    f"{line_left}.end",
                )
                removed_count += 1
                line_left += 1
            elif diff_line.startswith("+ "):
                self.right_text.tag_add(
                    "added",
                    f"{line_right}.0",
                    f"{line_right}.end",
                )
                added_count += 1
                line_right += 1
            elif diff_line.startswith("  "):
                line_left += 1
                line_right += 1
            elif diff_line.startswith("? "):
                changed_count += 1

        self.status_bar.configure(
            text=f"Comparacao concluida: +{added_count} adicionadas, "
            f"-{removed_count} removidas, ~{changed_count} modificadas"
        )

        logger.info(
            "Diff: %s vs %s - +%d -%d ~%d",
            self._left_path.name,
            self._right_path.name,
            added_count,
            removed_count,
            changed_count,
        )

    def compare_strings(self, left_content: str, right_content: str, left_name: str = "A", right_name: str = "B") -> None:
        """Compara dois conteudos XML diretamente como strings."""
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        self.left_text.insert("1.0", left_content)
        self.right_text.insert("1.0", right_content)

        self.left_label.configure(text=left_name)
        self.right_label.configure(text=right_name)


# "A diferenca entre o quase certo e o certo e enorme." - Nassim Taleb
