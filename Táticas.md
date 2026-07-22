# Resumo do Projeto

O objetivo do projeto foi construir um pipeline completo para processamento de leads, transformando um arquivo JSON com dados inconsistentes em uma estrutura limpa, padronizada e pronta para integração com outros sistemas.

O pipeline foi dividido em módulos independentes para manter baixo acoplamento, alta legibilidade e facilitar futuras evoluções.

Fluxo geral:

```text
Leitura
      ↓
Diagnóstico
      ↓
Normalização
      ↓
Validação
      ↓
Deduplicação
      ↓
Classificação
      ↓
Geração do arquivo final
```

---

# Arquitetura utilizada

O projeto foi dividido em responsabilidades únicas.

## reader.py

Responsável exclusivamente pela leitura do JSON.

Principais funções:

* leitura do arquivo
* validação estrutural
* verificação da raiz do JSON
* validação dos registros

Pensamento utilizado:

> Separar leitura da lógica de negócio torna o código reutilizável para qualquer outra origem de dados.

---

## diagnostic.py

Criado antes da transformação dos dados.

Objetivo:

inspecionar a qualidade dos registros recebidos.

Informações apresentadas:

* quantidade de registros
* campos encontrados
* campos inesperados
* campos ausentes
* campos vazios
* tipos encontrados
* problemas estruturais

Pensamento:

> Nunca modificar dados sem primeiro conhecer sua qualidade.

---

## normalizers.py

Responsável somente por normalizar valores.

Foram implementadas funções independentes para:

### Textos

* trim
* remoção de espaços duplicados
* padronização

---

### Emails

* lowercase
* trim
* regex
* validação

Pensamento:

> Email representa a identidade do lead.

---

### Telefones

* remoção de caracteres especiais
* preservação apenas dos dígitos

---

### Datas

Conversão para ISO 8601.

Foram aceitos:

* ISO
* dd/mm/yyyy
* yyyy/mm/dd
* Jan 7, 2026
* timestamps Unix

Pensamento:

> Sistemas diferentes geram datas diferentes.

Padronizar evita problemas de integração.

---

### Classificação

Foi criada uma classificação simples utilizando palavras-chave.

Exemplos:

* demo
* commercial
* support
* partnership
* general

Sem IA.

Apenas regras determinísticas.

---

# processor.py

É o coração do projeto.

Responsável por:

* aplicar normalizações
* validar regras
* rejeitar registros inválidos
* deduplicar
* montar resultado final

Pensamento:

> Todas as regras de negócio ficam concentradas em um único módulo.

---

# writer.py

Responsável pela gravação.

Foi utilizada escrita atômica.

Fluxo:

arquivo temporário

↓

replace()

Pensamento:

> Evita arquivos corrompidos caso a execução falhe durante a escrita.

---

# main.py

Orquestração.

Fluxo:

```text
reader

↓

diagnostic

↓

processor

↓

writer
```

O main praticamente não possui regra de negócio.

---

# Testes

Foram criados testes unitários para:

## normalização

* texto
* email
* telefone
* datas

---

## processor

* rejeição
* deduplicação
* alias nome/name
* preservação do registro original

---

# Principais regras implementadas

## Email obrigatório

Se:

* inexistente

ou

* inválido

↓

registro rejeitado.

---

## Alias

Aceita:

```text
nome
```

como

```text
name
```

---

## Deduplicação

Chave:

email

Critério:

registro mais recente.

---

## Telefones

Normalização

Não rejeita.

Campo opcional.

---

## Datas

Conversão para ISO 8601.

---

## Classificação

Mensagem analisada.

Palavras-chave.

Sem Machine Learning.

---

# Estruturas utilizadas

Durante o projeto foram utilizados:

## pathlib

Para manipulação segura de caminhos.

---

## json

Leitura e escrita.

---

## datetime

Conversão das datas.

---

## re

Regex para:

* emails
* telefones

---

## dataclass

Representação dos resultados do processamento.

---

## typing

Utilização de:

* Any
* Mapping
* Iterable
* Final
* Sequence
* Type Hints

---

## unittest

Testes automatizados.

---

# Princípios de engenharia adotados

Durante todo o desenvolvimento foram seguidos alguns princípios.

## Single Responsibility Principle

Cada arquivo possui apenas uma responsabilidade.

---

## Funções pequenas

Cada função faz apenas uma tarefa.

---

## Imutabilidade

O registro original nunca é alterado.

Sempre é criado um novo registro normalizado.

---

## Separação entre infraestrutura e negócio

Infraestrutura:

* leitura
* escrita

Negócio:

* normalização
* validação
* deduplicação

---

## Biblioteca padrão

Foi utilizada apenas a Standard Library do Python.

Pensamento:

> Reduz dependências, facilita execução e demonstra domínio da linguagem.

---

# Pensamentos utilizados durante o desenvolvimento

Durante o case, a linha de raciocínio foi aproximadamente esta:

### 1

Antes de escrever código, entender completamente os dados.

---

### 2

Diagnosticar os problemas antes de corrigi-los.

---

### 3

Normalizar primeiro.

Validar depois.

---

### 4

Utilizar email como identificador principal.

---

### 5

Evitar perda de informação.

Registros inválidos são armazenados junto com o motivo da rejeição.

---

### 6

Separar regras de negócio da infraestrutura.

---

### 7

Manter o código simples o suficiente para explicar durante uma entrevista.

---

### 8

Projetar pensando em evolução.

Hoje:

JSON

Futuro:

* API
* Banco
* JSON Lines
* Filas

sem alterar a lógica principal.

---

# Melhorias futuras

Caso o projeto evoluísse, os próximos passos seriam:

* suporte a JSON Lines;
* processamento em streaming;
* configuração externa das regras de classificação;
* logging estruturado;
* métricas;
* processamento paralelo;
* persistência de deduplicação;
* integração com APIs;
* banco de dados;
* filas de mensagens.

---

# Como explicar o projeto em uma entrevista

> "Desenvolvi um pipeline modular para processamento de leads utilizando apenas a biblioteca padrão do Python. O fluxo começa validando a estrutura do JSON, gera um diagnóstico da qualidade dos dados, normaliza textos, emails, telefones e datas, aplica regras de negócio, rejeita registros inválidos com justificativa, elimina duplicidades utilizando o email como identificador principal, classifica o interesse do lead por palavras-chave e gera um arquivo final estruturado com um resumo da execução. Procurei manter a separação de responsabilidades entre leitura, processamento e escrita para facilitar manutenção, testes e futuras integrações com outras fontes de dados."

