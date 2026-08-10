"""
visualize.py: gera visualizações dos resultados da análise PLN.

Produz gráficos exportados como PNG em data/outputs/figures/:
  1. heatmap_razao_mf.png                — razão M/F por profissão e modelo
  2. barras_pronomes_<modelo>.png (×3)    — contagem M/F por profissão, um arquivo por modelo
  3. valência_genero_modelo.png          — distribuição de valência por gênero do prompt e modelo
  4. valência_categoria.png              — distribuição de valência por categoria de profissão e gênero

Uso:
    python src/visualize.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

PRONOUN_PATH   = "data/outputs/pronoun_counts.csv"
ADJECTIVE_PATH = "data/outputs/adjective_polarity.csv"
FIGURES_DIR    = Path("data/outputs/figures")

# Paleta neutra e legível para publicação acadêmica
PALETTE_VALENCIA = {
    "positivo": "#4C9BE8",
    "negativo": "#E8654C",
    "neutro":   "#B0B0B0",
}
PALETTE_GENERO = {
    "masc.": "#5B8DB8",
    "fem.":  "#C2678D",
}

# Ordem fixa para modelos e valências
MODEL_ORDER    = ["gpt-5.4-mini", "gemini-2.5-flash", "llama-3.3-70b"]
VALENCIA_ORDER = ["positivo", "neutro", "negativo"]
GENERO_ORDER   = ["masc.", "fem."]

# Nomes curtos para exibição nos gráficos
MODEL_LABELS = {
    "gpt-5.4-mini":    "GPT-5.4 mini",
    "gemini-2.5-flash":"Gemini 2.5 Flash",
    "llama-3.3-70b":   "LLaMA 3.3 70B",
}

# Abreviações das profissões para caber nos eixos
PROF_ABBREV = {
    "Desenvolvedor/a":                    "Desenvolvedor/a",
    "Médico/a":                           "Médico/a",
    "Engenheiro/a de Dados":              "Eng. de Dados",
    "Diretor/a":                          "Diretor/a",
    "CTO (Chief Technology Officer)":     "CTO",
    "Gerente":                            "Gerente",
    "Enfermeiro/a":                       "Enfermeiro/a",
    "Professor/a de Educação Infantil":   "Prof. Ed. Infantil",
    "Assistente Social":                  "Assist. Social",
}

CATEGORIA_MAP = {
    "Desenvolvedor/a":                  "Esp. Alta Renda",
    "Médico/a":                         "Esp. Alta Renda",
    "Engenheiro/a de Dados":            "Esp. Alta Renda",
    "Diretor/a":                        "Liderança",
    "CTO (Chief Technology Officer)":   "Liderança",
    "Gerente":                          "Liderança",
    "Enfermeiro/a":                     "Cuidado e Suporte",
    "Professor/a de Educação Infantil": "Cuidado e Suporte",
    "Assistente Social":                "Cuidado e Suporte",
}

# Tamanhos de fonte centralizados (fáceis de ajustar para o TCC)
FONT_SIZES = {
    "title":       15,
    "subtitle":    16,
    "axis_label":  12,
    "tick_label":  10.5,
    "panel_title": 13,
    "legend":      10.5,
    "legend_title":11.5,
    "annot":       10.5,
    "cbar_label":  11,
    "cbar_tick":   10,
}

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def setup():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams.update({
        "figure.dpi":      150,
        "savefig.dpi":     300,
        "savefig.bbox":    "tight",
        "font.family":     "sans-serif",
        "font.size":       FONT_SIZES["tick_label"],
        "axes.titlesize":  FONT_SIZES["panel_title"],
        "axes.labelsize":  FONT_SIZES["axis_label"],
        "xtick.labelsize": FONT_SIZES["tick_label"],
        "ytick.labelsize": FONT_SIZES["tick_label"],
        "legend.fontsize": FONT_SIZES["legend"],
        "legend.title_fontsize": FONT_SIZES["legend_title"],
        "figure.titlesize": FONT_SIZES["subtitle"],
    })


def load_data():
    pronouns = pd.read_csv(PRONOUN_PATH, encoding="utf-8")
    adjectives = pd.read_csv(ADJECTIVE_PATH, encoding="utf-8")

    # Normaliza nomes de profissão
    pronouns["profissao_abrev"]   = pronouns["profissao"].map(PROF_ABBREV).fillna(pronouns["profissao"])
    adjectives["profissao_abrev"] = adjectives["profissao"].map(PROF_ABBREV).fillna(adjectives["profissao"])
    adjectives["categoria"]       = adjectives["profissao"].map(CATEGORIA_MAP).fillna("Outro")

    # Normaliza labels de modelo
    pronouns["modelo_label"]   = pronouns["modelo"].map(MODEL_LABELS).fillna(pronouns["modelo"])
    adjectives["modelo_label"] = adjectives["modelo"].map(MODEL_LABELS).fillna(adjectives["modelo"])

    return pronouns, adjectives


def save(fig, filename: str):
    path = FIGURES_DIR / filename
    fig.savefig(path)
    plt.close(fig)
    print(f"Salvo: {path}")


# ---------------------------------------------------------------------------
# Gráfico 1 — Heatmap de razão M/F
# ---------------------------------------------------------------------------

def plot_heatmap(df: pd.DataFrame):
    """
    Heatmap: linhas = profissões, colunas = modelos, células = razão M/F.
    Razão > 1 → tendência masculina; < 1 → tendência feminina.
    N/A (fem=0) tratado como valor alto para destacar viés extremo.
    """
    # Substitui string "N/A (fem=0)" por valor sentinela alto
    df = df.copy()
    df["razao_mf"] = pd.to_numeric(df["razao_mf"], errors="coerce").fillna(15.0)

    pivot = df.pivot_table(
        index="profissao_abrev",
        columns="modelo_label",
        values="razao_mf",
        aggfunc="mean",
    )

    # Garante ordem das colunas
    col_order = [MODEL_LABELS[m] for m in MODEL_ORDER if MODEL_LABELS[m] in pivot.columns]
    pivot = pivot[col_order]

    fig, ax = plt.subplots(figsize=(9, 5.5))

    sns.heatmap(
        pivot,
        ax=ax,
        cmap="RdBu_r",
        center=1.0,
        annot=True,
        fmt=".2f",
        annot_kws={"size": FONT_SIZES["annot"]},
        linewidths=0.5,
        linecolor="#e0e0e0",
        cbar_kws={"label": "Razão M/F (>1 = tendência masc., <1 = tendência fem.)"},
    )

    ax.set_title("Razão Pronominal Masculino/Feminino por Profissão e Modelo",
                 pad=16, fontweight="bold", fontsize=FONT_SIZES["title"])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=15, labelsize=FONT_SIZES["tick_label"])
    ax.tick_params(axis="y", rotation=0, labelsize=FONT_SIZES["tick_label"])

    cbar = ax.collections[0].colorbar
    cbar.set_label("Razão M/F (>1 = tendência masc., <1 = tendência fem.)",
                   fontsize=FONT_SIZES["cbar_label"])
    cbar.ax.tick_params(labelsize=FONT_SIZES["cbar_tick"])

    save(fig, "heatmap_razao_mf.png")


# ---------------------------------------------------------------------------
# Gráfico 2 — Barras agrupadas: contagem M/F por profissão (grid em V)
# ---------------------------------------------------------------------------

def plot_pronoun_bars(df: pd.DataFrame):
    """
    Gera um arquivo separado por modelo (barras_pronomes_<modelo>.png),
    em vez de um único painel combinado — facilita a inclusão individual
    de cada gráfico no LaTeX.
    Barras lado a lado com count_masc e count_fem para cada profissão.
    """
    model_labels = [MODEL_LABELS[m] for m in MODEL_ORDER if MODEL_LABELS[m] in df["modelo_label"].unique()]

    # Slug simples para nome de arquivo (sem espaços/acentos problemáticos)
    SLUGS = {
        "GPT-5.4 mini":      "gpt",
        "Gemini 2.5 Flash":  "gemini",
        "LLaMA 3.3 70B":     "llama",
    }

    for label in model_labels:
        sub = df[df["modelo_label"] == label].copy()
        sub = sub.sort_values("profissao_abrev")

        x = range(len(sub))
        width = 0.38

        fig, ax = plt.subplots(figsize=(8, 5.5))

        ax.bar(
            [i - width / 2 for i in x], sub["count_masc"],
            width=width, color=PALETTE_GENERO["masc."], label="Masculino", alpha=0.9
        )
        ax.bar(
            [i + width / 2 for i in x], sub["count_fem"],
            width=width, color=PALETTE_GENERO["fem."], label="Feminino", alpha=0.9
        )

        ax.set_xticks(list(x))
        ax.set_xticklabels(sub["profissao_abrev"], rotation=45, ha="right",
                            fontsize=FONT_SIZES["tick_label"])
        ax.set_title(f"Frequência de Pronomes por Profissão — {label}",
                     fontweight="bold", fontsize=FONT_SIZES["title"])
        ax.set_ylabel("Nº de pronomes", fontsize=FONT_SIZES["axis_label"])
        ax.tick_params(axis="y", labelsize=FONT_SIZES["tick_label"])
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.legend(fontsize=FONT_SIZES["legend"])

        plt.tight_layout()

        slug = SLUGS.get(label, label.lower().replace(" ", "_"))
        save(fig, f"barras_pronomes_{slug}.png")


# ---------------------------------------------------------------------------
# Gráfico 3 — Valência por gênero do prompt e modelo
# ---------------------------------------------------------------------------

def plot_valence_by_gender(df: pd.DataFrame):
    """
    Apenas prompts em PT (têm variação de gênero).
    Barras empilhadas 100%: eixo x = gênero do prompt, painel = modelo.
    """
    pt = df[(df["idioma"] == "PT") & (df["genero"].isin(["masc.", "fem."]))].copy()

    model_labels = [MODEL_LABELS[m] for m in MODEL_ORDER if MODEL_LABELS[m] in pt["modelo_label"].unique()]
    fig, axes = plt.subplots(1, len(model_labels), figsize=(12, 5.5), sharey=True)

    for ax, label in zip(axes, model_labels):
        sub = pt[pt["modelo_label"] == label]

        # Proporção de cada valência por gênero
        counts = (
            sub.groupby(["genero", "valencia"])
            .size()
            .reset_index(name="n")
        )
        totals = counts.groupby("genero")["n"].transform("sum")
        counts["pct"] = counts["n"] / totals * 100

        pivot = counts.pivot_table(
            index="genero", columns="valencia", values="pct", aggfunc="sum"
        ).reindex(index=GENERO_ORDER, columns=VALENCIA_ORDER, fill_value=0)

        bottom = [0] * len(pivot)
        for valencia in VALENCIA_ORDER:
            vals = pivot[valencia].values if valencia in pivot.columns else [0] * len(pivot)
            ax.bar(pivot.index, vals, bottom=bottom,
                   color=PALETTE_VALENCIA[valencia], label=valencia.capitalize(), alpha=0.9)
            bottom = [b + v for b, v in zip(bottom, vals)]

        ax.set_title(label, fontweight="bold", fontsize=FONT_SIZES["panel_title"])
        ax.set_xlabel("Gênero do prompt", fontsize=FONT_SIZES["axis_label"])
        ax.set_ylabel("% de adjetivos" if ax == axes[0] else "", fontsize=FONT_SIZES["axis_label"])
        ax.set_ylim(0, 100)
        ax.tick_params(axis="both", labelsize=FONT_SIZES["tick_label"])
        ax.yaxis.set_major_formatter(mticker.PercentFormatter())

        if ax == axes[-1]:
            handles = [plt.Rectangle((0, 0), 1, 1, color=PALETTE_VALENCIA[v]) for v in VALENCIA_ORDER]
            ax.legend(handles, [v.capitalize() for v in VALENCIA_ORDER],
                      title="Valência", fontsize=FONT_SIZES["legend"],
                      title_fontsize=FONT_SIZES["legend_title"], loc="upper right")

    fig.suptitle("Distribuição de Valência Adjetival por Gênero do Prompt (PT)",
                 fontweight="bold", fontsize=FONT_SIZES["subtitle"], y=1.03)
    plt.tight_layout()

    save(fig, "valencia_genero_modelo.png")


# ---------------------------------------------------------------------------
# Gráfico 4 — Valência por categoria de profissão e gênero
# ---------------------------------------------------------------------------

def plot_valence_by_category(df: pd.DataFrame):
    """
    Apenas prompts em PT. Agrupa por categoria × gênero × valencia.
    Painel por categoria; barras lado a lado por gênero; empilhadas por valência.
    """
    pt = df[(df["idioma"] == "PT") & (df["genero"].isin(["masc.", "fem."]))].copy()
    categorias = ["Esp. Alta Renda", "Liderança", "Cuidado e Suporte"]

    fig, axes = plt.subplots(1, 3, figsize=(13, 5.5), sharey=True)

    for ax, cat in zip(axes, categorias):
        sub = pt[pt["categoria"] == cat]

        counts = (
            sub.groupby(["genero", "valencia"])
            .size()
            .reset_index(name="n")
        )
        totals = counts.groupby("genero")["n"].transform("sum")
        counts["pct"] = counts["n"] / totals * 100

        pivot = counts.pivot_table(
            index="genero", columns="valencia", values="pct", aggfunc="sum"
        ).reindex(index=GENERO_ORDER, columns=VALENCIA_ORDER, fill_value=0)

        bottom = [0] * len(pivot)
        for valencia in VALENCIA_ORDER:
            vals = pivot[valencia].values if valencia in pivot.columns else [0] * len(pivot)
            ax.bar(pivot.index, vals, bottom=bottom,
                   color=PALETTE_VALENCIA[valencia], label=valencia.capitalize(), alpha=0.9)
            bottom = [b + v for b, v in zip(bottom, vals)]

        ax.set_title(cat, fontweight="bold", fontsize=FONT_SIZES["panel_title"])
        ax.set_xlabel("Gênero do prompt", fontsize=FONT_SIZES["axis_label"])
        ax.set_ylabel("% de adjetivos" if ax == axes[0] else "", fontsize=FONT_SIZES["axis_label"])
        ax.set_ylim(0, 100)
        ax.tick_params(axis="both", labelsize=FONT_SIZES["tick_label"])
        ax.yaxis.set_major_formatter(mticker.PercentFormatter())

    handles = [plt.Rectangle((0, 0), 1, 1, color=PALETTE_VALENCIA[v]) for v in VALENCIA_ORDER]
    fig.legend(handles, [v.capitalize() for v in VALENCIA_ORDER],
               title="Valência", fontsize=FONT_SIZES["legend"],
               title_fontsize=FONT_SIZES["legend_title"],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.1))

    fig.suptitle("Valência Adjetival por Categoria de Profissão e Gênero do Prompt (PT)",
                 fontweight="bold", fontsize=FONT_SIZES["subtitle"], y=1.03)
    plt.tight_layout()

    save(fig, "valencia_categoria.png")


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main():
    setup()
    pronouns, adjectives = load_data()

    print("Gerando gráfico 1: heatmap de razão M/F...")
    plot_heatmap(pronouns)

    print("Gerando gráficos 2: barras de pronomes (um arquivo por modelo)...")
    plot_pronoun_bars(pronouns)

    print("Gerando gráfico 3: valência por gênero e modelo...")
    plot_valence_by_gender(adjectives)

    print("Gerando gráfico 4: valência por categoria...")
    plot_valence_by_category(adjectives)

    print(f"\nConcluído. Figuras em: {FIGURES_DIR.resolve()}")


if __name__ == "__main__":
    main()