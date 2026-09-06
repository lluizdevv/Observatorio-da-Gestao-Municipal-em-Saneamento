# 🎲 Observatório da Gestão Municipal em Saneamento

**Maturidade da gestão municipal: observado versus esperado**

Plataforma analítica e exploratória desenvolvida para o **2º Concurso de Reúso de Dados Abertos da Controladoria-Geral da União (Edital CGU nº 46/2026)**, que compara a maturidade observada da governança municipal em saneamento básico com um escore esperado, estimado por um modelo de Machine Learning, a partir do perfil socioeconômico de cada um dos 5.570 municípios brasileiros. O dashboard reúne, em quatro módulos interativos, a apresentação institucional do projeto, a consulta individualizada por município, painéis territoriais agregados (Brasil, Região e Estado) e um explorador de dados livre para cruzamento de variáveis — todos construídos sobre a mesma base de 165 colunas, unificada a partir de quatro fontes oficiais de dados abertos.

<img width="1435" height="325" alt="image" src="https://github.com/user-attachments/assets/b8aababc-e4c8-4282-9c9e-3fb5c39a596b" />

> ⚠️ **Aviso de rigor metodológico**: a classificação apresentada é **comparativa**, não causal. Ela mede o desempenho de um município em relação ao que um modelo estatístico esperaria dado seu perfil socioeconômico — não é um veredito de eficiência, competência ou qualidade de gestão.

---

## Sumário

