"""
collect.py: envia o dataset de prompts às APIs dos modelos e salva as respostas.

Uso:
    python collect.py --model gpt
    python collect.py --model gemini
    python collect.py --model llama
    python collect.py --model all

Variáveis de ambiente necessárias (dependem do modelo escolhido):
    OPENAI_API_KEY   → gpt
    GOOGLE_API_KEY   → gemini
    GROQ_API_KEY     → llama
"""

import argparse
import datetime
import time
import requests

from utils import load_prompts, get_api_key, with_retry, CSVWriter, setup_logger

# ---------------------------------------------------------------------------
# Configuração dos modelos
# ---------------------------------------------------------------------------

MODELS = {
    "gpt": {
        "name": "gpt-5.4-mini",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "build_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        "build_body": lambda prompt: {
            "model": "gpt-5.4-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_completion_tokens": 900,
        },
        "extract_text": lambda r: r["choices"][0]["message"]["content"],
        "extract_tokens": lambda r: r["usage"]["completion_tokens"],
        "delay": 0.5,
    },
    "gemini": {
        "name": "gemini-2.5-flash",
        "endpoint": (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent"
        ),
        "build_headers": lambda key: {
            "Content-Type": "application/json",
        },
        "build_body": lambda prompt: {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000,
            }
        },
        "extract_text": lambda r: r["candidates"][0]["content"]["parts"][0]["text"],
        "extract_tokens": lambda r: r.get("usageMetadata", {}).get("candidatesTokenCount", -1),
        "delay": 8.0,
    },
    "llama": {
        "name": "llama-3.3-70b",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "build_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        "build_body": lambda prompt: {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 900,
        },
        "extract_text": lambda r: r["choices"][0]["message"]["content"],
        "extract_tokens": lambda r: r["usage"]["completion_tokens"],
        "delay": 0.5,
    },
}

OUTPUT_FIELDS = [
    "id_prompt", "modelo", "idioma", "categoria",
    "profissao", "genero", "cenario", "resposta",
    "tokens_gerados", "timestamp",
]

DATASET_PATH = "data/raw/dataset_prompts.csv"
OUTPUT_PATH = "data/outputs/responses.csv"

# ---------------------------------------------------------------------------
# Coleta para um modelo
# ---------------------------------------------------------------------------

def collect_model(alias: str, prompts: list[dict], logger):
    config = MODELS[alias]
    api_key = get_api_key(alias)
    model_name = config["name"]

    logger.info(f"Iniciando coleta: {model_name} ({len(prompts)} prompts)")

    with CSVWriter(OUTPUT_PATH, OUTPUT_FIELDS) as writer:
        for row in prompts:
            prompt_id = row["ID"]
            prompt_text = row["Prompt"]

            def call_api():
                headers = config["build_headers"](api_key)
                body = config["build_body"](prompt_text)
                params = {"key": api_key} if alias == "gemini" else {}
                resp = requests.post(config["endpoint"], headers=headers, json=body, params=params, timeout=60)
                resp.raise_for_status()
                return resp.json()

            try:
                result = with_retry(call_api, max_attempts=3, base_delay=2.0, logger=logger)
                text = config["extract_text"](result)
                tokens = config["extract_tokens"](result)
                status = "ok"
            except Exception as exc:
                logger.error(f"Prompt {prompt_id} falhou definitivamente: {exc}")
                text = f"ERRO: {exc}"
                tokens = -1
                status = "erro"

            writer.write({
                "id_prompt":      prompt_id,
                "modelo":         model_name,
                "idioma":         row["Idioma"],
                "categoria":      row["Categoria"],
                "profissao":      row["Profissão"],
                "genero":         row["Gênero"],
                "cenario":        row["Cenário"],
                "resposta":       text,
                "tokens_gerados": tokens,
                "timestamp":      datetime.datetime.utcnow().isoformat(),
            })

            logger.info(f"[{model_name}] Prompt {prompt_id} — {status} ({tokens} tokens)")

            # Pausa mínima entre chamadas para evitar rate limit
            time.sleep(config["delay"])

    logger.info(f"Coleta concluída para {model_name}. Saída: {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Coleta de respostas dos LLMs")
    parser.add_argument(
        "--model",
        choices=["gpt", "gemini", "llama", "all"],
        required=True,
        help="Modelo a usar na coleta (ou 'all' para todos os três)",
    )
    args = parser.parse_args()

    logger = setup_logger("collect")
    prompts = load_prompts(DATASET_PATH)

    targets = list(MODELS.keys()) if args.model == "all" else [args.model]

    for alias in targets:
        collect_model(alias, prompts, logger)


if __name__ == "__main__":
    main()