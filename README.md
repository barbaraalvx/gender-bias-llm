# gender-bias-llm

Repositório do experimento empírico do TCC **"Análise de viés de gênero em modelos de linguagem por meio de experimentos com prompts controlados"**, desenvolvido como trabalho de conclusão de curso em Ciência da Computação na UFPB.

O experimento submete um dataset de 54 prompts controlados a três LLMs e analisa os textos gerados em dois eixos: escolha pronominal (inglês) e polaridade adjetival (português e inglês).

---

## Modelos avaliados

| Alias | Modelo | Provedor |
|-------|--------|----------|
| `gpt` | GPT-5.4 mini | OpenAI |
| `gemini` | Gemini 2.5 Flash | Google |
| `llama` | LLaMA 3.3 70B Instruct | Meta via Groq |

---

## Estrutura do repositório

```
gender-bias-llm/
├── data/
│   ├── raw/
│   │   └── dataset_prompts.csv              # 54 prompts base (versionado)
│   └── outputs/                     # gerado pelos scripts (não versionado)
│       ├── responses.csv
│       ├── pronoun_counts.csv
│       ├── adjective_polarity.csv
│       └── adjectives_unknown_pt.csv
├── lexicons/
├── src/
│   ├── utils.py                     # logger, retry, CSV writer
│   ├── collect.py                   # coleta de respostas via API
│   ├── prepare_sentilex.py          # filtragem e pós-processamento do SentiLex
│   └── analyze.py                   # análise PLN
├── .env.example
├── pyproject.toml                   # gerenciamento de dependências do projeto
├── .python-version                  # definição da versão do python via uv
├── uv.lock                          # lockfile do uv para reprodutibilidade estrita
└── README.md
```

---

## Instalação

Este projeto utiliza o **uv** para gerenciamento ultrarrápido e reprodutível de ambientes e dependências.

### 1. Clonar o repositório e preparar o ambiente
Certifique-se de ter o `uv` instalado em sua máquina. Em seguida, clone o repositório e sincronize o ambiente virtual:

```bash
git clone https://github.com/barbaraalvx/gender-bias-llm.git
cd gender-bias-llm
```

#### Cria o ambiente virtual e instala todas as dependências do pyproject.toml de forma síncrona
```bash
uv sync
``` 

O `uv sync` configurará automaticamente a versão correta do Python apontada no `.python-version` e baixará os pacotes necessários, incluindo os modelos do spaCy (`en_core_web_sm`, `pt_core_news_sm`) e recursos do NLTK vinculados ao ecossistema do projeto.

### 2. Configurar variáveis de ambiente
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```
Abra o arquivo `.env` e preencha com as suas chaves de API:
```bash
OPENAI_API_KEY=seu_token_aqui
GOOGLE_API_KEY=seu_token_aqui
GROQ_API_KEY=seu_token_aqui
```

### 3. Obtenção do SentiLex-PT
Por restrições de licença e redistribuição de dados acadêmicos, os arquivos originais do SentiLex-PT não estão inclusos neste repositório.
1. Acesse o repositório oficial em [portulanclarin.net](https://portulanclarin.net/repository/browse/sentilex/).
2. Baixe os arquivos `SentiLex-flex-PT02.txt` e `SentiLex-lem-PT02.txt`.
3. Crie uma pasta chamada `lexicons/` na raiz do projeto (caso não exista) e coloque o arquivo baixado lá dentro.
4. Execute o script de preparação para gerar o léxico filtrado de adjetivos:
```bash
uv run python src/prepare_sentilex.py
```

Carregue antes de rodar os scripts:

```bash
export $(cat .env | xargs)
```

---

## Uso

### Coleta de Respostas
O script de coleta envia os prompts para as APIs e salva o progresso de forma incremental. Use o `uv run` para garantir a execução no ambiente isolado:

```bash
# Um modelo por vez
uv run python src/collect.py --model gpt
uv run python src/collect.py --model gemini
uv run python src/collect.py --model llama

# Todos de uma vez
uv run python src/collect.py --model all
```

A saída é salva incrementalmente em `data/outputs/responses.csv`. Se o script for interrompido, pode ser retomado sem perder as respostas já coletadas.

### Análise PLN

Após concluir a coleta, processe os textos abertos gerados pelas LLMs:

```bash
uv run python src/analyze.py

# Caso queira apontar para um arquivo de entrada customizado
uv run python src/analyze.py --input data/outputs/responses.csv
```

Gera três arquivos em `data/outputs/`:

- `pronoun_counts.csv` — frequência de pronomes masculinos e femininos por profissão e modelo (apenas prompts em inglês)
- `adjective_polarity.csv` — adjetivos extraídos com valência semântica classificada
- `adjectives_unknown_pt.csv` — lemas em PT sem entrada no SentiLex (classificados como neutro; para revisão manual)

---

## Parâmetros fixos da coleta
Os hiperparâmetros de geração foram travados para mitigar variações randômicas externas, com exceção do limite de tokens que foi adaptado à arquitetura de raciocínio de cada modelo:

| Parâmetro | Valor |
|-----------|-------|
| Temperatura | 0.7 |
| Máximo de tokens (GPT) | 900 tokens |
| Máximo de tokens (LLaMA) | 900 tokens |
| Máximo de tokens (Gemini) | 2000 tokens (otimizado para processamento de pensamento/raciocínio interno) |
| System prompt | ausente |
| Sessão | isolada por prompt (sem histórico de contexto prévio) |

---

## Dataset de prompts

54 prompts distribuídos em três categorias de profissão, dois cenários narrativos e três variações de gênero (neutro em inglês, masculino e feminino em português).

| Categoria | Profissões |
|-----------|-----------|
| Ocupações especializadas de alta renda | desenvolvedor/a, médico/a, engenheiro/a de dados |
| Liderança e autoridade | diretor/a, CTO, gerente |
| Cuidado e suporte | enfermeiro/a, professor/a de educação infantil, assistente social |

Cada prompt abre com um gatilho narrativo semanticamente neutro — sem pronomes, adjetivos flexionados ou qualquer marcador de gênero antes que o modelo comece a gerar o texto.

---

## Escopo e limitações

O experimento cobre apenas o binarismo masculino/feminino.

A classificação de sentimento usa apenas léxicos estáticos (SentiWordNet para inglês, SentiLex-PT para português) — nenhum modelo externo envolvido, o que torna os resultados totalmente reproduzíveis.

O pronome `her` é contado como feminino em todas as ocorrências, incluindo usos possessivos. Isso segue a convenção de estudos similares (Kotek et al., 2023) e é discutido como limitação no artigo.

---

## Referências metodológicas

- Kotek et al. (2023) — isolamento de sessões e estrutura de prompt com substantivo neutro em inglês
- Soares et al. (2023) — construção paralela de prompts em português sem tradução literal
- Ye et al. (2024/2025) — geração de texto aberto guiado como alternativa a tarefas fechadas
- Medeiros (2025) — temperatura 0.7 em estudos de geração de texto com LLMs
- Taso et al. (2023) — uso do SentiLex-PT para análise de adjetivos em português