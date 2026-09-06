"""
callbacks.py — Registro e lógica de callbacks do dashboard.
Observatório da Gestão Municipal do Saneamento: Maturidade da gestão municipal (observado versus esperado).
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, Input, Output, State, no_update

from .data_loader import (
    load_geojson,
    get_municipality_options,
    get_uf_options,
    get_regiao_options,
    get_analytical_columns,
    friendly,
    DIMENSOES_GOVERNANCA,
    DIMENSOES_INSTITUCIONAIS,
    DIMENSOES_SERVICOS,
    ROTULOS_DIMENSOES,
)
from .components import (
    COLORS,
    CLASS_COLORS,
    REGION_COLORS,
    PLOTLY_THEME,
    create_metric_card,
    create_classification_badge,
    create_bullet_chart,
    create_governance_section,
    create_socioeconomic_section,
    create_about_tab_content,
    create_empty_state,
    create_methodological_note,
    create_chart_container,
    get_classification_theme,
)

logger = logging.getLogger(__name__)

# GeoJSON carregado uma única vez em memória para o mapa coroplético offline
GEOJSON_BRAZIL = load_geojson()

MAP_METRICS = {
    "media_indice": ("Índice Médio de Maturidade", "Índice médio observado (0 a 8)", "Teal"),
    "media_previsto": ("Índice Previsto Médio", "Estimativa média esperada pelo modelo", "Teal"),
    "media_residuo": ("Resíduo Médio", "Diferença média (Observado − Previsto)", "RdBu"),
    "pct_acima": ("% Acima do Esperado", "Percentual de municípios acima do previsto", "Greens"),
    "pct_abaixo": ("% Abaixo do Esperado", "Percentual de municípios abaixo do previsto", "Reds"),
    "n_com_dados": ("Municípios com Dados", "Quantidade de municípios com registro válido", "Blues"),
}


# ──────────────────────────────────────────────────────────────────────────────
# LAYOUTS DAS ABAS
# ──────────────────────────────────────────────────────────────────────────────
def create_consult_layout(df: pd.DataFrame):
    """Layout da aba Consulta Municipal."""
    options = get_municipality_options(df)
    return html.Div([
        html.Div([
            html.Div([
                html.Span("CONSULTA INDIVIDUALIZADA", className="section-eyebrow"),
                html.H2("Perfil de Gestão do Município", className="page-title"),
                html.P(
                    "Pesquise um município brasileiro por nome ou selecione para avaliar o índice de maturidade "
                    "observado, a estimativa esperada pelo modelo, os dados socioeconômicos e as 8 dimensões de governança.",
                    className="page-subtitle",
                ),
            ], className="page-header-content"),
        ], className="page-header-wrapper"),

        # Barra de Busca com Autocomplete
        html.Div([
            html.Div([
                html.Label("Pesquisar Município (digite o nome ou UF):", className="input-label"),
                dcc.Dropdown(
                    id="city-search",
                    options=options,
                    placeholder="Ex: Recife, Belo Horizonte, Campinas, Palmas...",
                    searchable=True,
                    clearable=True,
                    className="search-dropdown",
                ),
            ], className="search-bar-box"),
        ], className="search-container container"),

        # Área de Conteúdo Dinâmico do Município
        html.Div(id="city-output", className="container"),
    ], className="tab-page tab-page-consult")


def create_geo_layout(df: pd.DataFrame):
    """Layout da aba Panorama Territorial."""
    return html.Div([
        html.Div([
            html.Div([
                html.Span("VISÃO TERRITORIAL AGREGADA", className="section-eyebrow"),
                html.H2("Panorama Territorial", className="page-title"),
                html.P(
                    "Explore o comportamento da governança e as classificações de gestão por nível territorial: "
                    "Brasil consolidado, grandes regiões e estados (UFs).",
                    className="page-subtitle",
                ),
            ], className="page-header-content"),
        ], className="page-header-wrapper page-header-geo"),

        # Controles Territoriais
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Nível Territorial", className="control-label"),
                    dcc.RadioItems(
                        id="geo-level",
                        options=[
                            {"label": " Brasil", "value": "brasil"},
                            {"label": " Região", "value": "regiao"},
                            {"label": " Estado (UF)", "value": "estado"},
                        ],
                        value="brasil",
                        inline=True,
                        className="radio-group-institutional",
                    ),
                ], className="control-cell"),

                html.Div([
                    html.Label("Filtrar Região", className="control-label"),
                    dcc.Dropdown(
                        id="geo-regiao",
                        options=[{"label": r, "value": r} for r in get_regiao_options(df)],
                        placeholder="Todas as regiões",
                        clearable=True,
                        className="control-dropdown",
                    ),
                ], className="control-cell", id="geo-regiao-cell"),

                html.Div([
                    html.Label("Filtrar Estado (UF)", className="control-label"),
                    dcc.Dropdown(
                        id="geo-uf",
                        options=[{"label": u, "value": u} for u in get_uf_options(df)],
                        placeholder="Selecione o estado",
                        clearable=True,
                        className="control-dropdown",
                    ),
                ], className="control-cell", id="geo-uf-cell"),

                html.Div([
                    html.Label("Métrica do Mapa Coroplético", className="control-label"),
                    dcc.Dropdown(
                        id="geo-map-metric",
                        options=[{"label": v[0], "value": k} for k, v in MAP_METRICS.items()],
                        value="media_indice",
                        clearable=False,
                        className="control-dropdown",
                    ),
                ], className="control-cell", id="geo-metric-cell"),
            ], className="controls-grid"),
        ], className="controls-card container"),

        # Conteúdo Dinâmico Territorial
        html.Div(id="geo-content", className="container"),
    ], className="tab-page tab-page-geo")


def create_explore_layout(df: pd.DataFrame):
    """Layout da aba Explorar Dados."""
    catalog = get_analytical_columns(df)
    dropdown_options = []
    for group_name, vars_dict in catalog.items():
        dropdown_options.append({"label": f"─── {group_name.upper()} ───", "value": "DISABLED", "disabled": True})
        for var_col, var_label in vars_dict.items():
            dropdown_options.append({"label": var_label, "value": var_col})

    chart_types = [
        {"label": "Gráfico de Dispersão (Scatter)", "value": "scatter"},
        {"label": "Gráfico de Barras Agrupadas", "value": "bar"},
        {"label": "Diagrama de Caixas (Boxplot)", "value": "box"},
        {"label": "Histograma de Distribuição", "value": "histogram"},
    ]

    color_options = [
        {"label": "Classificação de Gestão", "value": "classificacao_gestao"},
        {"label": "Grande Região", "value": "Região"},
        {"label": "Estado (UF)", "value": "UF"},
        {"label": "Sem coloração agrupada", "value": "none"},
    ]

    return html.Div([
        html.Div([
            html.Div([
                html.Span("EXPLORAÇÃO ANALÍTICA LIVRE", className="section-eyebrow"),
                html.H2("Explorador Visual de Dados", className="page-title"),
                html.P(
                    "Cruze livremente variáveis do modelo e do perfil socioeconômico municipal com tipologias "
                    "estatísticas padronizadas e controle de ausência de dados.",
                    className="page-subtitle",
                ),
            ], className="page-header-content"),
        ], className="page-header-wrapper"),

        # Painel de Seleção de Variáveis e Filtros
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Eixo Horizontal (X):", className="control-label"),
                    dcc.Dropdown(
                        id="explore-x",
                        options=dropdown_options,
                        value="receita_per_capita",
                        clearable=False,
                        className="control-dropdown",
                    ),
                ], className="control-cell"),

                html.Div([
                    html.Label("Eixo Vertical (Y):", className="control-label"),
                    dcc.Dropdown(
                        id="explore-y",
                        options=dropdown_options,
                        value="indice_maturidade_saneamento",
                        clearable=False,
                        className="control-dropdown",
                    ),
                ], className="control-cell"),

                html.Div([
                    html.Label("Colorir / Agrupar por:", className="control-label"),
                    dcc.Dropdown(
                        id="explore-color",
                        options=color_options,
                        value="classificacao_gestao",
                        clearable=False,
                        className="control-dropdown",
                    ),
                ], className="control-cell"),

                html.Div([
                    html.Label("Tipo de Gráfico:", className="control-label"),
                    dcc.Dropdown(
                        id="explore-chart-type",
                        options=chart_types,
                        value="scatter",
                        clearable=False,
                        className="control-dropdown",
                    ),
                ], className="control-cell"),
            ], className="controls-grid"),

            # Linha Secundária de Filtros do Explorador
            html.Div([
                html.Div([
                    html.Label("Filtrar por Região:", className="filter-mini-label"),
                    dcc.Dropdown(
                        id="explore-regiao-filter",
                        options=[{"label": r, "value": r} for r in get_regiao_options(df)],
                        multi=True,
                        placeholder="Todas as regiões",
                        className="control-dropdown-mini",
                    ),
                ], className="filter-cell"),

                html.Div([
                    html.Label("Filtrar por UF:", className="filter-mini-label"),
                    dcc.Dropdown(
                        id="explore-uf-filter",
                        options=[{"label": u, "value": u} for u in get_uf_options(df)],
                        multi=True,
                        placeholder="Todos os estados",
                        className="control-dropdown-mini",
                    ),
                ], className="filter-cell"),

                html.Div([
                    html.Label("Filtrar por Classificação:", className="filter-mini-label"),
                    dcc.Dropdown(
                        id="explore-class-filter",
                        options=[
                            {"label": c.replace("Maturidade ", ""), "value": c}
                            for c in sorted(df["classificacao_gestao"].dropna().unique())
                        ],
                        multi=True,
                        placeholder="Todas as classificações",
                        className="control-dropdown-mini",
                    ),
                ], className="filter-cell"),
            ], className="explore-subfilters-row"),
        ], className="controls-card container"),

        # Área de Avisos e Gráfico
        html.Div([
            html.Div(id="explore-note-area"),
            html.Div(id="explore-chart-area", className="explore-graph-wrapper"),
        ], className="container"),
    ], className="tab-page tab-page-explore")


# ──────────────────────────────────────────────────────────────────────────────
# REGISTRO PRINCIPAL DE CALLBACKS
# ──────────────────────────────────────────────────────────────────────────────
def register_callbacks(app, df: pd.DataFrame):
    """Registra todos os callbacks do Dash vinculados ao app e ao DataFrame."""

    @app.callback(
        Output("dataset-download", "data"),
        Input("dataset-download-link", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_consolidated_dataset(_n_clicks):
        return dcc.send_data_frame(
            df.to_csv,
            "dataset_final_consolidado.csv",
            index=False,
            encoding="utf-8-sig",
        )

    # 1. Roteamento de Abas
    @app.callback(
        Output("content", "children"),
        Input("tabs", "value"),
    )
    def render_tab_content(tab_value):
        if tab_value == "about":
            return create_about_tab_content()
        elif tab_value == "consult":
            return create_consult_layout(df)
        elif tab_value == "geo":
            return create_geo_layout(df)
        elif tab_value == "explore":
            return create_explore_layout(df)
        return create_about_tab_content()

    # 2. Consulta Municipal: Exibição do Perfil do Município
    @app.callback(
        Output("city-output", "children"),
        Input("city-search", "value"),
    )
    def update_city_profile(selected_ibge):
        if not selected_ibge:
            return create_empty_state(
                "Explore um Município",
                "Pesquise pelo nome de uma cidade para visualizar sua maturidade de gestão em saneamento, "
                "a estimativa esperada pelo modelo, o contexto socioeconômico e as dimensões de governança.",
                "Selecione um município no campo de busca acima"
            )

        match = df[df["codigo_ibge_str"] == str(selected_ibge).strip()]
        if match.empty:
            return create_empty_state(
                "Município Não Localizado",
                "Nenhum registro correspondente foi encontrado para o identificador informado.",
                "Verifique a ortografia ou escolha outro município na lista"
            )

        row = match.iloc[0]
        nome = row.get("Município", "—")
        uf = row.get("UF", "—")
        regiao = row.get("Região", "—")
        cod_ibge = row.get("codigo_ibge_str", "—")
        idx_obs = row.get("indice_maturidade_saneamento")
        previsto = row.get("previsto_oof")
        residuo = row.get("residuo_oof")
        classificacao = row.get("classificacao_gestao", "Sem dados suficientes")

        # Tema visual correspondente à classificação (azul, verde, vermelho ou neutro)
        theme = get_classification_theme(classificacao)

        # Cabeçalho do Perfil com cor correspondente à sua classificação
        header = html.Div([
            html.Div([
                html.Div([
                    html.H2(nome, className="city-title"),
                    html.Span(f"{uf} · Região {regiao}", className="city-subtitle"),
                    html.Span(f"Código IBGE: {cod_ibge}", className="city-ibge-badge"),
                ], className="city-title-group"),
                create_classification_badge(classificacao),
            ], className="city-header-inner"),
        ], className=f"city-profile-header card-panel {theme['header_class']}")

        # Indicadores Principais do Modelo
        obs_val_str = f"{idx_obs:.1f}" if pd.notna(idx_obs) else "Sem dados"
        prev_val_str = f"{previsto:.1f}" if pd.notna(previsto) else "Sem dados"
        res_val_str = f"{residuo:+.2f}" if pd.notna(residuo) else "Sem dados"

        res_color = None
        if pd.notna(residuo):
            if residuo > 0.05:
                res_color = COLORS["teal_primary"]
            elif residuo < -0.05:
                res_color = COLORS["highlight_terracotta"]

        model_cards = html.Div([
            create_metric_card(
                "Classificação Comparativa",
                classificacao.replace("Maturidade ", ""),
                detail="Avaliação relativa ao modelo estatístico",
                value_color=theme["color"],
                card_class=theme["metric_class"],
            ),
            create_metric_card(
                "Índice Observado",
                obs_val_str,
                detail="Maturidade reportada (0 a 8 dimensões)",
                value_color=COLORS["teal_dark"],
            ),
            create_metric_card(
                "Índice Esperado (Modelo)",
                prev_val_str,
                detail="Estimativa segundo perfil socioeconômico",
                value_color=COLORS["blue_dark"],
            ),
            create_metric_card(
                "Resíduo Analítico",
                res_val_str,
                detail="Diferença: Observado − Esperado",
                value_color=res_color,
            ),
        ], className="grid-cards-4")

        # Bullet Chart de Comparação Observado vs. Esperado
        bullet_chart_box = create_bullet_chart(idx_obs, previsto, nome)

        # Contexto Socioeconômico
        socio_section = create_socioeconomic_section(row)

        # 8 Dimensões de Governança
        gov_section = create_governance_section(row)

        # Nota metodológica de rodapé do perfil
        footer_note = create_methodological_note(
            "A classificação de gestão é comparativa e expressa o distanciamento estatístico em relação ao valor "
            "esperado pelo modelo de Machine Learning. Não constitui julgamento absoluto sobre a eficácia da administração.",
            strong_prefix="Nota sobre a Classificação:"
        )

        return html.Div([
            header,
            model_cards,
            bullet_chart_box,
            socio_section,
            gov_section,
            footer_note,
        ], className="city-profile-content")

    # 3. Panorama Territorial: Filtro Dinâmico de UFs por Região
    @app.callback(
        Output("geo-uf", "options"),
        Input("geo-regiao", "value"),
    )
    def sync_geo_uf_options(selected_regiao):
        ufs = get_uf_options(df, selected_regiao)
        return [{"label": u, "value": u} for u in ufs]

    # 4. Panorama Territorial: Visibilidade dos Filtros Conforme o Nível
    @app.callback(
        Output("geo-regiao-cell", "style"),
        Output("geo-uf-cell", "style"),
        Output("geo-metric-cell", "style"),
        Input("geo-level", "value"),
    )
    def update_geo_controls_visibility(level):
        if level == "brasil":
            return {"display": "none"}, {"display": "none"}, {"display": "block"}
        elif level == "regiao":
            return {"display": "block"}, {"display": "none"}, {"display": "none"}
        else:  # estado
            return {"display": "block"}, {"display": "block"}, {"display": "none"}

    # 5. Panorama Territorial: Renderização Principal de Indicadores e Gráficos
    @app.callback(
        Output("geo-content", "children"),
        Input("geo-level", "value"),
        Input("geo-regiao", "value"),
        Input("geo-uf", "value"),
        Input("geo-map-metric", "value"),
    )
    def render_territorial_view(level, regiao, uf, map_metric):
        if df.empty:
            return create_empty_state("Base de Dados Indisponível", "Não foram carregados dados para esta visão.")

        sub = df.copy()

        # Filtragem estrita conforme o nível
        if level == "brasil":
            scope_label = "Brasil (Consolidado Nacional)"
            territory_name = "Brasil"
        elif level == "regiao":
            if regiao:
                sub = sub[sub["Região"] == regiao]
                scope_label = f"Região {regiao}"
                territory_name = regiao
            else:
                scope_label = "Todas as Regiões (Nacional)"
                territory_name = "Brasil"
        else:  # estado
            if uf:
                sub = sub[sub["UF"] == uf]
                scope_label = f"Estado de {uf}"
                territory_name = uf
            elif regiao:
                sub = sub[sub["Região"] == regiao]
                scope_label = f"Todos os Estados da Região {regiao}"
                territory_name = regiao
            else:
                scope_label = "Todos os Estados (Nacional)"
                territory_name = "Brasil"

        if sub.empty:
            return create_empty_state(
                "Nenhum Município Encontrado",
                "Os filtros territoriais selecionados não retornaram municípios.",
                "Altere a seleção de região ou estado"
            )

        # ─── CÁLCULOS RIGOROSOS DE MÉTRICAS TERRITORIAIS (SEM TRATAR NAN COMO ZERO) ───
        total_municipios = len(sub)
        subset_dados = sub.dropna(subset=["indice_maturidade_saneamento"])
        n_com_dados = len(subset_dados)

        media_obs = subset_dados["indice_maturidade_saneamento"].mean() if n_com_dados > 0 else np.nan
        media_prev = subset_dados["previsto_oof"].mean() if n_com_dados > 0 else np.nan
        media_res = subset_dados["residuo_oof"].mean() if n_com_dados > 0 else np.nan

        # Percentuais baseados apenas em municípios com dados válidos
        acima_count = (subset_dados["classificacao_gestao"] == "Maturidade acima do esperado").sum()
        abaixo_count = (subset_dados["classificacao_gestao"] == "Maturidade abaixo do esperado").sum()
        dentro_count = (subset_dados["classificacao_gestao"] == "Maturidade dentro do esperado").sum()

        pct_acima = (acima_count / n_com_dados * 100) if n_com_dados > 0 else 0.0
        pct_abaixo = (abaixo_count / n_com_dados * 100) if n_com_dados > 0 else 0.0
        pct_cobertura = (n_com_dados / total_municipios * 100) if total_municipios > 0 else 0.0

        # Cards de Resumo Territorial
        cards_summary = html.Div([
            create_metric_card(
                "Total de Municípios",
                f"{total_municipios:,}".replace(",", "."),
                detail=f"{scope_label}",
            ),
            create_metric_card(
                "Municípios com Dados",
                f"{n_com_dados:,}".replace(",", "."),
                detail=f"{pct_cobertura:.1f}% de cobertura da base",
                value_color=COLORS["blue_primary"],
            ),
            create_metric_card(
                "Maturidade Média",
                f"{media_obs:.2f}" if pd.notna(media_obs) else "—",
                detail="Média do índice observado (0 a 8)",
                value_color=COLORS["teal_dark"],
            ),
            create_metric_card(
                "Previsto Médio",
                f"{media_prev:.2f}" if pd.notna(media_prev) else "—",
                detail="Estimativa média do modelo",
                value_color=COLORS["blue_dark"],
            ),
            create_metric_card(
                "Resíduo Médio",
                f"{media_res:+.2f}" if pd.notna(media_res) else "—",
                detail="Diferença média (obs. − previsto)",
                value_color=COLORS["teal_primary"] if pd.notna(media_res) and media_res >= 0 else COLORS["highlight_terracotta"],
            ),
            create_metric_card(
                "% Acima do Esperado",
                f"{pct_acima:.1f}%",
                detail=f"{acima_count} cidades com resíduo positivo",
                value_color=CLASS_COLORS["Maturidade acima do esperado"],
            ),
            create_metric_card(
                "% Abaixo do Esperado",
                f"{pct_abaixo:.1f}%",
                detail=f"{abaixo_count} cidades com resíduo negativo",
                value_color=CLASS_COLORS["Maturidade abaixo do esperado"],
            ),
        ], className="grid-summary-strip")

        # Seções adicionais recolhíveis de governança, calculadas no recorte atual
        classificados = sub[sub["classificacao_gestao"] != "Sem dados suficientes"]
        n_classificados = len(classificados)

        def percentual_sim(coluna):
            if coluna not in classificados.columns or n_classificados == 0:
                return None
            return (classificados[coluna] == "Sim").sum() / n_classificados * 100

        def percentual_formatado(valor):
            return f"{valor:.1f}%" if valor is not None else "—"

        def investimento_formatado(valor):
            if pd.isna(valor):
                return "—"
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        percentual_dimensoes = [
            ("Plano de Saneamento Básico", percentual_sim(DIMENSOES_GOVERNANCA["plano_saneamento"]), COLORS["teal_dark"]),
            ("Plano Municipal de Gestão Integrada de Resíduos Sólidos", percentual_sim(DIMENSOES_GOVERNANCA["pmgirs"]), COLORS["teal_dark"]),
            ("Regulação de Água", percentual_sim(DIMENSOES_INSTITUCIONAIS["regulacao_agua"]), COLORS["teal_dark"]),
            ("Regulação de Esgoto", percentual_sim(DIMENSOES_INSTITUCIONAIS["regulacao_esgoto"]), COLORS["teal_dark"]),
            ("Ouvidoria", percentual_sim(DIMENSOES_GOVERNANCA["ouvidoria"]), COLORS["teal_dark"]),
            ("Conselho Específico de Saneamento", percentual_sim(DIMENSOES_GOVERNANCA["conselho_especifico"]), COLORS["teal_dark"]),
            ("Participação em Consórcio Público", percentual_sim(DIMENSOES_INSTITUCIONAIS["consorcio_publico"]), COLORS["teal_dark"]),
            ("Serviço Público de Esgoto", percentual_sim(DIMENSOES_SERVICOS["servico_esgoto"]), COLORS["teal_dark"]),
            ("Índice de Maturidade Preenchido", (n_classificados / total_municipios * 100) if total_municipios else None, COLORS["blue_primary"]),
        ]
        investimento_mediano = sub["investimento_per_capita_saneamento"].median()
        percentual_dimensoes.append(
            ("Investimento Mediano per capita (Água + Esgoto)", investimento_mediano, COLORS["blue_primary"])
        )

        governance_tiles = html.Details([
            html.Summary("Governança em Percentual", className="territorial-collapsible-title"),
            html.Div([
                create_metric_card(
                    label,
                    investimento_formatado(value) if label.startswith("Investimento") else percentual_formatado(value),
                    detail="Mediana do território filtrado" if label.startswith("Investimento") else "Municípios do território filtrado",
                    value_color=color,
                )
                for label, value, color in percentual_dimensoes
            ], className="grid-governance-tiles"),
        ], className="territorial-collapsible")

        dimensoes_gargalos = {**DIMENSOES_GOVERNANCA, **DIMENSOES_INSTITUCIONAIS}
        rotulos_institucionais = {
            "regulacao_residuos": "Regulação de Resíduos Sólidos",
            "regulacao_drenagem": "Regulação de Drenagem",
            "consorcio_publico": "Participação em Consórcio Público",
        }
        gargalos = []
        for chave, coluna in dimensoes_gargalos.items():
            pct = percentual_sim(coluna)
            if pct is not None:
                rotulo = ROTULOS_DIMENSOES.get(chave, rotulos_institucionais.get(chave, chave.replace("_", " ").capitalize()))
                gargalos.append((pct, rotulo))
        gargalos.sort(key=lambda item: item[0])
        gargalos_top = gargalos[:3]
        if gargalos_top:
            gargalos_texto = (
                f"Os principais gargalos de governança em {territory_name} são: "
                + ", ".join(
                    f"{rotulo} ({pct:.1f}% dos municípios)"
                    for pct, rotulo in gargalos_top[:-1]
                )
                + (f" e {gargalos_top[-1][1]} ({gargalos_top[-1][0]:.1f}%)" if len(gargalos_top) > 1 else "")
                + "."
            )
        else:
            gargalos_texto = "Não há dados suficientes para calcular os gargalos de governança neste território."

        bottlenecks = html.Details([
            html.Summary("Gargalos de Governança", className="territorial-collapsible-title"),
            create_methodological_note(gargalos_texto, strong_prefix="Diagnóstico territorial:"),
        ], className="territorial-collapsible")

        territorial_additions = html.Div([governance_tiles, bottlenecks], className="territorial-additions")

        # Seção Específica para Nível Brasil: Mapa Coroplético por UF + Ranking Estadual
        if level == "brasil":
            map_metric_key = map_metric or "media_indice"
            metric_title, metric_desc, metric_colorscale = MAP_METRICS.get(
                map_metric_key, MAP_METRICS["media_indice"]
            )

            # Agregação rigorosa por UF
            uf_agg = df.groupby("UF").agg(
                media_indice=("indice_maturidade_saneamento", "mean"),
                media_previsto=("previsto_oof", "mean"),
                media_residuo=("residuo_oof", "mean"),
                n_total=("Município", "count"),
                n_com_dados=("indice_maturidade_saneamento", lambda x: x.notna().sum()),
            ).reset_index()

            acima_uf = df[df["classificacao_gestao"] == "Maturidade acima do esperado"].groupby("UF").size().reset_index(name="acima")
            abaixo_uf = df[df["classificacao_gestao"] == "Maturidade abaixo do esperado"].groupby("UF").size().reset_index(name="abaixo")

            uf_agg = uf_agg.merge(acima_uf, on="UF", how="left").merge(abaixo_uf, on="UF", how="left")
            uf_agg["acima"] = uf_agg["acima"].fillna(0)
            uf_agg["abaixo"] = uf_agg["abaixo"].fillna(0)
            uf_agg["pct_acima"] = (uf_agg["acima"] / uf_agg["n_com_dados"].replace(0, np.nan)) * 100
            uf_agg["pct_abaixo"] = (uf_agg["abaixo"] / uf_agg["n_com_dados"].replace(0, np.nan)) * 100

            # Associação da região
            uf_regiao_map = df.drop_duplicates("UF").set_index("UF")["Região"].to_dict()
            uf_agg["Região"] = uf_agg["UF"].map(uf_regiao_map)

            # 1. Mapa Coroplético
            fig_map = None
            if GEOJSON_BRAZIL and "features" in GEOJSON_BRAZIL:
                try:
                    fig_map = px.choropleth(
                        uf_agg,
                        geojson=GEOJSON_BRAZIL,
                        locations="UF",
                        featureidkey="properties.sigla",
                        color=map_metric_key,
                        color_continuous_scale=metric_colorscale,
                        hover_name="UF",
                        hover_data={
                            map_metric_key: ":.2f",
                            "n_com_dados": True,
                            "n_total": True,
                            "Região": True,
                            "UF": False,
                        },
                    )
                    fig_map.update_geos(
                        visible=False,
                        fitbounds=False,
                        lataxis_range=[-34.5, 6.0],
                        lonaxis_range=[-74.5, -34.0],
                        domain=dict(x=[0.0, 0.78], y=[0.0, 1.0]),
                    )
                    fig_map.update_layout(
                        **PLOTLY_THEME,
                        margin=dict(l=0, r=15, t=10, b=10),
                        height=620,
                        coloraxis_colorbar=dict(
                            title=dict(text=metric_title, font=dict(size=10)),
                            thickness=10,
                            len=0.48,
                            x=1.0,
                            xanchor="right",
                            y=0.5,
                            yanchor="middle",
                            tickfont=dict(size=9),
                        ),
                    )
                except Exception as e:
                    logger.error("Erro ao gerar mapa coroplético: %s", e)
                    fig_map = None

            # 2. Ranking Estadual por UF
            uf_agg_sorted = uf_agg.sort_values(map_metric_key, ascending=True)
            region_colors_list = [REGION_COLORS.get(r, "#64748b") for r in uf_agg_sorted["Região"]]

            fig_ranking_uf = go.Figure()
            fig_ranking_uf.add_trace(go.Bar(
                y=uf_agg_sorted["UF"],
                x=uf_agg_sorted[map_metric_key],
                orientation="h",
                marker=dict(color=region_colors_list, cornerradius=3),
                text=uf_agg_sorted[map_metric_key].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "—"),
                textposition="outside",
                textfont=dict(size=10, family="Inter"),
                hovertemplate="<b>UF: %{y}</b><br>" + f"{metric_title}: " + "%{x:.2f}<extra></extra>",
            ))
            fig_ranking_uf.update_layout(
                **PLOTLY_THEME,
                title=dict(text=f"Ranking dos 27 Estados — {metric_title}", font=dict(size=14)),
                height=620,
                yaxis=dict(title="", categoryorder="total ascending"),
                xaxis=dict(title=metric_title, gridcolor="#e2e8f0"),
                margin=dict(l=48, r=50, t=40, b=40),
            )

            # Montagem das visualizações do nível Brasil
            map_component = (
                dcc.Graph(figure=fig_map, config={"displayModeBar": False})
                if fig_map else html.Div("Mapa geográfico temporariamente indisponível.")
            )

            brazil_section = html.Div([
                html.Div([
                    create_chart_container(
                        f"Mapa Coroplético por Estado — {metric_title}",
                        map_component,
                        subtitle=metric_desc,
                        note="Passe o cursor sobre os estados para consultar dados agregados detalhados.",
                    ),
                    create_chart_container(
                        "Distribuição e Ranking por UF",
                        dcc.Graph(figure=fig_ranking_uf, config={"displayModeBar": False}),
                        subtitle="Cores por Grande Região geográfica do Brasil",
                        note="Legenda: Verde (Norte), Laranja (Nordeste), Azul (Sudeste), Roxo (Sul), Amarelo (Centro-Oeste).",
                    ),
                ], className="grid-charts-2"),
            ], className="brazil-territorial-block")

            return html.Div([cards_summary, territorial_additions, brazil_section])

        # Seção para Nível Região e Nível Estado
        else:
            regional_elements = []

            # 1. Histograma de Distribuição do Índice (0 a 8)
            if n_com_dados > 0:
                fig_dist = px.histogram(
                    subset_dados,
                    x="indice_maturidade_saneamento",
                    nbins=9,
                    color_discrete_sequence=[COLORS["teal_primary"]],
                )
                if pd.notna(media_obs):
                    fig_dist.add_vline(
                        x=media_obs,
                        line_dash="dash",
                        line_color=COLORS["highlight_terracotta"],
                        annotation_text=f"Média: {media_obs:.2f}",
                        annotation_position="top right",
                        annotation_font=dict(size=11, color=COLORS["highlight_terracotta"]),
                    )
                fig_dist.update_layout(
                    **PLOTLY_THEME,
                    title=dict(text="Distribuição do Índice de Maturidade Observado", font=dict(size=14)),
                    xaxis=dict(title="Índice de Maturidade (0 a 8)", dtick=1, gridcolor="#e2e8f0"),
                    yaxis=dict(title="Quantidade de Municípios", gridcolor="#e2e8f0"),
                    height=360,
                    bargap=0.08,
                    margin=dict(l=48, r=24, t=48, b=40),
                )
                chart_dist = create_chart_container(
                    "Distribuição da Maturidade",
                    dcc.Graph(figure=fig_dist, config={"displayModeBar": False}),
                    subtitle=f"Frequência nos {n_com_dados} municípios com dados válidos",
                )
            else:
                chart_dist = create_empty_state("Sem Dados para Distribuição", "Não há municípios com índice válido no recorte.")

            # 2. Distribuição da Classificação de Gestão
            class_counts = sub["classificacao_gestao"].value_counts().reset_index()
            class_counts.columns = ["Classificação", "Municípios"]
            ordem_classes = [
                "Maturidade acima do esperado",
                "Maturidade dentro do esperado",
                "Maturidade abaixo do esperado",
                "Sem dados suficientes",
            ]
            class_counts["Classificação"] = pd.Categorical(class_counts["Classificação"], categories=ordem_classes, ordered=True)
            class_counts = class_counts.sort_values("Classificação")

            bar_colors = [CLASS_COLORS.get(c, "#94a3b8") for c in class_counts["Classificação"]]
            fig_class = go.Figure()
            fig_class.add_trace(go.Bar(
                x=class_counts["Classificação"].apply(lambda s: s.replace("Maturidade ", "").capitalize()),
                y=class_counts["Municípios"],
                marker=dict(color=bar_colors, cornerradius=4),
                text=class_counts["Municípios"],
                textposition="outside",
                textfont=dict(size=11, family="Inter"),
                hovertemplate="<b>%{x}</b>: %{y} municípios<extra></extra>",
            ))
            fig_class.update_layout(
                **PLOTLY_THEME,
                title=dict(text="Municípios por Classificação de Gestão", font=dict(size=14)),
                xaxis=dict(title=""),
                yaxis=dict(title="Nº de Municípios", gridcolor="#e2e8f0"),
                height=360,
                margin=dict(l=48, r=24, t=48, b=40),
            )
            chart_class = create_chart_container(
                "Classificação Comparativa de Gestão",
                dcc.Graph(figure=fig_class, config={"displayModeBar": False}),
                subtitle="Categorias estatísticas em relação ao modelo",
            )

            # Linha 1 de Gráficos Regionais
            regional_elements.append(html.Div([chart_dist, chart_class], className="grid-charts-2"))

            # 3. Dispersão Socioeconômica: Receita per Capita x Índice de Maturidade
            scatter_data = sub.dropna(subset=["receita_per_capita", "indice_maturidade_saneamento"])
            if len(scatter_data) >= 3:
                fig_scatter = px.scatter(
                    scatter_data,
                    x="receita_per_capita",
                    y="indice_maturidade_saneamento",
                    color="classificacao_gestao",
                    color_discrete_map=CLASS_COLORS,
                    hover_name="Município",
                    hover_data={
                        "UF": True,
                        "receita_per_capita": ":,.2f",
                        "indice_maturidade_saneamento": ":.1f",
                        "populacao": ":,.0f",
                        "classificacao_gestao": True,
                    },
                    opacity=0.65,
                )
                fig_scatter.update_traces(marker=dict(size=6))
                fig_scatter.update_layout(
                    **PLOTLY_THEME,
                    title=dict(text="Receita per Capita Municipal × Índice de Maturidade Observado", font=dict(size=14)),
                    xaxis=dict(
                        title="Receita per capita anual (R$/habitante)",
                        gridcolor="#e2e8f0",
                    ),
                    yaxis=dict(title="Índice de Maturidade (0 a 8)", dtick=1, gridcolor="#e2e8f0"),
                    height=440,
                    legend=dict(
                        title=dict(text="Classificação"),
                        orientation="h",
                        yanchor="bottom",
                        y=-0.28,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11),
                    ),
                    margin=dict(l=48, r=24, t=48, b=64),
                )
                chart_scatter = create_chart_container(
                    "Dispersão Socioeconômica",
                    dcc.Graph(figure=fig_scatter, config={"displayModeBar": False}),
                    subtitle="Associação descritiva entre disponibilidade de receita e escore de maturidade",
                    note="Nota: A dispersão reflete associação descritiva dos dados e não comprova relação causal entre receita e governança.",
                    full_width=True,
                )
                regional_elements.append(chart_scatter)

            # 4. Rankings Municipais (Maiores e Menores Resíduos)
            res_data = sub.dropna(subset=["residuo_oof"])
            if len(res_data) >= 5:
                top_limit = min(12, len(res_data))
                top_cities = res_data.nlargest(top_limit, "residuo_oof")
                bot_cities = res_data.nsmallest(top_limit, "residuo_oof").sort_values("residuo_oof", ascending=True)

                # Gráfico Top Resíduo Positivo
                fig_top = go.Figure()
                fig_top.add_trace(go.Bar(
                    y=top_cities["Município"] + " (" + top_cities["UF"] + ")",
                    x=top_cities["residuo_oof"],
                    orientation="h",
                    marker=dict(color=COLORS["teal_primary"], cornerradius=3),
                    text=top_cities["residuo_oof"].apply(lambda v: f"{v:+.2f}"),
                    textposition="outside",
                    textfont=dict(size=10, family="Inter"),
                    hovertemplate="<b>%{y}</b><br>Resíduo: %{x:+.2f}<extra></extra>",
                ))
                fig_top.update_layout(
                    **PLOTLY_THEME,
                    title=dict(text=f"Destaques com Maior Resíduo Positivo (Top {top_limit})", font=dict(size=13)),
                    yaxis=dict(categoryorder="total ascending", title=""),
                    xaxis=dict(title="Resíduo (Observado − Esperado)", gridcolor="#e2e8f0"),
                    height=380,
                    margin=dict(l=150, r=50, t=40, b=40),
                )

                # Gráfico Bottom Resíduo Negativo
                fig_bot = go.Figure()
                fig_bot.add_trace(go.Bar(
                    y=bot_cities["Município"] + " (" + bot_cities["UF"] + ")",
                    x=bot_cities["residuo_oof"],
                    orientation="h",
                    marker=dict(color=COLORS["highlight_terracotta"], cornerradius=3),
                    text=bot_cities["residuo_oof"].apply(lambda v: f"{v:+.2f}"),
                    textposition="outside",
                    textfont=dict(size=10, family="Inter"),
                    hovertemplate="<b>%{y}</b><br>Resíduo: %{x:+.2f}<extra></extra>",
                ))
                fig_bot.update_layout(
                    **PLOTLY_THEME,
                    title=dict(text=f"Destaques com Maior Resíduo Negativo (Top {top_limit})", font=dict(size=13)),
                    yaxis=dict(categoryorder="total descending", title=""),
                    xaxis=dict(title="Resíduo (Observado − Esperado)", gridcolor="#e2e8f0"),
                    height=380,
                    margin=dict(l=150, r=50, t=40, b=40),
                )

                ranking_row = html.Div([
                    create_chart_container("Maturidade Superior à Estimada", dcc.Graph(figure=fig_top, config={"displayModeBar": False})),
                    create_chart_container("Maturidade Inferior à Estimada", dcc.Graph(figure=fig_bot, config={"displayModeBar": False})),
                ], className="grid-charts-2 territorial-ranking-row")
                regional_elements.append(ranking_row)

            return html.Div([cards_summary, territorial_additions] + regional_elements)

    # 6. Explorador de Dados: Sincronização Dinâmica de Filtros de UF
    @app.callback(
        Output("explore-uf-filter", "options"),
        Input("explore-regiao-filter", "value"),
    )
    def sync_explore_ufs(regioes):
        if regioes:
            sub = df[df["Região"].isin(regioes)]
        else:
            sub = df
        ufs = sorted(sub["UF"].dropna().unique()) if "UF" in sub.columns else []
        return [{"label": u, "value": u} for u in ufs]

    # 7. Explorador de Dados: Nota Metodológica de Dados Ausentes
    @app.callback(
        Output("explore-note-area", "children"),
        Input("explore-x", "value"),
        Input("explore-y", "value"),
    )
    def update_explore_missing_note(var_x, var_y):
        notes = []
        total = len(df)
        for var in [var_x, var_y]:
            if var and var != "DISABLED" and var in df.columns:
                n_miss = df[var].isna().sum()
                pct_miss = (n_miss / total * 100) if total > 0 else 0
                if pct_miss > 12:
                    notes.append(
                        f"A variável \"{friendly(var)}\" possui {pct_miss:.1f}% de registros ausentes "
                        f"({n_miss:,} de {total:,} municípios).".replace(",", ".")
                    )
        if notes:
            full_text = " ".join(notes) + " Os resultados apresentados consideram apenas os municípios com informação disponível."
            return create_methodological_note(full_text, strong_prefix="Atenção à Cobertura:")
        return html.Div()

    # 8. Explorador de Dados: Renderização do Gráfico com Tratamento de Erros
    @app.callback(
        Output("explore-chart-area", "children"),
        Input("explore-x", "value"),
        Input("explore-y", "value"),
        Input("explore-color", "value"),
        Input("explore-chart-type", "value"),
        Input("explore-regiao-filter", "value"),
        Input("explore-uf-filter", "value"),
        Input("explore-class-filter", "value"),
    )
    def render_explore_chart(x_col, y_col, color_col, chart_type, regioes, ufs, classes):
        if not x_col or x_col == "DISABLED":
            return create_empty_state("Selecione as Variáveis", "Escolha uma variável válida para o Eixo X.")

        sub = df.copy()

        # Aplicação dos filtros do explorador
        if regioes:
            sub = sub[sub["Região"].isin(regioes)]
        if ufs:
            sub = sub[sub["UF"].isin(ufs)]
        if classes:
            sub = sub[sub["classificacao_gestao"].isin(classes)]

        if len(sub) == 0:
            return create_empty_state(
                "Sem Registros Encontrados",
                "Não existem observações suficientes para gerar este gráfico com os filtros selecionados.",
                "Remova ou amplie os filtros de região, estado ou classificação"
            )

        # Mapeamento de Cores
        actual_color = None if color_col == "none" else color_col
        color_map = None
        if actual_color == "classificacao_gestao":
            color_map = CLASS_COLORS
        elif actual_color == "Região":
            color_map = REGION_COLORS

        hover_info = {
            "UF": True,
            "Região": True,
            "populacao": ":,.0f",
            "receita_per_capita": ":,.2f",
            "indice_maturidade_saneamento": ":.1f",
        }
        try:
            if chart_type == "scatter":
                if not y_col or y_col == "DISABLED":
                    return create_empty_state("Selecione o Eixo Y", "Para gráfico de dispersão, selecione uma variável para o Eixo Y.")

                clean_sub = sub.dropna(subset=[x_col, y_col])
                if len(clean_sub) == 0:
                    return create_empty_state("Dados Ausentes", "Não existem observações completas com dados preenchidos simultaneamente em X e Y.")

                fig = px.scatter(
                    clean_sub,
                    x=x_col,
                    y=y_col,
                    color=actual_color,
                    color_discrete_map=color_map,
                    hover_name="Município",
                    hover_data=hover_info,
                    opacity=0.65,
                )
                fig.update_traces(marker=dict(size=5.5))

            elif chart_type == "bar":
                if sub[x_col].nunique() <= 35:
                    group_columns = [x_col]
                    if actual_color and actual_color != x_col:
                        group_columns.append(actual_color)

                    if y_col and y_col != "DISABLED":
                        agg_bar = sub.groupby(group_columns, dropna=False)[y_col].mean().reset_index()
                        fig = px.bar(
                            agg_bar, x=x_col, y=y_col,
                            color=actual_color,
                            color_discrete_map=color_map,
                            color_discrete_sequence=[COLORS["teal_primary"]],
                        )
                    else:
                        agg_bar = sub.groupby(group_columns, dropna=False).size().reset_index(name="Municípios")
                        fig = px.bar(
                            agg_bar, x=x_col, y="Municípios",
                            color=actual_color,
                            color_discrete_map=color_map,
                            color_discrete_sequence=[COLORS["blue_primary"]],
                        )
                else:
                    clean_sub = sub.dropna(subset=[x_col] + ([y_col] if y_col and y_col != "DISABLED" else []))
                    fig = px.bar(
                        clean_sub.head(50),
                        x=x_col,
                        y=y_col if y_col and y_col != "DISABLED" else None,
                        color=actual_color,
                        color_discrete_map=color_map,
                    )

            elif chart_type == "box":
                cat_col = actual_color if actual_color else "Região"
                val_col = y_col if y_col and y_col != "DISABLED" else x_col
                clean_sub = sub.dropna(subset=[val_col])
                fig = px.box(
                    clean_sub,
                    x=cat_col,
                    y=val_col,
                    color=actual_color,
                    color_discrete_map=color_map,
                )

            elif chart_type == "histogram":
                clean_sub = sub.dropna(subset=[x_col])
                fig = px.histogram(
                    clean_sub,
                    x=x_col,
                    color=actual_color,
                    color_discrete_map=color_map,
                    nbins=30,
                    opacity=0.75,
                )

            else:
                return create_empty_state("Tipo Não Suportado", "Tipo de gráfico não reconhecido.")

            fig.update_layout(
                **PLOTLY_THEME,
                title=dict(
                    text=f"{friendly(x_col)}" + (f" × {friendly(y_col)}" if y_col and y_col != "DISABLED" and chart_type != "histogram" else ""),
                    font=dict(size=15),
                ),
                xaxis=dict(title=friendly(x_col), gridcolor="#e2e8f0"),
                yaxis=dict(
                    title=friendly(y_col) if y_col and y_col != "DISABLED" else "",
                    gridcolor="#e2e8f0",
                ),
                height=520,
                legend=dict(
                    title=dict(text=""),
                    orientation="h",
                    yanchor="bottom",
                    y=-0.22,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11),
                ),
                margin=dict(l=48, r=24, t=48, b=64),
            )

            return dcc.Graph(figure=fig, config={"displayModeBar": True})

        except Exception as err:
            logger.error("Falha ao gerar gráfico do explorador: %s", err)
            return create_empty_state(
                "Visualização Incompatível",
                "A combinação selecionada de variáveis e tipo de gráfico não pôde ser renderizada.",
                "Tente selecionar outro tipo de gráfico ou verificar as variáveis nos eixos"
            )
