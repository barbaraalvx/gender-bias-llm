# gender-bias-llm

Repositório do experimento empírico do TCC **"Análise de viés de gênero em modelos de linguagem por meio de experimentos com prompts controlados"**, desenvolvido como trabalho de conclusão de curso em Ciência da Computação na UFPB.

O experimento submete um dataset de 54 prompts controlados a três LLMs e analisa os textos gerados em dois eixos: escolha pronominal (inglês) e polaridade adjetival (português e inglês).

---

## Modelos avaliados

| Alias | Modelo | Provedor |
|-------|--------|----------|
| `gpt` | GPT-5.4 mini | OpenAI |
| `gemini` | Gemini 3.5 Flash | Google |
| `llama` | LLaMA 3.1 70B Instruct | Meta via Groq |

---

## Estrutura do repositório

```
gender-bias-llm/
├── data/
│   ├── raw/
│   │   └── dataset.csv              # 54 prompts base (versionado)
│   └── outputs/                     # gerado pelos scripts (não versionado)
│       ├── responses.csv
│       ├── pronoun_counts.csv
│       ├── adjective_polarity.csv
│       └── adjectives_unknown_pt.csv
├── lexicons/
│   └── SentiLex-PT02-Adj.txt        # léxico estático PT (versionado)
├── src/
│   ├── utils.py                     # logger, retry, CSV writer
│   ├── collect.py                   # coleta de respostas via API
│   └── analyze.py                   # análise PLN
├── .env.example
├── requirements.txt
└── README.md
```

---

## Instalação

```bash
git clone https://github.com/barbaraalvx/gender-bias-llm.git
cd gender-bias-llm
pip install -r requirements.txt

# Modelos spaCy
python -m spacy download en_core_web_sm
python -m spacy download pt_core_news_sm

# Recursos NLTK
python -c "import nltk; nltk.download('sentiwordnet'); nltk.download('wordnet')"
```

Copie `.env.example` para `.env` e preencha as chaves:

```bash
cp .env.example .env
```

As variáveis necessárias são:

```
OPENAI_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
```

Carregue antes de rodar os scripts:

```bash
export $(cat .env | xargs)
```

O SentiLex-PT não está incluído neste repositório por restrições de licença. Baixe o arquivo `SentiLex-PT02-Adj.txt` em [portulanclarin.net](https://portulanclarin.net/repository/browse/sentilex/) e coloque-o em `lexicons/`.

---

## Uso

### Coleta

```bash
# Um modelo por vez
python src/collect.py --model gpt
python src/collect.py --model gemini
python src/collect.py --model llama

# Todos de uma vez
python src/collect.py --model all
```

A saída é salva incrementalmente em `data/outputs/responses.csv`. Se o script for interrompido, pode ser retomado sem perder as respostas já coletadas.

### Análise PLN

```bash
python src/analyze.py

# Arquivo de entrada alternativo
python src/analyze.py --input data/outputs/responses.csv
```

Gera três arquivos em `data/outputs/`:

- `pronoun_counts.csv` — frequência de pronomes masculinos e femininos por profissão e modelo (apenas prompts em inglês)
- `adjective_polarity.csv` — adjetivos extraídos com valência semântica classificada
- `adjectives_unknown_pt.csv` — lemas em PT sem entrada no SentiLex (classificados como neutro; para revisão manual)

---

## Parâmetros fixos da coleta

| Parâmetro | Valor |
|-----------|-------|
| Temperatura | 0.7 |
| Máximo de tokens | 300 |
| System prompt | ausente |
| Sessão | isolada por prompt |

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