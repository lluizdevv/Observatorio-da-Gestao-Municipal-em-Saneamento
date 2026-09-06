# Observatório da Gestão Municipal do Saneamento
### Maturidade da gestão municipal: observado versus esperado

---

## 1. Descrição do Projeto

O **Observatório da Gestão Municipal do Saneamento** é uma plataforma analítica e interativa desenvolvida em Python (Dash + Plotly + CSS puro) para investigação da governança municipal no saneamento básico no Brasil. 

A aplicação confronta a maturidade observada da gestão pública com um escore esperado estimado por modelos de Machine Learning (validação cruzada out-of-fold), considerando as características socioeconômicas e a disponibilidade de receita de cada um dos 5.570 municípios brasileiros.

O produto foi concebido com padrão de **publicação e diagnóstico institucional**, priorizando transparência estatística, clareza editorial, rigor metodológico e ausência de linguagem causal.

---

## 2. Objetivo

- **Explorar:** Permitir a navegação individualizada por município, identificando quais dimensões de governança estão ativas segundo o SINISA.
- **Comparar:** Contrastar o índice observado com a expectativa estatística modelada segundo o perfil socioeconômico municipal.
- **Diagnosticar:** Oferecer panoramas territoriais agregados (Brasil consolidado, Grandes Regiões e Unidades da Federação) e mapa coroplético para apoiar tomadores de decisão na formulação de políticas públicas.

---

## 3. Estrutura de Arquivos

```text
dashboard_saneamento/
│
├── app.py                  # Ponto de entrada: inicialização do Dash e layout mestre
├── src/
│   ├── __init__.py         # Pacote da aplicação
│   ├── data_loader.py      # Leitura segura, padronização do código IBGE e validações
│   ├── components.py       # Design system: cards, badges, bullet charts e seções editoriais
│   └── callbacks.py        # Roteamento de abas, filtros territoriais e explorador analítico
├── requirements.txt        # Dependências mínimas de execução
├── README.md               # Documentação técnica e metodológica
│
├── data/
│   └── base_municipal_com_classificacao_ml.csv # Base municipal integrada
│
├── assets/
│   ├── style.css           # Estilização institucional em CSS puro (sem frameworks pesados)
│   ├── brazil_states.geojson # Malha geográfica offline das 27 UFs para mapas coropléticos
│   ├── autor.jpg           # Foto exibida na seção de autoria
│   ├── logo.png            # Identidade visual da sidebar
│   ├── modelo_maturidade_saneamento_v2.pkl # Artefato do melhor modelo
│   └── arquivos-referencia/ # Imagens de apoio não utilizadas pela aplicação
```

---

## 4. Requisitos de Sistema

- **Python:** 3.9 ou superior
- **Bibliotecas:**
  - `dash >= 2.14.0`
  - `plotly >= 5.18.0`
  - `pandas >= 2.0.0`
  - `numpy >= 1.24.0`

Não requer chaves de API externa, banco de dados ou serviços pagos. Todo o processamento analítico e espacial ocorre localmente em memória.

---

## 5. Instalação

Clone ou acerte o diretório do projeto e crie um ambiente virtual (recomendado):

```bash
# Criação do ambiente virtual
python -m venv venv

# Ativação do ambiente (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Ativação do ambiente (Linux/macOS)
source venv/bin/activate

# Instalação das dependências
pip install -r requirements.txt
```

---

## 6. Como Executar

Execute o comando principal a partir da raiz do repositório:

```bash
python app.py
```

Abra o navegador no endereço indicado (por padrão: `http://127.0.0.1:8050/`).

---

## 7. Fonte dos Dados

Os dados foram integrados a partir de registros públicos oficiais:
- **SINISA (Sistema Nacional de Informações sobre Saneamento):** Módulo de Gestão Municipal 2024 (Governança, Regulação, Planos e Controle Social).
- **IBGE (Instituto Brasileiro de Geografia e Estatística):** Dados populacionais e malha geográfica municipal.
- **STN / Siconfi (Secretaria do Tesouro Nacional):** Finanças públicas e arrecadação de receitas orçamentárias municipais.
- **INEP (Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira):** Taxas de rendimento e aprovação escolar.

