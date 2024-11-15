# Tutoriais - QoL Alteryx-ODI Tools

## Tutorial 1: Primeiro Uso

### Objetivo
Familiarizar-se com a interface e funcionalidades basicas da ferramenta.

### Passos

1. **Iniciar a aplicacao**
   ```bash
   python main.py
   ```

2. **Conhecer a interface**
   - O dropdown superior permite selecionar a operacao desejada
   - O campo "Arquivo de Entrada" aceita caminhos ou selecao via "Procurar"
   - A area de log exibe todas as operacoes em tempo real
   - A barra de progresso indica o andamento do processamento

3. **Parsear um workflow**
   - Selecione "Parsear Workflow Alteryx"
   - Clique em "Procurar" e selecione um arquivo .yxmd
   - Clique em "Executar"
   - Observe os metadados extraidos no log

---

## Tutorial 2: Conversao Alteryx para ODI

### Objetivo
Converter um workflow Alteryx existente para formato de package ODI.

### Pre-requisitos
- Arquivo .yxmd valido

### Passos

1. Selecione "Converter Alteryx -> ODI" no dropdown
2. Selecione o arquivo .yxmd de entrada
3. Clique em "Executar"
4. O arquivo ODI sera salvo na pasta `output/`
5. Verifique os avisos no log para tools sem mapeamento

### Mapeamento de Tools

O conversor mapeia os seguintes plugins Alteryx para tipos de step ODI:

```
DbFileInput  -> DataStoreCommand
DbFileOutput -> DataStoreCommand
Filter       -> ProcedureCommand
Formula      -> ProcedureCommand
Join         -> ProcedureCommand
Sort         -> ProcedureCommand
Summarize    -> ProcedureCommand
Union        -> ProcedureCommand
```

Tools que nao possuem mapeamento serao ignorados e listados nos avisos.

---

## Tutorial 3: Processamento de Template XML

### Objetivo
Modificar datas e servidores em templates de workflow Alteryx.

### Contexto
Em ambientes corporativos, e comum ter workflows que referenciam datas e servidores
fixos. Esta funcionalidade permite atualiza-los de forma cirurgica, modificando
apenas os nodes especificados nas regras (RULES).

### Passos

1. Selecione "Processar Template XML"
2. Selecione o arquivo template
3. No campo "Mes/Ano", selecione o periodo desejado
4. No campo "Servidor", informe a connection string
5. Clique em "Executar"

### Como funciona internamente

O processador usa um dicionario de regras (RULES) que mapeia cada template
para os Tool IDs que devem ser modificados:

```python
RULES = {
    "gerar-fechamento-diario.yxmd": {
        "date_nodes": {"tool_ids": ["16", "17"]},
        "server_nodes": [],
    },
    "base-funil.yxmd": {
        "date_nodes": {"tool_ids": ["2877", "2878", "1695"]},
        "server_nodes": ["2916", "2914", "2978"],
    },
}
```

Apenas os nodes listados em `tool_ids` terao suas datas substituidas.
Apenas os nodes em `server_nodes` terao o servidor atualizado.

### Formatos de data reconhecidos

| Formato | Exemplo | Substituicao |
|---------|---------|-------------|
| YYYY-MM-DD | 2024-01-15 | 2024-03-01 |
| YYYY-MM | 2024-01 | 2024-03 |
| DD/MM/YYYY | 15/01/2024 | 01/03/2024 |
| MM/YYYY | 01/2024 | 03/2024 |
| MM-YYYY | 01-2024 | 03-2024 |

---

## Tutorial 4: Validacao de Workflows

### Objetivo
Verificar integridade e boas praticas de um workflow antes de promove-lo.

### Regras de validacao

| Codigo | Severidade | Descricao |
|--------|-----------|-----------|
| ORPHAN_NODE | Aviso | Node sem nenhuma conexao |
| DISCONNECTED_OUTPUT | Erro | Output sem input conectado |
| HARDCODED_DATE | Info | Data fixa encontrada no XML |
| HARDCODED_SERVER | Info | Servidor fixo encontrado |
| MISSING_ANNOTATIONS | Aviso | Mais de 50% dos nodes sem anotacao |
| DUPLICATE_TOOL_ID | Erro | ToolID repetido no workflow |
| EMPTY_CONFIG | Aviso | Tool sem configuracao |

### Interpretando resultados

- **Erros**: Problemas que impedem o workflow de funcionar corretamente
- **Avisos**: Problemas de qualidade que devem ser corrigidos
- **Info**: Informacoes uteis para revisao manual

---

## Tutorial 5: Comparacao de Arquivos (Diff Viewer)

### Objetivo
Comparar dois arquivos XML para identificar diferencas.

### Passos

1. Na janela principal, acesse o Diff Viewer
2. Clique em "Arquivo Esquerdo" para selecionar o original
3. Clique em "Arquivo Direito" para selecionar o modificado
4. Clique em "Comparar"
5. As diferencas serao destacadas com cores:
   - Verde: linhas adicionadas
   - Vermelho: linhas removidas
   - Amarelo: linhas modificadas

---

## Tutorial 6: Busca e Substituicao

### Objetivo
Realizar buscas e substituicoes em conteudo XML.

### Opcoes disponiveis

- **Sensivel a maiusculas**: diferencia "ABC" de "abc"
- **Expressao regular**: permite padroes como `\d{4}-\d{2}-\d{2}`
- **Palavra inteira**: busca apenas palavras completas, nao substrings

### Exemplos de regex uteis

| Padrao | Descricao |
|--------|-----------|
| `\d{4}-\d{2}-\d{2}` | Datas no formato YYYY-MM-DD |
| `\d{2}/\d{2}/\d{4}` | Datas no formato DD/MM/YYYY |
| `\w+\.corp:\d+` | Servidores corporativos |
| `ToolID="\d+"` | Atributos ToolID |

---

## Tutorial 7: Processamento em Lote

### Objetivo
Processar multiplos arquivos de uma vez.

### Configuracao

```python
config = BatchConfig(
    input_dir=Path("workflows/"),
    output_dir=Path("output/"),
    operation="parse",       # parse, convert_a2o, convert_o2a, template
    recursive=True,          # buscar em subdiretorios
    file_pattern="*.yxmd",   # padrao de arquivo
    max_files=100,           # limite de arquivos (0 = sem limite)
)
```

### Operacoes disponiveis

- `parse`: extrai metadados de cada arquivo
- `convert_a2o`: converte Alteryx para ODI
- `convert_o2a`: converte ODI para Alteryx
- `template`: aplica substituicoes de template

---

## Tutorial 8: Exportacao de Documentacao

### Objetivo
Gerar documentacao automatica de workflows e packages.

### Formato de saida

A documentacao e gerada em Markdown (.md) contendo:

- Informacoes gerais (nome, versao, autor)
- Estatisticas (nodes, conexoes, inputs/outputs)
- Tabela de tools com ID, tipo e anotacao
- Resultado de validacao (se habilitado)
- Lista de fontes e destinos de dados (para ODI)
- Fluxo de execucao (para ODI)

### Exemplo de uso

```python
from src.exporters.doc_exporter import DocumentationExporter

exporter = DocumentationExporter()
doc_path = exporter.export_workflow_doc(
    filepath=Path("workflow.yxmd"),
    output_dir=Path("docs/generated/"),
    include_validation=True,
)
```
