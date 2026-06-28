"""
analyze.py: análise PLN sobre as respostas coletadas.

Executa dois eixos de análise:
  1. Frequência pronominal (apenas prompts em inglês)
     Pronomes masculinos: he, his, him
     Pronomes femininos: she, her
     Saída: pronoun_counts.csv

  2. Polaridade adjetival (inglês e português)
     POS-Tagging via spaCy; classificação via SentiWordNet (EN) e SentiLex-PT (PT)
     Saída: adjective_polarity.csv

Uso:
    python analyze.py
    python analyze.py --input respostas_custom.csv

Dependências:
    pip install spacy nltk
    python -m spacy download en_core_web_sm
    python -m spacy download pt_core_news_sm
    python -c "import nltk; nltk.download('sentiwordnet'); nltk.download('wordnet')"

SentiLex-PT:
    Baixe SentiLex-lem-PT02.txt de https://b2find.eudat.eu
    e gere o arquivo filtrado com: python src/prepare_sentilex.py
"""

import argparse
import csv
import re
from pathlib import Path

import spacy
from nltk.corpus import sentiwordnet as swn
import nltk

from utils import setup_logger

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

INPUT_PATH = "data/outputs/responses.csv"
SENTILEX_PATH = "lexicons/SentiLex-PT02-Adj.txt"

PRONOUN_OUTPUT = "data/outputs/pronoun_counts.csv"
ADJECTIVE_OUTPUT = "data/outputs/adjective_polarity.csv"

MASC_PRONOUNS = {"he", "his", "him"}
FEM_PRONOUNS  = {"she", "her"}

# ---------------------------------------------------------------------------
# Carregamento dos modelos spaCy (feito uma vez)
# ---------------------------------------------------------------------------

def load_spacy_models(logger):
    models = {}
    for lang, model_name in [("EN", "en_core_web_sm"), ("PT", "pt_core_news_sm")]:
        try:
            models[lang] = spacy.load(model_name)
            logger.info(f"spaCy carregado: {model_name}")
        except OSError:
            raise OSError(
                f"Modelo spaCy '{model_name}' não encontrado. "
                f"Execute: python -m spacy download {model_name}"
            )
    return models


# ---------------------------------------------------------------------------
# SentiLex-PT
# ---------------------------------------------------------------------------

def load_sentilex(path: str, logger) -> dict[str, str]:
    """
    Lê o SentiLex-PT (arquivo de lemas filtrado por prepare_sentilex.py) e devolve
    um dicionário {lemma_lower: 'positivo'|'negativo'|'neutro'}.

    Formato real do arquivo (separador ';'):
        abafado.PoS=Adj;TG=HUM:N0;POL:N0=-1;ANOT=JALC
    """
    lexicon = {}
    p = Path(path)
    if not p.exists():
        logger.warning(
            f"SentiLex não encontrado em '{path}'. "
            "Adjetivos em PT serão classificados como neutro."
        )
        return lexicon

    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            # Lema é tudo antes do primeiro ponto
            lemma = line.split(".")[0].lower()

            # Extrai polaridade do campo POL:N0=<valor>
            pol_value = None
            for part in line.split(";"):
                if part.startswith("POL:N0="):
                    try:
                        pol_value = int(part.split("=")[1])
                    except ValueError:
                        pass
                    break

            if pol_value is None:
                continue
            if pol_value > 0:
                lexicon[lemma] = "positivo"
            elif pol_value < 0:
                lexicon[lemma] = "negativo"
            else:
                lexicon[lemma] = "neutro"

    logger.info(f"SentiLex carregado: {len(lexicon)} entradas")
    return lexicon


# ---------------------------------------------------------------------------
# SentiWordNet (inglês)
# ---------------------------------------------------------------------------

def classify_en_adjective(word: str) -> str:
    """
    Consulta o SentiWordNet pelo lema do adjetivo.
    Devolve 'positivo', 'negativo' ou 'neutro'.
    """
    synsets = list(swn.senti_synsets(word, "a"))
    if not synsets:
        return "neutro"

    pos_score = sum(s.pos_score() for s in synsets) / len(synsets)
    neg_score = sum(s.neg_score() for s in synsets) / len(synsets)

    if pos_score > neg_score and pos_score > 0.1:
        return "positivo"
    if neg_score > pos_score and neg_score > 0.1:
        return "negativo"
    return "neutro"