- [Objetivo](#objetivo)
- [Funcionalidades](#funcionalidades)
- [Metodologia](#metodologia)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Fontes de dados](#fontes-de-dados)
- [Variáveis principais](#variáveis-principais)
- [Como executar localmente](#como-executar-localmente)
- [Limitações](#limitações)
- [Recursos e transparência](#recursos-e-transparência)
- [Autor](#autor)
- [Licença](#licença)

---

## Objetivo

- **Explorar**: navegar individualmente por município, identificando quais dimensões de governança em saneamento estão ativas segundo o SINISA.
- **Comparar**: contrastar o índice de maturidade observado com a expectativa estatística modelada a partir do perfil socioeconômico do município.
- **Diagnosticar**: oferecer panoramas territoriais agregados (Brasil, Grandes Regiões e Unidades da Federação) para apoiar a formulação de políticas públicas e o controle social.

## Funcionalidades

O dashboard é organizado em quatro abas, cada uma voltada a um tipo de uso analítico:

### 📘 Sobre o Projeto
Apresentação institucional da iniciativa: contexto do concurso, objetivo, as 8 dimensões de governança que compõem o índice de maturidade, a metodologia em 5 etapas (observado × esperado × resíduo × classificação) e a seção de **Dados e Transparência**, com acesso direto ao dataset final, ao dicionário de variáveis e aos notebooks de integração e de Machine Learning.

### 🔍 Consulta Municipal
Busca individualizada por município (nome ou UF), retornando:
- índice observado, índice esperado pelo modelo, resíduo analítico e classificação comparativa;
- gráfico de comparação observado × esperado na escala de 0 a 8;
- contexto socioeconômico (população, receita per capita, taxa de aprovação escolar, receita orçamentária total);
- as 8 dimensões de governança em saneamento (regulação, política municipal, plano, PMGIRS, sistema de informações, ouvidoria, conselho), cada uma sinalizada como presente ou ausente.

### 🗺️ Panorama Territorial
Visão agregada por nível territorial — Brasil, Região ou Estado (UF) — com:
- métricas consolidadas (total de municípios, cobertura de dados, maturidade média, previsto médio, resíduo médio, % acima/abaixo do esperado);
- mapa coroplético e ranking dos estados pela métrica escolhida;
- distribuição do índice de maturidade e classificação comparativa de gestão;
- dispersão socioeconômica (receita per capita × maturidade observada);
- destaques dos municípios com maior resíduo positivo e negativo (maturidade muito acima ou muito abaixo da estimativa).

### 📊 Explorar Dados
Ambiente de exploração analítica livre, para cruzar qualquer combinação de variáveis do modelo e do perfil socioeconômico municipal:
- seleção livre dos eixos X e Y, variável de cor/agrupamento e tipo de gráfico (dispersão, barra, box plot, histograma);
- filtros por região, UF e classificação de gestão;
- aviso automático de cobertura de dados sempre que a variável selecionada tiver registros ausentes.

## Metodologia

1. **Integração dos dados** — unificação de quatro bases oficiais (SINISA, IBGE, SICONFI/Tesouro Nacional e INEP), casadas pelo código IBGE de 7 dígitos.
2. **Construção do índice** — soma normalizada de 8 dimensões de governança em saneamento (leis, planos, conselhos, regulação, ouvidoria, sistema de informações), resultando em um escore de 0 a 8.
3. **Modelagem preditiva** — regressão (Ridge) treinada sobre o perfil socioeconômico do município (receita per capita, população, IDHM, grau de urbanização, taxa de aprovação escolar), com previsões calculadas **fora da amostra** (out-of-fold), para evitar resíduos artificialmente pequenos.
4. **Cálculo do resíduo** — `resíduo = índice observado − índice previsto`.
5. **Classificação comparativa** — a margem de classificação é definida pelo erro médio absoluto (MAE) do modelo fora da amostra, não por um corte arbitrário em zero:
   - `Maturidade acima do esperado`
   - `Maturidade dentro do esperado`
   - `Maturidade abaixo do esperado`
   - `Sem dados suficientes` (municípios que não responderam ao módulo do SINISA)

## Estrutura do repositório

```text
dashboard_saneamento/
├── app.py                                    # Ponto de entrada: inicialização do Dash e layout raiz
├── src/
│   ├── __init__.py
│   ├── data_loader.py                        # Carga, limpeza e padronização da base municipal
│   ├── components.py                         # Design system: cards, badges, seções editoriais
│   └── callbacks.py                          # Roteamento de abas, filtros e gráficos interativos
├── data/
│   └── base_municipal_com_classificacao_ml.csv  # Base municipal integrada (5.570 linhas, 165 colunas)
├── assets/                                   # CSS, imagens e malha geográfica (GeoJSON)
├── requirements.txt                          # Dependências mínimas de execução
├── README.md
└── .gitignore
```

> **Nota sobre os imports**: como `data_loader.py`, `components.py` e `callbacks.py` agora vivem dentro de `src/`, o `app.py` deve importá-los como pacote (`from src.data_loader import load_data`, etc.), e `src/data_loader.py` deve apontar o caminho do CSV para `../data/base_municipal_com_classificacao_ml.csv` em vez do diretório raiz.

## 🛰️ Fontes de dados
 
| Base | Órgão | Uso no projeto |
|---|---|---|
| 🗺️ [IBGE — Localidades](https://servicodados.ibge.gov.br/api/docs/localidades?versao=1) | Instituto Brasileiro de Geografia e Estatística | Código IBGE, UF e Região de cada município |
| 💰 [SICONFI](http://apidatalake.tesouro.gov.br/docs/siconfi/) | Secretaria do Tesouro Nacional | Receita municipal (Declaração de Contas Anuais) |
| 🎓 [INEP — Taxas de Rendimento Escolar](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-rendimento-escolar) | Instituto Nacional de Estudos e Pesquisas Educacionais | Taxa de aprovação no ensino fundamental |
| 🚰 [SINISA — Diagnóstico de Gestão Municipal 2024](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa) | Ministério das Cidades | Dimensões de governança, estrutura institucional, serviços e investimentos em saneamento |

## Variáveis principais

| Variável | Descrição |
|---|---|
| `indice_maturidade_saneamento` | Índice observado de maturidade em gestão de saneamento (0 a 8) |
| `previsto_oof` | Índice esperado, estimado pelo modelo (previsão out-of-fold) |
| `residuo_oof` | Resíduo do modelo: `indice_maturidade_saneamento − previsto_oof` |
| `classificacao_gestao` | Categoria comparativa final (ver [Metodologia](#metodologia)) |
| `receita_per_capita` | Receita municipal total ÷ população (R$/habitante) |
| `idhm` | Índice de Desenvolvimento Humano Municipal |
| `grau_urbanizacao` | Proporção da população residente em área urbana |

A relação completa das 165 colunas da base, com descrição e base de origem de cada uma, está no [Dicionário de Variáveis](https://docs.google.com/spreadsheets/d/1pGq2Lo92O31m8aeHRKajbapyUwbWOitEpWP8gkudOuE/edit?usp=sharing).

## Como executar localmente

```bash
# Clonar o repositório
git clone https://github.com/lluizdevv/Observatorio-da-Gestao-Municipal-em-Saneamento.git
cd dashboard_saneamento

# Criar e ativar um ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
.\venv\Scripts\Activate.ps1     # Windows PowerShell

# Instalar as dependências
pip install -r requirements.txt

# Executar a aplicação
python app.py
```

Acesse `http://127.0.0.1:8050/` no navegador.

**Requisitos**: Python 3.9+, `dash`, `dash-bootstrap-components`, `plotly`, `pandas`, `numpy`. Não é necessária nenhuma chave de API, banco de dados ou serviço pago — todo o processamento ocorre localmente em memória, a partir do CSV em `data/`.

## Limitações

- As respostas do SINISA decorrem de auto-declaração dos municípios; 863 municípios (15,5%) não responderam ao módulo de Gestão Municipal em 2024 e aparecem como `Sem dados suficientes`.
- O modelo estatístico capta associações descritivas, não relações de causa e efeito.
- Municípios com receita per capita muito atípica (ex.: royalties de petróleo/mineração e baixa população) podem gerar estimativas menos precisas — o resíduo desses casos deve ser interpretado com cautela.
- A ausência de dado nunca é tratada como zero: médias, percentuais e classificações consideram estritamente o subconjunto de municípios com registro válido.

## Recursos e transparência

- 📊 [Dataset final consolidado](data/base_municipal_com_classificacao_ml.csv)
- 📖 [Dicionário de variáveis](https://docs.google.com/spreadsheets/d/1pGq2Lo92O31m8aeHRKajbapyUwbWOitEpWP8gkudOuE/edit?usp=sharing)
- 🔗 [Notebook de integração das bases (Colab)](https://colab.research.google.com/drive/1v3HcafOW9EXENzyIVFA95XNGoPhP44gn?usp=sharing)
- 🤖 [Notebook de Machine Learning (Colab)](https://colab.research.google.com/drive/1sf8G4n3HRgtC7nYmXOFbnHSzVQHRTHgK?usp=sharing)

##  👤Autor

**Luiz Vinicius de Lima Santos**
Desenvolvedor & Autor do Projeto — Sistemas de Informação, Universidade Federal Rural de Pernambuco (UFRPE)

[LinkedIn](https://www.linkedin.com/in/luizviniciuss/) · [GitHub](https://github.com/lluizdevv/Observatorio-da-Gestao-Municipal-em-Saneamento)

## 📄Licença

Projeto submetido ao 2º Concurso de Reúso de Dados Abertos da Controladoria-Geral da União (Edital CGU nº 46/2026). Os dados utilizados são públicos e abertos, conforme as fontes listadas acima.
