# Guia do Usuario - QoL Alteryx-ODI Tools

## Introducao

O QoL Alteryx-ODI Tools e uma ferramenta Python com interface grafica para manipulacao
de workflows Alteryx (.yxmd) e packages ODI em formato XML. Permite parsing, conversao,
validacao e processamento em lote de arquivos de workflow.

## Requisitos

- Python 3.10+
- Tkinter (incluso na instalacao padrao do Python)
- Nenhuma dependencia externa

## Instalacao

### Linux

```bash
chmod +x install.sh
./install.sh
source venv/bin/activate
python main.py
```

### Windows

```batch
setup.bat
```

## Funcionalidades

### 1. Parser Alteryx

Extrai metadados de workflows Alteryx (.yxmd):

- Nodes com ToolID, plugin type, posicao e anotacao
- Conexoes entre nodes
- Propriedades globais do workflow
- Constantes definidas

**Como usar:**
1. Selecione "Parsear Workflow Alteryx" no dropdown
2. Clique em "Procurar" e selecione o arquivo .yxmd
3. Clique em "Executar"
4. Os metadados serao exibidos no log

### 2. Parser ODI

Extrai metadados de packages ODI:

- Steps com tipo, comando e fluxo de execucao
- Cenarios referenciados
- Interfaces com source/target e mappings
- Variaveis do package

**Como usar:**
1. Selecione "Parsear Package ODI" no dropdown
2. Selecione o arquivo XML do package
3. Clique em "Executar"

### 3. Converter Alteryx para ODI

Converte workflows Alteryx para formato de package ODI:

- Mapeia tools Alteryx para steps ODI
- Preserva conexoes como fluxo de execucao
- Gera XML ODI valido

**Mapeamento de Tools:**

| Tool Alteryx | Step ODI |
|-------------|----------|
| DbFileInput | DataStoreCommand |
| DbFileOutput | DataStoreCommand |
| Filter | ProcedureCommand |
| Formula | ProcedureCommand |
| Join | ProcedureCommand |
| Sort | ProcedureCommand |

### 4. Converter ODI para Alteryx

Converte packages ODI para formato de workflow Alteryx:

- Mapeia steps ODI para nodes Alteryx
- Atribui ToolIDs sequenciais
- Posiciona nodes automaticamente no canvas

### 5. Processar Template XML

Aplica substituicoes cirurgicas em templates XML:

- Substitui datas em nodes especificos (YYYY-MM-DD, DD/MM/YYYY, MM/YYYY)
- Substitui string de conexao de servidor
- Preserva todos os demais dados do XML

**Formatos de data suportados:**
- `YYYY-MM-DD` (ex: 2024-01-01)
- `YYYY-MM` (ex: 2024-01)
- `DD/MM/YYYY` (ex: 01/01/2024)
- `MM/YYYY` (ex: 01/2024)
- `MM-YYYY` (ex: 01-2024)

### 6. Validacao de Workflows

Verifica integridade e boas praticas:

- Nodes orfaos (sem conexoes)
- Outputs desconectados
- Datas hardcoded
- Servidores hardcoded
- Anotacoes ausentes
- ToolIDs duplicados
- Configuracoes vazias

### 7. Diff Viewer

Comparacao side-by-side entre dois arquivos XML:

- Destaque de linhas adicionadas, removidas e modificadas
- Scroll sincronizado
- Cores Dracula para diferenciacao visual

### 8. Busca e Substituicao

Busca e substituicao em conteudo XML:

- Busca por texto simples
- Busca por expressao regular
- Opcao de sensibilidade a maiusculas
- Opcao de palavra inteira
- Preview antes de aplicar

### 9. Processamento em Lote

Processa multiplos arquivos de uma vez:

- Selecao de diretorio
- Filtro por padrao de arquivo
- Processamento recursivo opcional
- Barra de progresso e log detalhado

### 10. Exportacao de Documentacao

Gera documentacao Markdown de workflows e packages:

- Informacoes gerais (nome, versao, descricao)
- Estatisticas (nodes, conexoes, inputs/outputs)
- Lista de tools com anotacoes
- Resultado de validacao

## Interface Grafica

A interface utiliza o tema Dracula com as seguintes cores:
- Fundo: `#282a36`
- Texto: `#f8f8f2`
- Destaque: `#bd93f9` (roxo)
- Sucesso: `#50fa7b` (verde)
- Erro: `#ff5555` (vermelho)
- Aviso: `#ffb86c` (laranja)
- Info: `#8be9fd` (ciano)

## Atalhos de Teclado

| Atalho | Acao |
|--------|------|
| Ctrl+A | Selecionar todo o log |
| Ctrl+C | Copiar selecao |
| Botao direito | Menu de contexto |

## Estrutura do Projeto

```
main.py                    # Ponto de entrada
src/
  core/
    alteryx_parser.py      # Parser de workflows Alteryx
    odi_parser.py          # Parser de packages ODI
    workflow_extractor.py  # Extrator de metadados Alteryx
    package_extractor.py   # Extrator de metadados ODI
    converter.py           # Conversor bidirecional
    xml_processor.py       # Processamento cirurgico de XML
    validation.py          # Regras de validacao
  gui/
    main_window.py         # Janela principal (Tkinter)
    diff_viewer.py         # Visualizador de diffs
    search_dialog.py       # Busca e substituicao
  exporters/
    doc_exporter.py        # Exportacao de documentacao
  batch/
    processor.py           # Processamento em lote
  updater/
    auto_update.py         # Atualizacao automatica
tests/
  test_alteryx_parser.py   # Testes do parser Alteryx
  test_odi_parser.py       # Testes do parser ODI
  test_converter.py        # Testes do conversor
docs/
  user_guide.md            # Este documento
  tutorials.md             # Tutoriais detalhados
```

## Resolucao de Problemas

### Erro ao parsear XML
- Verifique se o arquivo XML esta bem-formado
- Verifique a codificacao (UTF-8 recomendado)
- Verifique se o arquivo nao esta corrompido

### Interface nao abre
- Verifique se o Tkinter esta instalado: `python -c "import tkinter"`
- No Linux, instale: `sudo apt install python3-tk`

### Conversao incompleta
- Verifique os avisos no log para tools sem mapeamento
- Consulte a tabela de mapeamento acima
- Tools customizados nao possuem mapeamento automatico

## Licenca

GPLv3 - Software livre, modificacao e redistribuicao permitidas.