# ---------------------------------------------------------------------------
# Normalização de texto
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Caixa baixa e remoção de pontuação redundante. Mantém estrutura para POS-Tagging."""
    text = text.lower()
    # Remove pontuação exceto apóstrofos (relevantes para contrações em inglês)
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Análise 1 — Frequência pronominal (EN)
# ---------------------------------------------------------------------------

def analyze_pronouns(rows: list[dict], logger) -> list[dict]:
    """
    Para cada combinação (profissão, modelo), conta pronomes M e F
    nos textos gerados a partir de prompts em inglês.
    """
    counts: dict[tuple, dict] = {}

    en_rows = [r for r in rows if r["idioma"].strip().upper() == "EN"]
    logger.info(f"Prompts em EN para análise pronominal: {len(en_rows)}")

    for row in en_rows:
        key = (row["profissao"], row["modelo"])
        if key not in counts:
            counts[key] = {"masc": 0, "fem": 0}

        tokens = normalize(row["resposta"]).split()
        for token in tokens:
            t = token.strip("'")  # remove apóstrofos residuais
            if t in MASC_PRONOUNS:
                counts[key]["masc"] += 1
            elif t in FEM_PRONOUNS:
                counts[key]["fem"] += 1

    results = []
    for (profissao, modelo), c in counts.items():
        masc, fem = c["masc"], c["fem"]
        total = masc + fem
        razao = round(masc / fem, 4) if fem > 0 else None
        results.append({
            "profissao":  profissao,
            "modelo":     modelo,
            "count_masc": masc,
            "count_fem":  fem,
            "total":      total,
            "razao_mf":   razao if razao is not None else "N/A (fem=0)",
        })

    return results


def save_pronoun_counts(results: list[dict], logger):
    fields = ["profissao", "modelo", "count_masc", "count_fem", "total", "razao_mf"]
    with open(PRONOUN_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Frequência pronominal salva: {PRONOUN_OUTPUT}")


# ---------------------------------------------------------------------------
# Análise 2 — Polaridade adjetival (EN + PT)
# ---------------------------------------------------------------------------

def analyze_adjectives(rows: list[dict], nlp_models: dict, sentilex: dict, logger) -> list[dict]:
    """
    Extrai adjetivos de cada resposta via POS-Tagging e classifica
    a valência com SentiWordNet (EN) ou SentiLex-PT (PT).
    """
    results = []
    unknown_for_review = []

    for i, row in enumerate(rows, 1):
        lang = row["idioma"].strip().upper()
        if lang not in nlp_models:
            continue

        nlp = nlp_models[lang]
        text_normalized = normalize(row["resposta"])
        doc = nlp(text_normalized)

        for token in doc:
            if token.pos_ != "ADJ":
                continue

            lemma = token.lemma_.lower()

            if lang == "EN":
                valencia = classify_en_adjective(lemma)
            else:  # PT
                valencia = sentilex.get(lemma, "neutro")
                if lemma not in sentilex:
                    unknown_for_review.append({
                        "lemma":     lemma,
                        "id_prompt": row["id_prompt"],
                        "modelo":    row["modelo"],
                    })

            results.append({
                "id_prompt": row["id_prompt"],
                "modelo":    row["modelo"],
                "idioma":    lang,
                "profissao": row["profissao"],
                "genero":    row["genero"],
                "cenario":   row.get("cenario", ""),
                "adjetivo":  token.text,
                "lemma":     lemma,
                "valencia":  valencia,
            })

        if i % 50 == 0:
            logger.info(f"Adjetivos: {i}/{len(rows)} respostas processadas")

    if unknown_for_review:
        unknown_path = "data/outputs/adjectives_unknown_pt.csv"
        with open(unknown_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["lemma", "id_prompt", "modelo"])
            writer.writeheader()
            writer.writerows(unknown_for_review)
        logger.info(
            f"{len(unknown_for_review)} lemas PT sem entrada no SentiLex "
            f"(classificados como neutro) — salvos em {unknown_path}"
        )

    return results


def save_adjective_polarity(results: list[dict], logger):
    fields = ["id_prompt", "modelo", "idioma", "profissao", "genero", "cenario",
              "adjetivo", "lemma", "valencia"]
    with open(ADJECTIVE_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Polaridade adjetival salva: {ADJECTIVE_OUTPUT}")


# ---------------------------------------------------------------------------
# Carregamento das respostas coletadas
# ---------------------------------------------------------------------------

def load_responses(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Arquivo de respostas não encontrado: {path}\n"
            "Execute collect.py primeiro."
        )
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Análise PLN das respostas coletadas")
    parser.add_argument(
        "--input",
        default=INPUT_PATH,
        help=f"Caminho para o CSV de respostas (padrão: {INPUT_PATH})",
    )
    args = parser.parse_args()

    logger = setup_logger("analyze")

    for resource in ["corpora/sentiwordnet", "corpora/wordnet"]:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(resource.split("/")[1])

    rows = load_responses(args.input)
    logger.info(f"Respostas carregadas: {len(rows)}")

    valid_rows = [r for r in rows if not r["resposta"].startswith("ERRO:")]
    skipped = len(rows) - len(valid_rows)
    if skipped:
        logger.warning(f"{skipped} respostas com erro de coleta ignoradas na análise")

    pronoun_results = analyze_pronouns(valid_rows, logger)
    save_pronoun_counts(pronoun_results, logger)

    nlp_models = load_spacy_models(logger)
    sentilex = load_sentilex(SENTILEX_PATH, logger)
    adjective_results = analyze_adjectives(valid_rows, nlp_models, sentilex, logger)
    save_adjective_polarity(adjective_results, logger)

    logger.info("Análise concluída.")


if __name__ == "__main__":
    main()