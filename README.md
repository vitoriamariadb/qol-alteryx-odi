<div align="center">

[![opensource](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](#)
[![Licenca](https://img.shields.io/badge/licenca-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)

<h1>QoL Alteryx-ODI Tools</h1>
</div>

---

### Descricao

Ferramenta Python com interface grafica (Tkinter) para parsing, conversao e manipulacao
de workflows Alteryx (.yxmd) e packages ODI em formato XML. Permite processamento
cirurgico de templates, validacao de regras, comparacao de arquivos e exportacao de
documentacao automatica.

---

### Funcionalidades

- **Parser Alteryx**: Extrai metadados de workflows .yxmd (nodes, conexoes, propriedades)
- **Parser ODI**: Extrai metadados de packages ODI XML (steps, scenarios, interfaces)
- **Conversor Bidirecional**: Converte entre formatos Alteryx e ODI
- **Processamento de Template**: Substituicao cirurgica de datas e servidores em XML
- **Validacao de Workflows**: Verifica integridade, nodes orfaos, datas hardcoded
- **Diff Viewer**: Comparacao side-by-side de arquivos XML
- **Busca e Substituicao**: Busca com texto simples ou regex em conteudo XML
- **Processamento em Lote**: Processa multiplos arquivos de uma vez
- **Exportacao de Documentacao**: Gera docs Markdown automaticos
- **Auto Update**: Verificacao de novas versoes

### Padroes de Data Suportados

| Formato | Exemplo |
|---------|---------|
| YYYY-MM-DD | 2024-01-01 |
| DD/MM/YYYY | 01/01/2024 |
| MM/YYYY | 01/2024 |
| MM-YYYY | 01-2024 |

---

### Instalacao e Uso

#### Linux

```bash
chmod +x install.sh
./install.sh
source venv/bin/activate
python main.py
```

#### Windows

```batch
setup.bat
```

---

### Estrutura do Projeto

```
main.py                    # Ponto de entrada (orchestrator)
src/
  core/
    alteryx_parser.py      # Parser de workflows Alteryx XML
    odi_parser.py          # Parser de packages ODI XML
    workflow_extractor.py  # Extrator de metadados Alteryx
    package_extractor.py   # Extrator de metadados ODI
    converter.py           # Conversor bidirecional Alteryx/ODI
    xml_processor.py       # Processamento cirurgico de XML
    validation.py          # Regras de validacao
  gui/
    main_window.py         # Interface principal Tkinter (tema Dracula)
    diff_viewer.py         # Visualizador side-by-side de diffs
    search_dialog.py       # Dialogo de busca e substituicao
  exporters/
    doc_exporter.py        # Exportacao de documentacao Markdown
  batch/
    processor.py           # Processamento em lote
  updater/
    auto_update.py         # Verificacao de atualizacoes
tests/
  test_alteryx_parser.py   # Testes do parser Alteryx
  test_odi_parser.py       # Testes do parser ODI
  test_converter.py        # Testes do conversor
docs/
  user_guide.md            # Guia do usuario
  tutorials.md             # Tutoriais detalhados
```

---

### Licenca

Este projeto esta licenciado sob a GPLv3 - veja o arquivo [LICENSE](LICENSE) para detalhes.
