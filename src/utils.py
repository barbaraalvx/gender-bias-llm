"""
utils.py: funções compartilhadas entre collect.py e analyze.py.
"""

import csv
import os
import time
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ---------------------------------------------------------------------------
# Leitura do dataset
# ---------------------------------------------------------------------------

def load_prompts(csv_path: str) -> list[dict]:
    """Lê o dataset de prompts e devolve uma lista de dicionários."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {csv_path}")

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("Dataset vazio.")

    return rows


# ---------------------------------------------------------------------------
# Chaves de API
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "gpt":    "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "llama":  "GROQ_API_KEY",
}

def get_api_key(model_alias: str) -> str:
    """Lê a chave de API do ambiente. Lança erro se ausente."""
    env_var = REQUIRED_KEYS[model_alias]
    key = os.environ.get(env_var)
    if not key:
        raise EnvironmentError(
            f"Variável de ambiente {env_var} não definida. "
            f"Execute: export {env_var}=sua_chave"
        )
    return key


# ---------------------------------------------------------------------------
# Retry com backoff exponencial
# ---------------------------------------------------------------------------

def with_retry(fn, max_attempts: int = 3, base_delay: float = 2.0, logger=None):
    """
    Chama fn() com até max_attempts tentativas.
    O intervalo entre tentativas dobra a cada falha (backoff exponencial).
    """
    log = logger or logging.getLogger(__name__)
    last_exc = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            log.warning(f"Tentativa {attempt} falhou: {exc}. Aguardando {delay:.1f}s...")
            time.sleep(delay)

    raise RuntimeError(f"Todas as {max_attempts} tentativas falharam. Último erro: {last_exc}")


# ---------------------------------------------------------------------------
# Escrita incremental de CSV
# ---------------------------------------------------------------------------

class CSVWriter:
    """
    Abre (ou cria) um CSV de saída e permite adicionar linhas uma a uma.
    Útil para salvar respostas imediatamente após a coleta,
    sem acumular tudo em memória.
    """

    def __init__(self, path: str, fieldnames: list[str]):
        self.path = Path(path)
        self.fieldnames = fieldnames
        self._file = None
        self._writer = None
        self._open()

    def _open(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists()
        self._file = open(self.path, "a", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=self.fieldnames)
        if write_header:
            self._writer.writeheader()

    def write(self, row: dict):
        self._writer.writerow(row)
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()