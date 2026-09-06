"""
data_loader.py — Carregamento, validação e tratamento dos dados.
Observatório da Gestão Municipal do Saneamento: Maturidade da gestão municipal (observado versus esperado).
"""

from pathlib import Path
import json
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "base_municipal_com_classificacao_ml.csv"
GEOJSON_PATH = ROOT / "assets" / "brazil_states.geojson"

# ──────────────────────────────────────────────────────────────────────────────
# 1. MAPEAMENTO DAS 8 DIMENSÕES DE GOVERNANÇA (COMPOSIÇÃO DO ÍNDICE)
# ──────────────────────────────────────────────────────────────────────────────
# Mapeamento com nomes exatos das colunas da base após correção de encoding
DIMENSOES_GOVERNANCA = {
    "regulacao_agua": "Existência de entidade responsável pela regulação de serviços de abastecimento de água",
    "regulacao_esgoto": "Existência de entidade responsável pela regulação de serviços de esgotamento sanitário",
    "politica_municipal": "Existência de Lei que institui a Política Municipal de Saneamento Básico, conforme a Lei Federal nº 11.445/2007",
    "plano_saneamento": "Existência de Plano de Saneamento Básico (municipal e/ou regional), conforme a Lei Federal nº 11.445/2007",
    "pmgirs": "Existência de Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS), conforme a Lei Federal nº 12.305/2010",
    "sistema_informacoes": "Existência de sistema de informações sobre os  serviços de saneamento básico, de caráter público",
    "ouvidoria": "Existência de ouvidoria municipal ou central de atendimento ao cidadão para recebimento de reclamações ou manifestações sobre os serviços",
    "conselho_especifico": "Existência de Conselho Municipal com atuação específica para os serviços de saneamento básico",
}

DIMENSOES_INSTITUCIONAIS = {
    "regulacao_agua": DIMENSOES_GOVERNANCA["regulacao_agua"],
    "regulacao_esgoto": DIMENSOES_GOVERNANCA["regulacao_esgoto"],
    "regulacao_residuos": "Existência de entidade responsável pela regulação de serviços de limpeza urbana e manejo de resíduos sólidos",
    "regulacao_drenagem": "Existência de entidade responsável pela regulação de serviços de drenagem e manejo de águas pluviais urbanas",
    "consorcio_publico": "Participação do município em Consórcio Público com atuação em Saneamento Básico",
}

DIMENSOES_SERVICOS = {
    "servico_esgoto": "Existência de prestação de serviço público de esgotamento sanitário com rede coletora (independentemente de existir tratamento de esgoto). [No caso de empresa(s) terceirizada(s), é cadastrado o próprio município]",
}

# Rótulos institucionais curtos e informativos para a interface
ROTULOS_DIMENSOES = {
    "regulacao_agua": "Entidade de Regulação — Abastecimento de Água",
    "regulacao_esgoto": "Entidade de Regulação — Esgotamento Sanitário",
    "politica_municipal": "Política Municipal de Saneamento (Lei Federal 11.445/07)",
    "plano_saneamento": "Plano Municipal ou Regional de Saneamento Básico",
    "pmgirs": "Plano de Gestão Integrada de Resíduos Sólidos (PMGIRS)",
    "sistema_informacoes": "Sistema Público de Informações sobre Saneamento",
    "ouvidoria": "Ouvidoria Municipal / Central de Atendimento ao Cidadão",
    "conselho_especifico": "Conselho Municipal Específico de Saneamento",
}

# ──────────────────────────────────────────────────────────────────────────────
# 2. CATÁLOGO CURADO DE VARIÁVEIS PARA O EXPLORADOR DE DADOS
# ──────────────────────────────────────────────────────────────────────────────
# Agrupamento temático de variáveis analiticamente válidas (excluindo CNPJs,
# identificadores e textos administrativos longos)
VAR_CATALOG = {
    "Núcleo do Modelo": {
        "indice_maturidade_saneamento": "Índice de maturidade observado (0 a 8)",
        "previsto_oof": "Índice esperado pelo modelo (estimativa OOF)",
        "residuo_oof": "Resíduo (observado − esperado)",
    },
    "Perfil Socioeconômico": {
        "receita_per_capita": "Receita per capita (R$/hab.)",
        "populacao": "População residente (hab.)",
        "receita_total": "Receita total orçamentária (R$)",
        "taxa_aprovacao_ensino_fundamental": "Taxa de aprovação no Ensino Fundamental (%)",
        "idhm": "IDHM (PNUD)",
        "pib_municipio": "PIB do Município (R$ mil)",
        "grau_urbanizacao": "Grau de urbanização (%)",
        "investimento_per_capita_saneamento": "Investimento em saneamento per capita (R$/hab.)",
    },
}

