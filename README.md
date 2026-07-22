# LiveCase Cora — Lead Processing Pipeline

Pipeline em Python para leitura, diagnóstico, normalização, validação, classificação e deduplicação de leads recebidos em JSON.

## Objetivo

O projeto recebe registros de leads com formatos inconsistentes e produz uma saída padronizada, pronta para integração com outros sistemas.

O pipeline executa as seguintes etapas:

1. leitura e validação estrutural do JSON;
2. diagnóstico dos campos recebidos;
3. normalização de textos, emails, telefones e datas;
4. validação de campos obrigatórios;
5. classificação do interesse do lead;
6. deduplicação por email;
7. geração de resumo e arquivo final.

## Estrutura

```text
LiveCase_Cora/
├── data/
│   └── leads_raw.json
├── output/
├── src/
│   ├── reader.py
│   ├── diagnostic.py
│   ├── normalizers.py
│   ├── processor.py
│   ├── writer.py
│   └── main.py
├── tests/
├── pyproject.toml
└── README.md
```

## Requisitos

* Python 3.11 ou superior;
* nenhuma biblioteca externa obrigatória.

## Execução

Na raiz do projeto:

```bash
python -m src.main
```

Para informar arquivos diferentes:

```bash
python -m src.main \
  --input data/leads_raw.json \
  --output output/leads_processed.json
```

No PowerShell:

```powershell
python -m src.main `
  --input data/leads_raw.json `
  --output output/leads_processed.json
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Regras aplicadas

### Email

* espaços externos são removidos;
* letras são convertidas para minúsculas;
* emails ausentes ou inválidos rejeitam o registro;
* o email normalizado é utilizado como chave de deduplicação.

### Nome

O campo `nome` é aceito como alias de `name`.

### Telefone

Caracteres não numéricos são removidos. Um telefone ausente não rejeita o lead.

### Datas

O pipeline aceita formatos ISO, formatos brasileiros, formatos alternativos conhecidos e timestamps Unix. A saída é convertida para ISO 8601.

### Deduplicação

Quando dois registros possuem o mesmo email normalizado, o registro com a data de criação mais recente é mantido.

Em caso de empate, o primeiro registro permanece.

### Classificação

A mensagem é classificada nos segmentos:

* `demo`;
* `commercial`;
* `support`;
* `partnership`;
* `general`.

As regras são baseadas em palavras-chave explícitas e determinísticas.

## Exemplo de saída

```json
{
  "generated_at": "2026-07-22T14:00:00+00:00",
  "summary": {
    "received": 12,
    "processed": 7,
    "rejected": 3,
    "duplicates_removed": 2
  },
  "leads": [],
  "rejected": []
}
```

## Decisões técnicas

### Biblioteca padrão

A solução utiliza somente a biblioteca padrão do Python porque o problema não exige dependências externas. Isso reduz configuração, tempo de instalação e superfície de falhas.

### Separação de responsabilidades

* `reader.py`: leitura e validação estrutural;
* `diagnostic.py`: inspeção da qualidade dos dados;
* `normalizers.py`: funções puras de normalização;
* `processor.py`: regras de negócio;
* `writer.py`: persistência da saída;
* `main.py`: orquestração.

### Imutabilidade da entrada

Os registros originais não são modificados. Cada lead normalizado é criado como um novo dicionário.

### Escalabilidade

O processador aceita qualquer `Iterable` de registros. Isso permite evoluir a origem dos dados para JSON Lines, APIs, paginação ou filas sem alterar as regras centrais.

O formato JSON atual ainda é carregado integralmente em memória. Para volumes muito grandes ou ingestão contínua, uma evolução natural seria usar JSON Lines e processamento incremental.

## Evoluções futuras

* suporte nativo a JSON Lines;
* processamento de diretórios de entrada;
* persistência da deduplicação entre execuções;
* métricas e logging estruturado;
* configuração externa das regras de classificação;
* integração com API, banco de dados ou fila;
* dead-letter queue para registros rejeitados.
