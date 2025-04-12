"""
Main Window Module
Interface grafica principal para QoL Alteryx-ODI Tools.
Tema Dracula com logging aprimorado.
"""
import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from src.core.logger import AppLogger

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

PLACEHOLDER_TEXT = "Ex: caminho/para/arquivo.yxmd"
PLACEHOLDER_COLOR = DRACULA_COMMENT
NORMAL_COLOR = DRACULA_FG


class MainWindow(tk.Tk):
    """Janela principal da aplicacao QoL Alteryx-ODI Tools."""

    def __init__(self) -> None:
        super().__init__()

        self.title("QoL Alteryx-ODI Tools")
        self.geometry("900x800")
        self.resizable(False, False)
        self.configure(bg=DRACULA_BG)

        self._on_generate_callback: Optional[Callable] = None
        self._on_convert_callback: Optional[Callable] = None
        self._placeholder_active = True
        self._log_messages: list[str] = []

        self._setup_logs_folder()
        AppLogger.setup(log_dir=self.logs_dir)
        self._setup_styles()
        self._setup_ui()
        logger.info("Interface inicializada")

    def _setup_logs_folder(self) -> None:
        """Cria pasta de logs no diretorio raiz."""
        self.logs_dir = Path(__file__).parent.parent.parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def _setup_styles(self) -> None:
        """Configura estilos ttk para tema Dracula."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("Dark.TFrame", background=DRACULA_BG)
        self.style.configure("Card.TFrame", background=DRACULA_CURRENT)

        self.style.configure(
            "Dark.TLabel",
            background=DRACULA_BG,
            foreground=DRACULA_FG,
            font=("Segoe UI", 12),
        )

        self.style.configure(
            "Card.TLabel",
            background=DRACULA_CURRENT,
            foreground=DRACULA_FG,
            font=("Segoe UI", 12),
        )

        self.style.configure(
            "Title.TLabel",
            background=DRACULA_BG,
            foreground=DRACULA_PURPLE,
            font=("Segoe UI", 24, "bold"),
        )

        self.style.configure(
            "Subtitle.TLabel",
            background=DRACULA_BG,
            foreground=DRACULA_CYAN,
            font=("Segoe UI", 13),
        )

        self.style.configure(
            "TCombobox",
            font=("Segoe UI", 12),
            padding=10,
            arrowsize=20,
        )

        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", DRACULA_CURRENT)],
            foreground=[("readonly", DRACULA_FG)],
            background=[("readonly", DRACULA_CURRENT)],
            selectbackground=[("readonly", DRACULA_PURPLE)],
            selectforeground=[("readonly", DRACULA_FG)],
        )

        self.option_add("*TCombobox*Listbox.background", DRACULA_CURRENT)
        self.option_add("*TCombobox*Listbox.foreground", DRACULA_FG)
        self.option_add("*TCombobox*Listbox.selectBackground", DRACULA_PURPLE)
        self.option_add("*TCombobox*Listbox.selectForeground", DRACULA_FG)
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 11))

        self.style.configure(
            "TProgressbar",
            troughcolor=DRACULA_CURRENT,
            background=DRACULA_GREEN,
            thickness=12,
        )

    def _setup_ui(self) -> None:
        """Configura todos os componentes da interface."""
        self._create_header()
        self._create_operation_selector()
        self._create_file_input()
        self._create_options_frame()
        self._create_action_buttons()
        self._create_log_area()
        self._create_progress_bar()

    def _create_header(self) -> None:
        """Cria o cabecalho com estilo Dracula."""
        header_frame = ttk.Frame(self, style="Dark.TFrame")
        header_frame.pack(fill="x", padx=30, pady=(30, 15))

        title_label = ttk.Label(
            header_frame,
            text="QoL Alteryx-ODI Tools",
            style="Title.TLabel",
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            header_frame,
            text="Parser, Converter e Validador de Workflows XML",
            style="Subtitle.TLabel",
        )
        subtitle_label.pack(pady=(6, 0))

    def _create_operation_selector(self) -> None:
        """Cria o seletor de operacao."""
        selector_frame = ttk.Frame(self, style="Dark.TFrame")
        selector_frame.pack(fill="x", padx=30, pady=10)

        label = ttk.Label(
            selector_frame,
            text="Operacao:",
            style="Dark.TLabel",
        )
        label.pack(anchor="w")

        operations = [
            "Parsear Workflow Alteryx",
            "Parsear Package ODI",
            "Converter Alteryx -> ODI",
            "Converter ODI -> Alteryx",
            "Processar Template XML",
            "Validar Workflow",
        ]

        self.operation_var = tk.StringVar(value=operations[0])
        self.operation_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.operation_var,
            values=operations,
            state="readonly",
            width=50,
            font=("Segoe UI", 12),
        )
        self.operation_combo.pack(anchor="w", pady=(8, 0), ipady=8)

    def _create_file_input(self) -> None:
        """Cria o campo de entrada de arquivo com placeholder."""
        file_frame = ttk.Frame(self, style="Dark.TFrame")
        file_frame.pack(fill="x", padx=30, pady=10)

        label = ttk.Label(
            file_frame,
            text="Arquivo de Entrada:",
            style="Dark.TLabel",
        )
        label.pack(anchor="w")

        input_row = ttk.Frame(file_frame, style="Dark.TFrame")
        input_row.pack(fill="x", pady=(8, 0))

        self.file_entry = tk.Entry(
            input_row,
            font=("Consolas", 12),
            bg=DRACULA_CURRENT,
            fg=PLACEHOLDER_COLOR,
            insertbackground=DRACULA_GREEN,
            relief="flat",
            highlightthickness=2,
            highlightbackground=DRACULA_COMMENT,
            highlightcolor=DRACULA_PURPLE,
            bd=0,
        )
        self.file_entry.pack(fill="x", side="left", expand=True, ipady=12)

        self.file_entry.insert(0, PLACEHOLDER_TEXT)
        self._placeholder_active = True

        self.file_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.file_entry.bind("<FocusOut>", self._on_entry_focus_out)

        browse_btn = tk.Button(
            input_row,
            text="Procurar",
            font=("Segoe UI", 11),
            bg=DRACULA_COMMENT,
            fg=DRACULA_FG,
            activebackground=DRACULA_PURPLE,
            activeforeground=DRACULA_FG,
            relief="flat",
            cursor="hand2",
            command=self._browse_file,
            padx=15,
            pady=8,
            bd=0,
        )
        browse_btn.pack(side="right", padx=(10, 0))

    def _create_options_frame(self) -> None:
        """Cria frame de opcoes adicionais."""
        options_frame = ttk.Frame(self, style="Dark.TFrame")
        options_frame.pack(fill="x", padx=30, pady=10)

        label = ttk.Label(
            options_frame,
            text="Mes/Ano (para processamento de template):",
            style="Dark.TLabel",
        )
        label.pack(anchor="w")

        options_row = ttk.Frame(options_frame, style="Dark.TFrame")
        options_row.pack(fill="x", pady=(8, 0))

        month_options = self._generate_month_options()
        current_year = datetime.now().year
        current_month = datetime.now().month
        default_value = f"{current_month:02d}/{current_year}"

        self.month_var = tk.StringVar(value=default_value)
        self.month_combo = ttk.Combobox(
            options_row,
            textvariable=self.month_var,
            values=month_options,
            state="readonly",
            width=15,
            font=("Segoe UI", 12),
        )
        self.month_combo.pack(side="left", ipady=8)

        if default_value in month_options:
            self.month_combo.current(month_options.index(default_value))

        server_label = ttk.Label(
            options_row,
            text="  Servidor:",
            style="Dark.TLabel",
        )
        server_label.pack(side="left", padx=(20, 5))

        self.server_entry = tk.Entry(
            options_row,
            font=("Consolas", 12),
            bg=DRACULA_CURRENT,
            fg=DRACULA_FG,
            insertbackground=DRACULA_GREEN,
            relief="flat",
            highlightthickness=2,
            highlightbackground=DRACULA_COMMENT,
            highlightcolor=DRACULA_PURPLE,
            bd=0,
            width=35,
        )
        self.server_entry.pack(side="left", ipady=8)

    def _generate_month_options(self) -> list[str]:
        """Gera lista de opcoes MM/YYYY de Jan 2022 ate Dez do proximo ano."""
        options: list[str] = []
        current_year = datetime.now().year
        end_year = current_year + 1
        for year in range(2022, end_year + 1):
            for month in range(1, 13):
                options.append(f"{month:02d}/{year}")
        return options

    def _create_action_buttons(self) -> None:
        """Cria os botoes de acao."""
        button_frame = ttk.Frame(self, style="Dark.TFrame")
        button_frame.pack(fill="x", padx=30, pady=20)

        self.execute_btn = tk.Button(
            button_frame,
            text="Executar",
            font=("Segoe UI", 13, "bold"),
            bg=DRACULA_GREEN,
            fg=DRACULA_BG,
            activebackground=DRACULA_CYAN,
            activeforeground=DRACULA_BG,
            relief="flat",
            cursor="hand2",
            command=self._on_execute_click,
            padx=40,
            pady=12,
            bd=0,
        )
        self.execute_btn.pack(side="left")

        self.execute_btn.bind("<Enter>", lambda e: self.execute_btn.configure(bg=DRACULA_CYAN))
        self.execute_btn.bind("<Leave>", lambda e: self.execute_btn.configure(bg=DRACULA_GREEN))

        self.clear_btn = tk.Button(
            button_frame,
            text="Limpar Log",
            font=("Segoe UI", 11),
            bg=DRACULA_COMMENT,
            fg=DRACULA_FG,
            activebackground=DRACULA_RED,
            activeforeground=DRACULA_FG,
            relief="flat",
            cursor="hand2",
            command=self._clear_log,
            padx=20,
            pady=10,
            bd=0,
        )
        self.clear_btn.pack(side="right")

    def _create_log_area(self) -> None:
        """Cria a area de log/output com estilo Dracula."""
        log_frame = ttk.Frame(self, style="Dark.TFrame")
        log_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        log_label = ttk.Label(
            log_frame,
            text="Log de Operacoes:",
            style="Dark.TLabel",
        )
        log_label.pack(anchor="w", pady=(0, 6))

        text_frame = tk.Frame(
            log_frame,
            bg=DRACULA_BG,
            highlightthickness=2,
            highlightbackground=DRACULA_COMMENT,
            highlightcolor=DRACULA_COMMENT,
        )
        text_frame.pack(fill="both", expand=True)

        self.log_textbox = tk.Text(
            text_frame,
            height=12,
            font=("Consolas", 10),
            bg=DRACULA_BG,
            fg=DRACULA_GREEN,
            insertbackground=DRACULA_FG,
            relief="flat",
            state="disabled",
            wrap="word",
            padx=12,
            pady=12,
        )
        self.log_textbox.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.log_textbox.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.log_textbox.configure(yscrollcommand=scrollbar.set)

        self.log_textbox.tag_configure("error", foreground=DRACULA_RED)
        self.log_textbox.tag_configure("warning", foreground=DRACULA_ORANGE)
        self.log_textbox.tag_configure("success", foreground=DRACULA_GREEN)
        self.log_textbox.tag_configure("info", foreground=DRACULA_CYAN)

        self.log_textbox.bind("<Control-a>", self._select_all_log)
        self.log_textbox.bind("<Control-A>", self._select_all_log)
        self.log_textbox.bind("<Control-c>", self._copy_log)
        self.log_textbox.bind("<Control-C>", self._copy_log)
        self.log_textbox.bind("<Button-3>", self._show_context_menu)

        self._create_context_menu()

    def _create_progress_bar(self) -> None:
        """Cria a barra de progresso."""
        progress_frame = ttk.Frame(self, style="Dark.TFrame")
        progress_frame.pack(fill="x", padx=30, pady=(0, 25))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            length=840,
        )
        self.progress_bar.pack()

    def _create_context_menu(self) -> None:
        """Cria menu de contexto (botao direito) para area de log."""
        self.context_menu = tk.Menu(
            self,
            tearoff=0,
            bg=DRACULA_CURRENT,
            fg=DRACULA_FG,
            activebackground=DRACULA_PURPLE,
            activeforeground=DRACULA_FG,
            font=("Segoe UI", 10),
        )
        self.context_menu.add_command(label="Copiar", command=self._copy_log)
        self.context_menu.add_command(label="Selecionar Tudo", command=self._select_all_log)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exportar Log...", command=self._export_log)

    def _show_context_menu(self, event: tk.Event) -> None:
        """Exibe menu de contexto na posicao do mouse."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _on_entry_focus_in(self, event: tk.Event) -> None:
        """Trata evento de foco no campo com placeholder."""
        if self._placeholder_active:
            self.file_entry.delete(0, tk.END)
            self.file_entry.configure(fg=NORMAL_COLOR)
            self._placeholder_active = False

    def _on_entry_focus_out(self, event: tk.Event) -> None:
        """Trata evento de perda de foco para restaurar placeholder."""
        if not self.file_entry.get().strip():
            self.file_entry.insert(0, PLACEHOLDER_TEXT)
            self.file_entry.configure(fg=PLACEHOLDER_COLOR)
            self._placeholder_active = True

    def _browse_file(self) -> None:
        """Abre dialogo de selecao de arquivo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo XML",
            filetypes=[
                ("Alteryx Workflows", "*.yxmd"),
                ("XML Files", "*.xml"),
                ("Todos os Arquivos", "*.*"),
            ],
        )
        if filepath:
            self.file_entry.delete(0, tk.END)
            self.file_entry.configure(fg=NORMAL_COLOR)
            self.file_entry.insert(0, filepath)
            self._placeholder_active = False

    def _on_execute_click(self) -> None:
        """Trata clique no botao de execucao."""
        if self._placeholder_active or not self.file_entry.get().strip():
            self.log("ERRO: Selecione um arquivo de entrada", "error")
            return

        filepath = self.file_entry.get().strip()
        operation = self.operation_var.get()
        self.log(f"Iniciando: {operation}")
        self.log(f"Arquivo: {filepath}")

        if self._on_generate_callback:
            self._on_generate_callback(filepath, operation)

    def log(self, message: str, level: str = "info") -> None:
        """Adiciona mensagem a area de log com estilo opcional."""
        self.log_textbox.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{timestamp}] ", "info")
        self.log_textbox.insert("end", f"{message}\n", level)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self._log_messages.append(f"[{timestamp}] {message}")
        self.update()

    def set_progress(self, value: float) -> None:
        """Define o valor da barra de progresso (0.0 a 1.0)."""
        self.progress_var.set(value * 100)
        self.update()

    def set_button_state(self, enabled: bool) -> None:
        """Habilita ou desabilita o botao de execucao."""
        if enabled:
            self.execute_btn.configure(state="normal", bg=DRACULA_GREEN)
        else:
            self.execute_btn.configure(state="disabled", bg=DRACULA_COMMENT)

    def get_month_year(self) -> tuple[int, int]:
        """Parseia o mes/ano selecionado e retorna como (year, month)."""
        month_year = self.month_var.get()
        parts = month_year.split("/")
        month = int(parts[0])
        year = int(parts[1])
        return year, month

    def set_on_generate(self, callback: Callable) -> None:
        """Define o callback para o botao de execucao."""
        self._on_generate_callback = callback

    def _clear_log(self) -> None:
        """Limpa a area de log."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.configure(state="disabled")
        self._log_messages.clear()

    def _select_all_log(self, event: Optional[tk.Event] = None) -> str:
        """Seleciona todo o texto na area de log."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.tag_add("sel", "1.0", "end")
        self.log_textbox.configure(state="disabled")
        return "break"

    def _copy_log(self, event: Optional[tk.Event] = None) -> str:
        """Copia texto selecionado para a area de transferencia."""
        try:
            self.log_textbox.configure(state="normal")
            selected = self.log_textbox.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(selected)
            self.log_textbox.configure(state="disabled")
        except tk.TclError:
            all_text = self.log_textbox.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(all_text)
        return "break"

    def _export_log(self) -> None:
        """Exporta log para um arquivo texto."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.logs_dir,
            initialfile=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if filepath:
            content = self.log_textbox.get("1.0", "end-1c")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"Log exportado para: {filepath}", "success")

    def save_session_log(self, stats: dict) -> Path:
        """Salva log de sessao com metricas na pasta de logs."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"session_{timestamp}.txt"

        content = self.log_textbox.get("1.0", "end-1c")

        metrics = [
            "=" * 50,
            "METRICAS DA SESSAO",
            "=" * 50,
            f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Nodes processados: {stats.get('nodes_modified', 0)}",
            f"Datas substituidas: {stats.get('total_dates', 0)}",
            f"Servidores substituidos: {stats.get('total_servers', 0)}",
            f"Arquivos processados: {stats.get('files_processed', 0)}",
            "=" * 50,
            "",
            "LOG COMPLETO:",
            "-" * 50,
            content,
        ]

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(metrics))

        return log_file


# "A interface e o produto." - Jef Raskin
