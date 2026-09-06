"""
app.py — Ponto de entrada do aplicativo Dash institucional.
Observatório da Gestão Municipal do Saneamento: Maturidade da gestão municipal (observado versus esperado).
"""

import logging
import os
from dash import Dash, html
from src.data_loader import load_data
from src.components import create_sidebar, create_footer
from src.callbacks import register_callbacks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("observatorio_saneamento")

# 1. Carregamento dos dados na inicialização
logger.info("Carregando e validando base de dados municipal...")
DF = load_data()
logger.info("Base municipal pronta: %d municípios carregados.", len(DF))

# 2. Inicialização do App Dash com SEO e Responsividade
app = Dash(
    __name__,
    title="Observatório da Gestão Municipal em Saneamento | Maturidade da Gestão Municipal",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0"},
        {
            "name": "description",
            "content": "Plataforma analítica e exploratória da maturidade de governança em saneamento básico municipal no Brasil: observado versus esperado."
        },
        {"name": "author", "content": "Observatório da Gestão Municipal em Saneamento"},
    ],
)

# 3. Layout Raiz da Aplicação com Sidebar Vertical à Esquerda
app.layout = html.Div([
    create_sidebar(),
    html.Div([
        html.Main(id="content", className="app-main-content"),
        create_footer(),
    ], className="app-main-layout"),
], className="app-wrapper app-sidebar-layout")

# 4. Registro de Callbacks Modulares
register_callbacks(app, DF)

# Servidor WSGI usado pelo Gunicorn no Render.
server = app.server

# 5. Execução Local
if __name__ == "__main__":
    app.run(
        debug=True,
        dev_tools_ui=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
    )
