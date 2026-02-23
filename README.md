<div align="center">

[![opensource](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](#)
[![Licenca](https://img.shields.io/badge/licenca-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)

<h1>QoL Alteryx-ODI Tools</h1>
</div>

---

### Descrição

Ferramenta Python com interface gráfica (Tkinter) para parsing, conversão e manipulação
de workflows Alteryx (.yxmd) e packages ODI em formato XML. Permite processamento
cirúrgico de templates, validação de regras, comparação de arquivos e exportação de
documentação automática.

---

### Funcionalidades

- **Parser Alteryx**: Extrai metadados de workflows .yxmd (nodes, conexões, propriedades)
- **Parser ODI**: Extrai metadados de packages ODI XML (steps, scenarios, interfaces)
- **Conversor Bidirecional**: Converte entre formatos Alteryx e ODI
- **Processamento de Template**: Substituição cirúrgica de datas e servidores em XML
- **Validação de Workflows**: Verifica integridade, nodes órfãos, datas hardcoded
- **Diff Viewer**: Comparação side-by-side de arquivos XML
- **Busca e Substituição**: Busca com texto simples ou regex em conteúdo XML
- **Processamento em Lote**: Processa múltiplos arquivos de uma vez
- **Exportação de Documentação**: Gera docs Markdown automáticos
- **Auto Update**: Verificação de novas versões

### Padrões de Data Suportados

| Formato | Exemplo |
|---------|---------|
| YYYY-MM-DD | 2024-01-01 |
| DD/MM/YYYY | 01/01/2024 |
| MM/YYYY | 01/2024 |
| MM-YYYY | 01-2024 |

---

### Instalação e Uso

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
    xml_processor.py       # Processamento cirúrgico de XML
    validation.py          # Regras de validação
  gui/
    main_window.py         # Interface principal Tkinter (tema Dracula)
    diff_viewer.py         # Visualizador side-by-side de diffs
    search_dialog.py       # Diálogo de busca e substituição
  exporters/
    doc_exporter.py        # Exportação de documentação Markdown
  batch/
    processor.py           # Processamento em lote
  updater/
    auto_update.py         # Verificação de atualizações
tests/
  test_alteryx_parser.py   # Testes do parser Alteryx
  test_odi_parser.py       # Testes do parser ODI
  test_converter.py        # Testes do conversor
docs/
  user_guide.md            # Guia do usuário
  tutorials.md             # Tutoriais detalhados
```

---

### Licença

Este projeto está licenciado sob a GPLv3 - veja o arquivo [LICENSE](LICENSE) para detalhes.