FRIENDLY_NAMES = {
    "indice_maturidade_saneamento": "Índice de maturidade observado",
    "previsto_oof": "Índice previsto pelo modelo",
    "residuo_oof": "Resíduo (observado − previsto)",
    "receita_per_capita": "Receita municipal per capita (R$)",
    "populacao": "População residente",
    "receita_total": "Receita total municipal (R$)",
    "taxa_aprovacao_ensino_fundamental": "Taxa de aprovação — Ensino Fundamental (%)",
    "idhm": "Índice de Desenvolvimento Humano Municipal (IDHM)",
    "pib_municipio": "PIB do Município (R$ mil)",
    "grau_urbanizacao": "Índice de Urbanização (%)",
    "investimento_per_capita_saneamento": "Investimento em saneamento per capita (R$/hab.)",
}


def _clean_text(val):
    """Corrige sequências com dupla decodificação (mojibake) se presentes."""
    if isinstance(val, str):
        try:
            return val.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return val
    return val


def _parse_numero_br(valor):
    """Converte string numérica brasileira para float, retornando None quando inválida."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip().replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _find_column(df, *terms):
    """Localiza uma coluna textual por termos estáveis, tolerando encoding legado."""
    for column in df.columns:
        normalized = str(column).lower()
        if all(term.lower() in normalized for term in terms):
            return column
    return None


def load_geojson() -> dict:
    """Carrega o GeoJSON com os 27 estados brasileiros para o mapa offline."""
    if GEOJSON_PATH.exists():
        try:
            with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Falha ao ler GeoJSON local: %s", e)
    return {}


def load_data() -> pd.DataFrame:
    """
    Carrega o CSV da base municipal, inspeciona e sanitiza os dados em memória.
    Preserva estritamente o arquivo original em disco.
    """
    if not DATA_PATH.exists():
        logger.error("Arquivo de dados não encontrado: %s", DATA_PATH)
        return pd.DataFrame()

    # Leitura com encoding latin1 (comum em bases do governo brasileiro exportadas)
    df = pd.read_csv(DATA_PATH, encoding="latin1", low_memory=False)

    # 1. Tratamento dos nomes das colunas (remoção de espaços e limpeza de mojibake)
    clean_cols = {}
    for col in df.columns:
        c_clean = _clean_text(col.strip())
        clean_cols[col] = c_clean
    df.rename(columns=clean_cols, inplace=True)

    # 2. Padronização e sanitização do identificador municipal (codigo_ibge)
    # A base possui 'codigo_ibge' e 'Cod_IBGE'. Usamos 'codigo_ibge' como chave primária.
    id_col = "codigo_ibge" if "codigo_ibge" in df.columns else "Cod_IBGE"
    if id_col in df.columns:
        df["codigo_ibge_str"] = (
            df[id_col]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
            .str.zfill(7)
        )
    else:
        df["codigo_ibge_str"] = ""

    # 3. Tratamento de colunas de texto principais
    for col in ["Município", "UF", "Região", "classificacao_gestao"]:
        if col in df.columns:
            df[col] = df[col].apply(_clean_text)

    # 4. Conversão estrita de tipos numéricos do núcleo analítico
    numeric_vars = [
        "indice_maturidade_saneamento",
        "previsto_oof",
        "residuo_oof",
        "receita_per_capita",
        "populacao",
        "receita_total",
        "taxa_aprovacao_ensino_fundamental",
        "idhm",
        "grau_urbanizacao",
    ]
    for col in numeric_vars:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4.1. Variáveis socioeconômicas derivadas para o explorador de dados
    idhm_raw_col = _find_column(df, "desenvolvimento humano municipal", "idhm")
    pib_raw_col = _find_column(df, "produto interno bruto", "pib")
    urbana_raw_col = _find_column(df, "popula", "urbana residente")
    rural_raw_col = _find_column(df, "popula", "rural residente")

    if idhm_raw_col:
        df["idhm"] = df[idhm_raw_col].apply(_parse_numero_br)
    if pib_raw_col:
        df["pib_municipio"] = df[pib_raw_col].apply(_parse_numero_br)
    else:
        df["pib_municipio"] = np.nan
    df["populacao_urbana"] = df[urbana_raw_col] if urbana_raw_col else np.nan
    df["populacao_rural"] = df[rural_raw_col] if rural_raw_col else np.nan
    populacao_total = df["populacao_urbana"] + df["populacao_rural"]
    df["grau_urbanizacao"] = df["populacao_urbana"] / populacao_total.replace(0, np.nan)

    # 4.2. Conversão dos investimentos SINISA no formato numérico brasileiro
    investimento_agua_col = "Investimento total realizado pelo Município para o serviço de abastecimento de água"
    investimento_esgoto_col = "Investimento total realizado pelo Município para o serviço de esgotamento sanitário"
    if investimento_agua_col in df.columns:
        df["investimento_total_agua"] = df[investimento_agua_col].apply(_parse_numero_br)
    else:
        df["investimento_total_agua"] = np.nan
    if investimento_esgoto_col in df.columns:
        df["investimento_total_esgoto"] = df[investimento_esgoto_col].apply(_parse_numero_br)
    else:
        df["investimento_total_esgoto"] = np.nan
    df["investimento_total_agua_esgoto"] = df[["investimento_total_agua", "investimento_total_esgoto"]].sum(axis=1, min_count=1)
    df["investimento_per_capita_saneamento"] = df["investimento_total_agua_esgoto"] / df["populacao"]

    # 5. Tratamento de valores ausentes em classificacao_gestao
    if "classificacao_gestao" in df.columns:
        df["classificacao_gestao"] = df["classificacao_gestao"].fillna("Sem dados suficientes").str.strip()
        # Padroniza representação
        df.loc[df["classificacao_gestao"].isin(["", "nan", "NaN", "None"]), "classificacao_gestao"] = "Sem dados suficientes"

    # 6. Limpeza e sanitização das 8 colunas de governança
    for key, col_name in DIMENSOES_GOVERNANCA.items():
        if col_name in df.columns:
            df[col_name] = df[col_name].apply(_clean_text)
            # Padroniza respostas conhecidas (Sim, Não, Sem resposta)
            df[col_name] = df[col_name].apply(
                lambda v: "Sim" if str(v).strip().lower() in ["sim", "s"]
                else ("Não" if str(v).strip().lower() in ["não", "nao", "n"]
                      else ("Sem resposta" if pd.isna(v) or str(v).strip().lower() in ["nan", "none", ""]
                            else str(v).strip()))
            )

    # 7. Rótulo padronizado para pesquisa de autocomplete: "Município — UF"
    if "Município" in df.columns and "UF" in df.columns:
        df["municipio_label"] = df["Município"].fillna("—") + " — " + df["UF"].fillna("—")
    else:
        df["municipio_label"] = df["codigo_ibge_str"]

    # 8. Validação e auditoria automatizada em memória
    _validate_dataset(df)

    return df


def _validate_dataset(df: pd.DataFrame) -> None:
    """Inspeciona e valida a consistência metodológica dos dados."""
    linhas, colunas = df.shape
    duplicados = df["codigo_ibge_str"].duplicated().sum() if "codigo_ibge_str" in df.columns else 0

    logger.info("Dataset inspecionado: %d municípios, %d variáveis.", linhas, colunas)
    if duplicados > 0:
        logger.warning("Alerta de integridade: %d duplicidades em codigo_ibge.", duplicados)

    # Validação da relação metodológica: residuo_oof = indice_maturidade - previsto_oof
    if (
        "indice_maturidade_saneamento" in df.columns
        and "previsto_oof" in df.columns
        and "residuo_oof" in df.columns
    ):
        valid = df.dropna(subset=["indice_maturidade_saneamento", "previsto_oof", "residuo_oof"])
        diff = (valid["indice_maturidade_saneamento"] - valid["previsto_oof"]) - valid["residuo_oof"]
        max_err = diff.abs().max()
        logger.info("Validação do resíduo (obs - prev = residuo): desvio máximo = %.4e", max_err)


def get_municipality_options(df: pd.DataFrame) -> list:
    """Retorna lista ordenada de dicionários label/value para o dropdown de busca."""
    if "municipio_label" not in df.columns or "codigo_ibge_str" not in df.columns:
        return []
    valid = df.dropna(subset=["municipio_label"]).sort_values("municipio_label")
    options = []
    for _, row in valid.iterrows():
        options.append({
            "label": row["municipio_label"],
            "value": row["codigo_ibge_str"],
        })
    return options


def get_regiao_options(df: pd.DataFrame) -> list:
    """Retorna regiões únicas ordenadas."""
    if "Região" not in df.columns:
        return []
    return sorted([r for r in df["Região"].dropna().unique() if str(r).strip() != ""])


def get_uf_options(df: pd.DataFrame, regiao: str = None) -> list:
    """Retorna UFs disponíveis, opcionalmente filtradas pela região."""
    subset = df
    if regiao and regiao != "Todas":
        subset = df[df["Região"] == regiao]
    if "UF" not in subset.columns:
        return []
    return sorted([u for u in subset["UF"].dropna().unique() if str(u).strip() != ""])


def get_analytical_columns(df: pd.DataFrame) -> dict:
    """Retorna dicionário agrupado de variáveis numéricas analíticas válidas."""
    available = {}
    for group, vars_dict in VAR_CATALOG.items():
        group_items = {}
        for col, label in vars_dict.items():
            if col in df.columns:
                group_items[col] = label
        if group_items:
            available[group] = group_items
    return available


def friendly(col: str) -> str:
    """Retorna nome institucional amigável para uma variável."""
    return FRIENDLY_NAMES.get(col, col.replace("_", " ").capitalize())