O arquivo original `base_municipal_com_classificacao_ml.csv` contém 5.570 municípios e é lido estritamente em modo de leitura (sem sobregravação ou alteração em disco). O carregador acrescenta variáveis derivadas em memória para as análises do dashboard.

---

## 8. Variáveis Principais

### Núcleo do Modelo
- `indice_maturidade_saneamento`: Valor observado da gestão (inteiro de 0 a 8), correspondente à soma de 8 dimensões de governança presentes no município.
- `previsto_oof`: Índice esperado estimado pelo modelo estatístico a partir das características socioeconômicas, utilizando predições fora da amostra (out-of-fold).
- `residuo_oof`: Diferença calculada entre o observado e o previsto:
  $$\text{residuo\_oof} = \text{indice\_maturidade\_saneamento} - \text{previsto\_oof}$$
- `classificacao_gestao`: Categoria comparativa atribuída ao município:
  - *Maturidade acima do esperado* (resíduo positivo relevante)
  - *Maturidade dentro do esperado* (desempenho condizente com o perfil)
  - *Maturidade abaixo do esperado* (resíduo negativo relevante)
  - *Sem dados suficientes* (municípios sem declaração ao SINISA)

### As 8 Dimensões de Governança
1. Entidade de Regulação para Abastecimento de Água
2. Entidade de Regulação para Esgotamento Sanitário
3. Lei da Política Municipal de Saneamento Básico (Lei Federal 11.445/07)
4. Plano de Saneamento Básico formalmente aprovado
5. Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS - Lei 12.305/10)
6. Sistema público de informações sobre saneamento
7. Ouvidoria municipal ou canal de manifestação cidadã
8. Conselho Municipal com atuação específica em saneamento

### Indicadores Socioeconômicos
- `populacao`: População residente municipal.
- `receita_per_capita`: Receita total anual dividida pela população (R$/habitante).
- `taxa_aprovacao_ensino_fundamental`: Percentual de aprovação escolar no ensino fundamental (%).
- `receita_total`: Arrecadação total do município (R$).

---

## 9. Metodologia

1. **Padronização Identificadora:** Utilização de `codigo_ibge` como chave primária de 7 dígitos (`zfill(7)`), eliminando sufixos `.0` e inconsistências de tipagem.
2. **Construção do Índice de Maturidade:** Escore quantitativo direto (0 a 8) sintetizando respostas afirmativas às oito dimensões de governança.
3. **Modelagem Preditiva Supervisionada:** Algoritmo treinado com dados socioeconômicos para projetar o índice de maturidade esperado, com avaliação em validação cruzada out-of-fold.
4. **Cálculo de Resíduos e Faixas:** Definição da classificação a partir do desvio relativo entre a governança observada e a esperada.

> **Observação de Rigor:** A classificação é estritamente comparativa e depende do modelo e das variáveis utilizadas. Ela **não constitui prova causal** de eficiência, virtude ou qualidade da gestão municipal.

---

## 10. Limitações

- As respostas do SINISA decorrem de auto-declaração dos entes municipais nas pesquisas anuais.
- O modelo estatístico capta associações descritivas multidimensionais, não relações de causa e efeito.
- Variações extremas de receita per capita (ex: municípios com royalties de petróleo e baixa população) geram assimetrias que devem ser interpretadas com cautela analítica.

---

## 11. Observações sobre Dados Ausentes

- Na base, 863 municípios (15,5%) não possuem retorno do Módulo Gestão do SINISA, figurando com valor ausente nas variáveis de governança e classificados formalmente como **"Sem dados suficientes"**.
- O sistema **nunca trata ausência de dado como zero**. Músicas, médias, percentuais e gráficos consideram estritamente o subconjunto de cidades com registros válidos.
- Quando um campo individual não possui informação, a interface exibe explicitamente o rótulo **"Sem dados"** ou **"—"**.
