"""
components.py — Componentes visuais institucionais, cards e layouts.
Observatório da Gestão Municipal do Saneamento: Maturidade da gestão municipal (observado versus esperado).
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html

from .data_loader import (
    DIMENSOES_GOVERNANCA,
    ROTULOS_DIMENSOES,
    friendly,
)

# ──────────────────────────────────────────────────────────────────────────────
# PALETA DE CORES INSTITUCIONAL
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {
    "teal_dark": "#0f766e",     # Verde-azulado profundo (primária)
    "teal_primary": "#0d9488",  # Verde-azulado institucional
    "teal_light": "#ccfbf1",    # Fundo verde suave
    "blue_dark": "#1e3a8a",     # Azul petróleo institucional (secundária)
    "blue_primary": "#0284c7",  # Azul médio
    "surface_light": "#f8fafc", # Fundo de superfície
    "border_subtle": "#e2e8f0", # Bordas discretas
    "text_dark": "#0f172a",     # Títulos e valores principais
    "text_body": "#334155",     # Textos normais
    "text_muted": "#64748b",    # Rótulos e legendas
    "highlight_terracotta": "#c2410c", # Destaque terracota
    "highlight_amber": "#d97706",      # Destaque âmbar
}

# Cores rigorosamente calibradas para as 4 classes de gestão
CLASS_COLORS = {
    "Maturidade acima do esperado": "#059669",   # Esmeralda sóbrio
    "Maturidade dentro do esperado": "#0284c7",  # Azul institucional
    "Maturidade abaixo do esperado": "#dc2626",  # Vermelho sóbrio
    "Sem dados suficientes": "#94a3b8",          # Ardósia neutro
}

REGION_COLORS = {
    "Norte": "#0d9488",
    "Nordeste": "#c2410c",
    "Sudeste": "#0284c7",
    "Sul": "#6366f1",
    "Centro-Oeste": "#d97706",
}

# Tema unificado para todos os gráficos Plotly
PLOTLY_THEME = dict(
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", color="#334155", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(
        bgcolor="#ffffff",
        bordercolor="#cbd5e1",
        font_size=12,
        font_family="Inter, sans-serif",
        font_color="#0f172a",
    ),
)


# ──────────────────────────────────────────────────────────────────────────────
# CABEÇALHO, NAVEGAÇÃO E RODAPÉ
# ──────────────────────────────────────────────────────────────────────────────
def create_sidebar():
    """Sidebar vertical institucional elegante e compacta no lado esquerdo."""
    return html.Aside([
        html.Div([
            # Topo: Brand / Logo institucional acima do título
            html.Div([
                html.Div([
                    html.Img(
                        src="/assets/logo.png",
                        alt="Logo Observatório da Gestão Municipal em Saneamento",
                        className="sidebar-logo-img",
                    ),
                ], className="sidebar-logo-wrapper"),
                html.Div([
                    html.H1("Observatório da Gestão Municipal em Saneamento", className="brand-title"),
                    html.Span("Maturidade da gestão municipal: observado versus esperado", className="brand-subtitle"),
                ], className="brand-text sidebar-brand-text"),
            ], className="sidebar-brand-container"),

            html.Div(className="sidebar-divider"),

            # Seção de Navegação Vertical
            html.Div([
                html.Span("NAVEGAÇÃO PRINCIPAL", className="sidebar-section-title"),
                dcc.Tabs(
                    id="tabs",
                    value="about",
                    vertical=True,
                    children=[
                        dcc.Tab(
                            label="Sobre o projeto",
                            value="about",
                            className="sidebar-tab",
                            selected_className="sidebar-tab--selected",
                        ),
                        dcc.Tab(
                            label="Consulta municipal",
                            value="consult",
                            className="sidebar-tab",
                            selected_className="sidebar-tab--selected",
                        ),
                        dcc.Tab(
                            label="Panorama territorial",
                            value="geo",
                            className="sidebar-tab",
                            selected_className="sidebar-tab--selected",
                        ),
                        dcc.Tab(
                            label="Explorar dados",
                            value="explore",
                            className="sidebar-tab",
                            selected_className="sidebar-tab--selected",
                        ),
                    ],
                    parent_className="sidebar-tabs-parent",
                    className="sidebar-tabs-container",
                ),
            ], className="sidebar-nav-section"),
        ], className="sidebar-top-wrapper"),

        # Rodapé Institucional da Sidebar
        html.Div([
            html.Div(className="sidebar-divider"),
            html.Div([
                html.Span("PROJETO DE REÚSO DE DADOS ABERTOS", className="tag-institutional sidebar-tag"),
                html.Span("SINISA · IBGE · STN · INEP", className="tag-source sidebar-source"),
                html.Span("Ano-base: 2024 · Dados Abertos", className="sidebar-year-meta"),
            ], className="sidebar-footer-meta"),
        ], className="sidebar-bottom-wrapper"),
    ], className="app-sidebar")


def create_header():
    """Mantido para compatibilidade, utiliza create_sidebar."""
    return create_sidebar()


def create_footer():
    """Rodapé institucional com aviso metodológico."""
    return html.Footer([
        html.Div([
            html.Div([
                html.P([
                    html.Strong("Observatório da Gestão Municipal em Saneamento"),
                    " — Plataforma analítica de avaliação de maturidade em saneamento básico municipal.",
                ], className="footer-title"),
                html.P(
                    "A classificação é comparativa e depende do modelo estatístico e das variáveis socioeconômicas utilizadas. "
                    "Ela não constitui prova causal de eficiência ou qualidade da gestão municipal.",
                    className="footer-disclaimer",
                ),
            ], className="footer-left"),
            html.Div([
                html.Span("Dados públicos · SINISA · IBGE · STN · INEP", className="footer-meta"),
                html.Span("Ano-base de referência: 2024 / Dados abertos", className="footer-meta"),
            ], className="footer-right"),
        ], className="footer-inner container"),
    ], className="app-footer")


# ──────────────────────────────────────────────────────────────────────────────
# CARDS, BADGES E COMPONENTES BÁSICOS
# ──────────────────────────────────────────────────────────────────────────────
def create_metric_card(label, value, detail=None, badge=None, value_color=None, icon=None, card_class=""):
    """Card de métrica institucional com hierarquia visual clara."""
    content = []
    header_elements = [html.Span(label, className="metric-label")]
    if badge:
        header_elements.append(badge)
    content.append(html.Div(header_elements, className="metric-card-header"))

    val_style = {"color": value_color} if value_color else {}
    content.append(html.Span(value, className="metric-value", style=val_style))

    if detail:
        content.append(html.Span(detail, className="metric-detail"))

    full_class = f"metric-card {card_class}".strip() if card_class else "metric-card"
    return html.Div(content, className=full_class)


def get_classification_theme(classificacao):
    """Retorna classes CSS e cores institucionais conforme a classificação da gestão."""
    cls_str = str(classificacao).strip().lower() if pd.notna(classificacao) else ""
    if "acima" in cls_str:
        return {
            "header_class": "city-header-above",
            "metric_class": "metric-card-above",
            "color": "#059669",  # Verde - acima do esperado
        }
    elif "dentro" in cls_str:
        return {
            "header_class": "city-header-within",
            "metric_class": "metric-card-within",
            "color": "#0284c7",  # Azul - dentro do esperado
        }
    elif "abaixo" in cls_str:
        return {
            "header_class": "city-header-below",
            "metric_class": "metric-card-below",
            "color": "#dc2626",  # Vermelho - abaixo do esperado
        }
    else:
        return {
            "header_class": "city-header-nodata",
            "metric_class": "metric-card-nodata",
            "color": "#64748b",  # Normal - sem dados
        }


def create_classification_badge(classificacao):
    """Badge elegante para a classificação com ícone discreto."""
    if not classificacao or pd.isna(classificacao):
        classificacao = "Sem dados suficientes"

    cls_str = str(classificacao).strip()
    badge_config = {
        "Maturidade acima do esperado": ("badge-above", "▲ Acima do esperado"),
        "Maturidade dentro do esperado": ("badge-within", "● Dentro do esperado"),
        "Maturidade abaixo do esperado": ("badge-below", "▼ Abaixo do esperado"),
        "Sem dados suficientes": ("badge-nodata", "— Sem dados suficientes"),
    }
    css_cls, label = badge_config.get(cls_str, ("badge-nodata", cls_str))
    return html.Span(label, className=f"status-badge {css_cls}")


def create_methodological_note(text, strong_prefix="Observação metodológica:"):
    """Caixa de aviso metodológico editorial."""
    return html.Div([
        html.Div("ℹ", className="note-symbol"),
        html.Div([
            html.Strong(f"{strong_prefix} ") if strong_prefix else None,
            html.Span(text),
        ], className="note-text"),
    ], className="methodological-note")


def create_empty_state(title, description, action_hint=None):
    """Estado vazio editorial quando nenhum elemento está selecionado."""
    return html.Div([
        html.Div([
            html.Div("🏛️", className="empty-state-symbol"),
            html.H3(title, className="empty-state-title"),
            html.P(description, className="empty-state-desc"),
            html.Span(action_hint, className="empty-state-hint") if action_hint else None,
        ], className="empty-state-card"),
    ], className="empty-state-wrapper")


def create_chart_container(title, graph_component, subtitle=None, note=None, full_width=False):
    """Contêiner padronizado com cabeçalho, divisor e rodapé informativo."""
    header_children = [html.H4(title, className="chart-title")]
    if subtitle:
        header_children.append(html.Span(subtitle, className="chart-subtitle"))

    elements = [
        html.Div(header_children, className="chart-header"),
        html.Div(graph_component, className="chart-body"),
    ]
    if note:
        elements.append(html.Div(note, className="chart-footer-note"))

    box_class = "chart-box chart-box-full" if full_width else "chart-box"
    return html.Div(elements, className=box_class)


# ──────────────────────────────────────────────────────────────────────────────
# COMPONENTES DA CONSULTA MUNICIPAL
# ──────────────────────────────────────────────────────────────────────────────
def create_bullet_chart(observado, previsto, nome_municipio):
    """
    Bullet chart horizontal limpo comparando Observado vs. Esperado (0 a 8).
    Cumpre estritamente a especificação visual editorial (0 ── Esperado ── Observado ── 8).
    """
    has_obs = pd.notna(observado)
    has_prev = pd.notna(previsto)

    if not has_obs and not has_prev:
        return html.Div(
            create_methodological_note("Município sem registro suficiente de governança no SINISA."),
            className="chart-bullet-container"
        )

    fig = go.Figure()

    # Faixa total de referência (0 a 8)
    fig.add_trace(go.Bar(
        y=["Índice"],
        x=[8],
        orientation="h",
        marker=dict(color="#f1f5f9", line=dict(color="#cbd5e1", width=1)),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Barra do Índice Observado
    if has_obs:
        fig.add_trace(go.Bar(
            y=["Índice"],
            x=[observado],
            orientation="h",
            marker=dict(color=COLORS["teal_primary"], cornerradius=4),
            name=f"Observado ({observado:.1f})",
            text=[f"Observado: {observado:.1f}"],
            textposition="inside",
            textfont=dict(color="#ffffff", size=13, family="Inter", weight=600),
            hovertemplate="<b>Índice Observado</b>: %{x:.2f} (escala 0 a 8)<extra></extra>",
        ))

    # Marcador vertical do Índice Previsto (Esperado)
    if has_prev:
        fig.add_trace(go.Scatter(
            y=["Índice"],
            x=[previsto],
            mode="markers+text",
            marker=dict(
                symbol="line-ns-open",
                size=32,
                color=COLORS["highlight_terracotta"],
                line=dict(width=3.5, color=COLORS["highlight_terracotta"]),
            ),
            text=[f" Previsto: {previsto:.1f}"],
            textposition="top center",
            textfont=dict(color=COLORS["highlight_terracotta"], size=12, family="Inter", weight=600),
            name=f"Previsto pelo modelo ({previsto:.1f})",
            hovertemplate="<b>Índice Previsto (Modelo)</b>: %{x:.2f}<extra></extra>",
        ))

    fig.update_layout(
        **PLOTLY_THEME,
        barmode="overlay",
        xaxis=dict(
            range=[0, 8.2],
            dtick=1,
            title=dict(text="Escala do Índice de Maturidade (0 a 8 dimensões)", font=dict(size=11, color="#64748b")),
            gridcolor="#e2e8f0",
            gridwidth=1,
            zeroline=False,
        ),
        yaxis=dict(title="", showticklabels=False),
        height=140,
        margin=dict(l=16, r=24, t=28, b=36),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
        showlegend=True,
    )

    residuo_calc = observado - previsto if has_obs and has_prev else None
    res_text = (
        f"Diferença observada versus prevista (resíduo): {residuo_calc:+.2f} pontos."
        if residuo_calc is not None else "Sem cálculo comparativo disponível."
    )

    return html.Div([
        html.Div([
            html.Span("AVALIAÇÃO ANALÍTICA", className="section-badge badge-blue"),
            html.H4("Comparação: Observado × Esperado pelo Modelo", className="chart-title section-title-comparacao"),
            html.Span(res_text, className="chart-subtitle section-subtitle-comparacao"),
        ], className="chart-header"),
        html.Div(
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
            className="bullet-chart-card-inner"
        ),
    ], className="chart-box chart-bullet-box section-box-comparacao")


def create_governance_section(row):
    """
    Renderiza o painel das 8 dimensões de governança com status Sim / Não / Sem resposta.
    """
    items = []
    num_sim = 0
    total_dim = len(DIMENSOES_GOVERNANCA)

    for key, col_name in DIMENSOES_GOVERNANCA.items():
        val = row.get(col_name)
        rotulo = ROTULOS_DIMENSOES.get(key, key)

        if str(val).strip().lower() in ["sim", "s"]:
            status_cls = "gov-status-sim"
            status_text = "Sim"
            icon = "✓"
            num_sim += 1
        elif str(val).strip().lower() in ["não", "nao", "n"]:
            status_cls = "gov-status-nao"
            status_text = "Não"
            icon = "✕"
        else:
            status_cls = "gov-status-sem-resposta"
            status_text = "Sem resposta"
            icon = "—"

        items.append(html.Div([
            html.Div([
                html.Span(icon, className=f"gov-icon {status_cls}"),
                html.Span(rotulo, className="gov-dimension-name"),
            ], className="gov-item-left"),
            html.Span(status_text, className=f"gov-item-badge {status_cls}"),
        ], className="gov-dimension-row"))

    header = html.Div([
        html.Div([
            html.Span("GOVERNANÇA E REGULAÇÃO", className="section-badge badge-teal"),
            html.H4("Dimensões de Governança Municipal em Saneamento", className="section-title section-title-gov"),
            html.Span("As 8 componentes do SINISA sintetizadas no Índice de Maturidade (0 a 8)", className="section-subtitle section-subtitle-gov"),
        ]),
        html.Div([
            html.Span(f"{num_sim} de {total_dim}", className="gov-counter-big"),
            html.Span("dimensões ativas", className="gov-counter-label"),
        ], className="gov-counter-box"),
    ], className="gov-section-header")

    return html.Div([
        header,
        html.Div(items, className="gov-dimensions-list"),
    ], className="card-panel section-box-gov")


def create_socioeconomic_section(row):
    """
    Renderiza o painel de contexto municipal socioeconômico.
    Nunca inventa valores e exibe 'Sem dados' para campos ausentes.
    """
    pop = row.get("populacao")
    rec_pc = row.get("receita_per_capita")
    rec_tot = row.get("receita_total")
    taxa_aprov = row.get("taxa_aprovacao_ensino_fundamental")
    idhm = row.get("idhm")
    grau_urb = row.get("grau_urbanizacao")

    pop_str = f"{pop:,.0f}".replace(",", ".") if pd.notna(pop) else "Sem dados"
    rec_pc_str = f"R$ {rec_pc:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(rec_pc) else "Sem dados"
    rec_tot_str = f"R$ {rec_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(rec_tot) else "Sem dados"
    taxa_str = f"{taxa_aprov:.1f}%" if pd.notna(taxa_aprov) else "Sem dados"

    # IDHM
    if pd.notna(idhm) and float(idhm) > 0:
        idhm_val = float(idhm)
        idhm_str = f"{idhm_val:.3f}"
        if idhm_val >= 0.800:
            idhm_detail = "Muito Alto (PNUD / Atlas)"
        elif idhm_val >= 0.700:
            idhm_detail = "Alto (PNUD / Atlas)"
        elif idhm_val >= 0.600:
            idhm_detail = "Médio (PNUD / Atlas)"
        else:
            idhm_detail = "Baixo (PNUD / Atlas)"
    else:
        idhm_str = "Sem dados"
        idhm_detail = "Índice de Desenv. Humano"

    # Grau / Índice de Urbanização
    if pd.notna(grau_urb):
        urb_val = float(grau_urb)
        if urb_val <= 1.0:
            urb_val = urb_val * 100.0
        urb_str = f"{urb_val:.1f}%"
        urb_detail = "População em área urbana (IBGE)"
    else:
        urb_str = "Sem dados"
        urb_detail = "Taxa de urbanização"

    return html.Div([
        html.Div([
            html.Span("INDICADORES DE BASE", className="section-badge badge-amber"),
            html.H4("Contexto Municipal Socioeconômico", className="section-title section-title-socio"),
            html.Span("Características utilizadas pelo modelo de machine learning para estimar o esperado", className="section-subtitle section-subtitle-socio"),
        ], className="section-header-simple"),
        html.Div([
            create_metric_card("População Residente", pop_str, detail="Habitantes (IBGE Censo)"),
            create_metric_card("Receita per Capita", rec_pc_str, detail="Receita anual / habitante"),
            create_metric_card("Taxa de Aprovação", taxa_str, detail="Ensino Fundamental (INEP)"),
            create_metric_card("Receita Orçamentária Total", rec_tot_str, detail="Arrecadação municipal (STN)"),
            create_metric_card("IDHM (Desenvolvimento)", idhm_str, detail=idhm_detail),
            create_metric_card("Índice de Urbanização", urb_str, detail=urb_detail),
        ], className="grid-cards-6"),
    ], className="card-panel section-box-socio")


# ──────────────────────────────────────────────────────────────────────────────
# ABA 1: CONTEÚDO EDITORIAL "SOBRE O PROJETO"
# ──────────────────────────────────────────────────────────────────────────────
def create_about_tab_content():
    """Gera a página editorial institucional completa sobre a metodologia e o projeto."""
    return html.Div([
        dcc.Download(id="dataset-download"),
        # Hero Editorial
        html.Div([
            html.Div([
                html.Span("PROJETO DE REÚSO DE DADOS ABERTOS", className="hero-eyebrow"),
                html.H2("Observatório da Gestão Municipal em Saneamento", className="hero-title"),
                html.H3("Maturidade da gestão municipal: observado versus esperado", className="hero-subtitle"),
                html.P(
                    "Uma ferramenta analítica de transparência e diagnóstico que investiga como a governança "
                    "e a gestão de saneamento básico nos municípios brasileiros se comportam em comparação com o que "
                    "seria esperado considerando suas características e perfis socioeconômicos.",
                    className="hero-description",
                ),
            ], className="hero-content"),
        ], className="editorial-hero"),

        # O que estamos medindo?
        html.Div([
            html.Div([
                html.Span("DIMENSÕES AVALIADAS", className="section-badge badge-teal"),
                html.H3("O que estamos medindo?", className="section-title-editorial"),
                html.P(
                    "O ponto de partida analítico é o Índice de Maturidade da Gestão Municipal em Saneamento, "
                    "que varia de 0 a 8. Cada ponto corresponde ao cumprimento de uma dimensão-chave de governança, "
                    "institucionalidade, transparência e regulação reportada ao SINISA:",
                    className="editorial-p",
                ),
            ], className="section-header-editorial"),

            html.Div([
                _editorial_dim_card("01", "Regulação de Água", "Entidade pública responsável pela regulação dos serviços de abastecimento de água."),
                _editorial_dim_card("02", "Regulação de Esgoto", "Entidade pública responsável pela regulação dos serviços de esgotamento sanitário."),
                _editorial_dim_card("03", "Política Municipal", "Existência de Lei Municipal que institui a Política de Saneamento Básico (Lei 11.445)."),
                _editorial_dim_card("04", "Plano de Saneamento", "Existência de Plano Municipal ou Regional de Saneamento Básico formalmente instituído."),
                _editorial_dim_card("05", "Gestão de Resíduos", "Existência de Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS)."),
                _editorial_dim_card("06", "Transparência de Dados", "Sistema público e acessível de informações sobre os serviços de saneamento básico."),
                _editorial_dim_card("07", "Controle Social", "Ouvidoria municipal ou central pública de atendimento a manifestações dos cidadãos."),
                _editorial_dim_card("08", "Conselho Específico", "Conselho Municipal deliberativo ou consultivo específico para o saneamento básico."),
            ], className="grid-editorial-dims"),
        ], className="editorial-section section-about-dims"),

        # Observado versus esperado (Fluxo Lógico)
        html.Div([
            html.Div([
                html.Span("MECÂNICA ESTRUTURAL", className="section-badge badge-blue"),
                html.H3("Observado versus Esperado", className="section-title-editorial"),
                html.P(
                    "O modelo estatístico busca responder: dado o tamanho populacional, a receita e os indicadores "
                    "socioeconômicos do município, qual seria o patamar de maturidade esperado?",
                    className="editorial-p",
                ),
            ], className="section-header-editorial"),

            html.Div([
                _flow_box("Índice Observado (0 a 8)", "Maturidade declarada e documentada na base oficial do SINISA."),
                html.Div("→", className="flow-arrow"),
                _flow_box("Índice Previsto pelo Modelo", "Estimativa gerada por Machine Learning (validação cruzada OOF) baseada no perfil municipal."),
                html.Div("→", className="flow-arrow"),
                _flow_box("Diferença / Resíduo", "Resíduo = Observado − Previsto. Quantifica o desvio relativo à estimativa."),
                html.Div("→", className="flow-arrow"),
                _flow_box("Classificação Comparativa", "Identificação estatística: acima, dentro ou abaixo do esperado."),
            ], className="methodology-flow-row"),

            create_methodological_note(
                "A classificação é estritamente comparativa e depende do modelo e das variáveis utilizadas. "
                "Ela não constitui prova causal de eficiência, competência ou qualidade administrativa do município.",
                strong_prefix="Aviso de Rigor Metodológico:"
            ),
        ], className="editorial-section section-about-fluxo"),

        # Metodologia em 5 passos
        html.Div([
            html.Div([
                html.Span("PIPELINE CIENTÍFICO", className="section-badge badge-indigo"),
                html.H3("Metodologia em 5 Etapas", className="section-title-editorial"),
                html.P("Rigor metodológico, reprodutibilidade e transparência analítica:", className="editorial-p"),
            ], className="section-header-editorial"),

            html.Div([
                _step_card("01", "Integração dos Dados", "Unificação dos registros do SINISA (Módulo de Gestão), IBGE (população), Tesouro Nacional (receitas) e INEP (educação) por código IBGE padronizado."),
                _step_card("02", "Construção do Índice", "Agregação das oito dimensões de governança em um escore analítico direto de 0 a 8 pontos de maturidade institucional."),
                _step_card("03", "Modelagem Estatística", "Aplicação de algoritmo de Machine Learning supervisionado para estimar o valor esperado com validação out-of-fold, prevenindo overfitting."),
                _step_card("04", "Cálculo do Resíduo", "Determinação da diferença entre a maturidade observada e o valor estimado pelo modelo para cada município do Brasil."),
                _step_card("05", "Classificação Comparativa", "Agrupamento dos municípios em Acima do esperado, Dentro do esperado, Abaixo do esperado ou Sem dados suficientes."),
            ], className="grid-steps"),
        ], className="editorial-section section-about-metodologia"),

        # Dados e Transparência (Links e Repositórios)
        html.Div([
            html.Div([
                html.Span("REPOSITÓRIOS ABERTOS", className="section-badge badge-amber"),
                html.H3("Dados e Transparência", className="section-title-editorial"),
                html.P("Acesso aos dados brutos, dicionários de variáveis e scripts de modelagem:", className="editorial-p"),
            ], className="section-header-editorial"),

            html.Div([
                _resource_item("📊", "Dataset Final Consolidado", "Arquivo CSV com as variáveis integradas e classificações do modelo.", "#", component_id="dataset-download-link"),
                _resource_item("🏛️", "Fontes Oficiais Originais", "Bases de dados abertos do SINISA, STN (Siconfi), IBGE e INEP.", "https://docs.google.com/spreadsheets/d/1pGq2Lo92O31m8aeHRKajbapyUwbWOitEpWP8gkudOuE/edit?gid=2038937363#gid=2038937363"),
                _resource_item("📖", "Dicionário de Variáveis", "Relação detalhada, tipos de dados e descrições das 163 colunas da base.", "https://docs.google.com/spreadsheets/d/1pGq2Lo92O31m8aeHRKajbapyUwbWOitEpWP8gkudOuE/edit?usp=sharing"),
                _resource_item("🔗", "Notebook de Integração", "Pipeline de limpeza, tratamento de nulos e casamento de códigos IBGE.", "https://colab.research.google.com/drive/1v3HcafOW9EXENzyIVFA95XNGoPhP44gn?usp=sharing"),
                _resource_item("🤖", "Notebook de Machine Learning", "Treinamento, otimização de hiperparâmetros e validação out-of-fold.", "https://colab.research.google.com/drive/1sf8G4n3HRgtC7nYmXOFbnHSzVQHRTHgK?usp=sharing"),
                _resource_item("💾", "Arquivo do Melhor Modelo", "Serialização do modelo de machine learning utilizado para predição.", "/assets/modelo_maturidade_saneamento_v2.pkl"),
            ], className="grid-resources"),
        ], className="editorial-section section-about-dados"),

        # Autor do Projeto
        html.Div([
            html.Div([
                html.Span("DESENVOLVIMENTO", className="section-badge badge-teal"),
                html.H3("Autor do Projeto", className="section-title-editorial"),
                html.Div([
                    html.Div([
                        html.Img(
                            src="/assets/autor.jpg",
                            alt="Luiz Vinicius de Lima Santos",
                            className="author-photo",
                        ),
                    ], className="author-photo-wrapper"),
                    html.Div([
                        html.H4("Luiz Vinicius de Lima Santos", className="author-name"),
                        html.Span("Desenvolvedor & Autor do Projeto", className="author-role"),
                        html.Div([
                            html.Div([
                                html.Span("Idade:", className="author-meta-label"),
                                html.Span("19 anos", className="author-meta-value"),
                            ], className="author-meta-item"),
                            html.Div([
                                html.Span("Curso:", className="author-meta-label"),
                                html.Span("Sistemas de Informação", className="author-meta-value"),
                            ], className="author-meta-item"),
                            html.Div([
                                html.Span("Universidade:", className="author-meta-label"),
                                html.Span("Universidade Federal Rural de Pernambuco (UFRPE)", className="author-meta-value"),
                            ], className="author-meta-item"),
                        ], className="author-meta-grid"),
                        html.Div([
                            html.A([
                                html.Span("💼", className="link-icon"),
                                html.Span("LinkedIn"),
                            ], href="https://www.linkedin.com/in/luizviniciuss/", target="_blank", className="author-social-link author-linkedin"),
                            html.A([
                                html.Span("💻", className="link-icon"),
                                html.Span("GitHub"),
                            ], href="https://github.com/lluizdevv/Observatorio-da-Gestao-Municipal-em-Saneamento", target="_blank", className="author-social-link author-github"),
                        ], className="author-links-row"),
                    ], className="author-info-wrapper"),
                ], className="author-card"),
            ], className="editorial-card-wrapper"),
        ], className="editorial-section-last section-about-autor"),
    ], className="about-page container")


def _editorial_dim_card(number, title, desc):
    return html.Div([
        html.Span(number, className="dim-card-number"),
        html.H4(title, className="dim-card-title"),
        html.P(desc, className="dim-card-desc"),
    ], className="editorial-dim-card")


def _flow_box(title, desc):
    return html.Div([
        html.H5(title, className="flow-box-title"),
        html.P(desc, className="flow-box-desc"),
    ], className="flow-box")


def _step_card(step_num, title, text):
    return html.Div([
        html.Div(step_num, className="step-num-badge"),
        html.H4(title, className="step-card-title"),
        html.P(text, className="step-card-text"),
    ], className="methodology-step-card")


def _resource_item(icon, title, desc, url, component_id=None):
    link_props = {
        "href": url,
        "className": "resource-item-card",
        "target": "_blank" if url != "#" else None,
    }
    if component_id:
        link_props["id"] = component_id

    return html.A([
        html.Div(icon, className="resource-item-icon"),
        html.Div([
            html.H5(title, className="resource-item-title"),
            html.P(desc, className="resource-item-desc"),
            html.Span("Acessar recurso →", className="resource-item-link"),
        ], className="resource-item-content"),
    ], **link_props)
