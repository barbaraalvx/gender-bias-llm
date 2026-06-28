"""
prepare_sentilex.py: filtra o SentiLex-lem-PT02.txt mantendo apenas adjetivos.

Entrada:  lexicons/SentiLex/SentiLex-lem-PT02.txt   (arquivo original baixado)
Saída:    lexicons/SentiLex-PT02-Adj.txt   (lido por analyze.py)

Uso:
    python src/prepare_sentilex.py
"""

from pathlib import Path

INPUT  = Path("lexicons/SentiLex/SentiLex-lem-PT02.txt")
OUTPUT = Path("lexicons/SentiLex-PT02-Adj.txt")


def main():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {INPUT}\n"
            "Baixe o SentiLex-lem-PT02.txt e coloque em lexicons/."
        )

    with open(INPUT, encoding="utf-8") as f:
        linhas = f.readlines()

    linhas_adjetivos = [l for l in linhas if "PoS=Adj" in l]

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.writelines(linhas_adjetivos)

    print(f"Concluído. {len(linhas_adjetivos)} adjetivos salvos em {OUTPUT}")


if __name__ == "__main__":
    main()