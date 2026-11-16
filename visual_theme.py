import base64
import os
import streamlit as st

@st.cache_data(show_spinner=False)
def localizar_imagem(nome_imagem, pastas_adicionais=None):
    """
    Busca por arquivos de imagem priorizando a pasta 'visual'.
    Aceita nomes como 'fundo', 'fundo.jpg', 'logo'.
    """
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    diretorio_visual = os.path.join(diretorio_base, "visual")
    diretorio_pai = os.path.dirname(diretorio_base)
    diretorio_pai_visual = os.path.join(diretorio_pai, "visual")
    
    locais_busca = [
        diretorio_visual,
        diretorio_pai_visual,
        os.path.join(os.getcwd(), "visual"),
        diretorio_base,
        diretorio_pai,
        os.getcwd()
    ]
    if pastas_adicionais:
        locais_busca = list(pastas_adicionais) + locais_busca

    extensoes = ["", ".jpeg", ".jpg", ".png", ".webp", ".svg"]
    
    # Se já vier com extensão, tenta ela primeiro
    nome_puro, ext_original = os.path.splitext(nome_imagem)
    if ext_original:
        exts_testar = [ext_original] + [e for e in extensoes if e != ext_original]
    else:
        exts_testar = extensoes

    for pasta in locais_busca:
        if not os.path.exists(pasta):
            continue
        for ext in exts_testar:
            candidato = os.path.join(pasta, f"{nome_puro}{ext}")
            if os.path.isfile(candidato):
                return candidato

    return None

@st.cache_data(show_spinner=False)
def obter_imagem_base64(caminho_arquivo):
    """Retorna URI em base64 da imagem com mimetype apropriado."""
    if not caminho_arquivo or not os.path.isfile(caminho_arquivo):
        return ""
    
    ext = os.path.splitext(caminho_arquivo)[1].lower()
    mimes = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".webp": "image/webp"
    }
    mime = mimes.get(ext, "image/jpeg")
    
    try:
        with open(caminho_arquivo, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""

def gerar_css_estilo_completo():
    """Gera o CSS de estilo e papel de parede com padrão Glassmorphism moderno."""
    caminho_fundo = localizar_imagem("fundo")
    fundo_uri = obter_imagem_base64(caminho_fundo) if caminho_fundo else ""
    
    css_wallpaper = f"""
        /* === PAPEL DE PAREDE UNIVERSAL (COM GRADIENTE OVERLAY SUAVE PARA CONFORTO VISUAL) === */
        html, body, .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stMain,
        section.main {{
            background-image: linear-gradient(rgba(11, 15, 25, 0.20), rgba(11, 15, 25, 0.35)), url("{fundo_uri}") !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: linear-gradient(rgba(11, 15, 25, 0.20), rgba(11, 15, 25, 0.35)), url("{fundo_uri}");
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            z-index: 0;
            pointer-events: none;
        }}
    """ if fundo_uri else """
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
            background-color: #0b0f19 !important;
        }
    """

    css_completo = f"""
    <style>
        /* =========================================================
           1. PAPEL DE PAREDE E ESTRUTURA GERAL
           ========================================================= */
        {css_wallpaper}

        /* Top header e containers transparentes para revelar o papel de parede */
        [data-testid="stHeader"] {{
            background-color: transparent !important;
            background: transparent !important;
        }}

        .stMainBlockContainer,
        .block-container {{
            background-color: transparent !important;
            background: transparent !important;
        }}

        /* =========================================================
           2. TIPOGRAFIA DE ALTO CONTRASTE
           ========================================================= */
        html, body, [class*="css"], .stApp, .stMarkdown, .stMarkdown p,
        h1, h2, h3, h4, h5, h6, p, span, label, li, a, div, b, strong, em, small {{
            color: #FFFFFF !important;
            opacity: 1 !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
        }}

        /* Títulos principais destacados e nítidos */
        h1, h2, h3, h4, h5, h6 {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
            opacity: 1 !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85) !important;
        }}

        /* Textos de apoio, legendas e subtítulos */
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] p,
        .stCaption,
        small {{
            color: #CBD5E1 !important;
            opacity: 1 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7) !important;
        }}

        /* Rótulos de campos e formulários */
        label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p {{
            color: #E2E8F0 !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }}

        /* Links em azul luminoso */
        a {{
            color: #60A5FA !important;
            text-decoration: underline;
        }}

        /* =========================================================
           3. PADRÃO GLASSMORPHISM: CONTAINERS COM BORDA
           ========================================================= */
        div[data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: transparent !important;
        }}

        /* =========================================================
           4. BLOCOS DE MÉTRICAS (st.metric)
           ========================================================= */
        div[data-testid="stMetric"],
        [data-testid="stMetric"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            padding: 14px 18px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetric"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 4px 0 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }}

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {{
            color: #CBD5E1 !important;
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] div {{
            color: #FFFFFF !important;
            font-size: 1.75rem !important;
            font-weight: 800 !important;
            opacity: 1 !important;
            text-shadow: 0 2px 6px rgba(0, 0, 0, 0.65) !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
            font-weight: 700 !important;
            opacity: 1 !important;
        }}

        /* =========================================================
           5. TABELAS E DATAFRAMES (.stDataFrame e st.table)
           ========================================================= */
        .stDataFrame,
        div[data-testid="stDataFrame"],
        [data-testid="stDataFrame"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            padding: 8px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
        }}
        div[data-testid="stDataFrame"] * {{
            color: #FFFFFF !important;
            opacity: 1 !important;
        }}

        [data-testid="stTable"],
        table,
        [data-testid="stTable"] table {{
            width: 100% !important;
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
            overflow: hidden !important;
        }}
        table th, [data-testid="stTable"] th {{
            color: #FFFFFF !important;
            background-color: rgba(30, 41, 59, 0.95) !important;
            font-weight: 700 !important;
            opacity: 1 !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            padding: 10px 14px !important;
            text-align: left !important;
        }}
        table td, [data-testid="stTable"] td {{
            color: #F8FAFC !important;
            background-color: rgba(15, 23, 42, 0.85) !important;
            opacity: 1 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            padding: 8px 12px !important;
        }}
        table tr:hover td {{
            background-color: rgba(51, 65, 85, 0.90) !important;
        }}

        /* =========================================================
           6. FORMULÁRIOS, EXPANDERS E UPLOADS
           ========================================================= */
        [data-testid="stForm"],
        form[data-testid="stForm"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
            padding: 16px 20px !important;
        }}

        div[data-testid="stExpander"],
        details[data-testid="stExpander"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
        }}
        div[data-testid="stExpander"] summary {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}

        [data-testid="stFileUploader"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px dashed rgba(255, 255, 255, 0.22) !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
            padding: 14px 18px !important;
        }}
        [data-testid="stFileUploader"] * {{
            color: #FFFFFF !important;
        }}
        [data-testid="stFileUploaderDropzoneInstructions"] * {{
            color: #E2E8F0 !important;
        }}

        [data-testid="stAlert"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            background-color: rgba(15, 23, 42, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.40) !important;
        }}
        [data-testid="stAlert"] * {{
            color: #FFFFFF !important;
        }}

        /* =========================================================
           7. CAMPOS DE ENTRADA, SELECTS E MENUS
           ========================================================= */
        input, textarea, [data-baseweb="input"], [data-baseweb="base-input"] {{
            color: #FFFFFF !important;
            background-color: rgba(30, 41, 59, 0.88) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 8px !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
        }}
        input::placeholder, textarea::placeholder {{
            color: #94A3B8 !important;
            opacity: 1 !important;
        }}
        div[data-baseweb="select"] {{
            background-color: rgba(30, 41, 59, 0.88) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 8px !important;
        }}
        div[data-baseweb="select"] * {{
            color: #FFFFFF !important;
            background-color: transparent !important;
        }}
        ul[data-baseweb="menu"], div[data-baseweb="popover"], [data-baseweb="popover"] > div {{
            background-color: #0F172A !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6) !important;
        }}
        li[data-baseweb="menu-item"] {{
            color: #FFFFFF !important;
        }}
        li[data-baseweb="menu-item"]:hover {{
            background-color: #1E293B !important;
        }}

        /* =========================================================
           8. BOTÕES E CONTROLES DE INTERAÇÃO
           ========================================================= */
        .stButton, .stDownloadButton {{
            width: 100% !important;
            display: flex !important;
        }}
        .stButton > button,
        .stDownloadButton > button {{
            width: 100% !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            border-radius: 8px !important;
            font-size: 0.98rem !important;
            font-weight: 700 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            padding: 8px 16px !important;
            box-sizing: border-box !important;
            transition: all 0.2s ease !important;
            line-height: 1.2 !important;
        }}
        .stButton > button *,
        .stDownloadButton > button * {{
            font-size: 0.98rem !important;
            font-weight: 700 !important;
            text-align: center !important;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            color: #FFFFFF !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%) !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45) !important;
            transform: translateY(-1px) !important;
        }}
        .stButton > button[kind="secondary"] {{
            background-color: rgba(30, 41, 59, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            color: #FFFFFF !important;
        }}
        .stButton > button[kind="secondary"]:hover {{
            background-color: rgba(51, 65, 85, 0.95) !important;
            border-color: rgba(255, 255, 255, 0.35) !important;
            transform: translateY(-1px) !important;
        }}
        .stDownloadButton > button {{
            background: linear-gradient(135deg, #15803d 0%, #16a34a 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
        }}
        .stDownloadButton > button:hover {{
            background: linear-gradient(135deg, #166534 0%, #15803d 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 14px rgba(22, 163, 74, 0.4) !important;
            transform: translateY(-1px) !important;
        }}

        /* =========================================================
           9. ABAS (st.tabs)
           ========================================================= */
        div[data-baseweb="tab-list"] {{
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1.5px solid rgba(255, 255, 255, 0.16) !important;
            border-radius: 12px !important;
            padding: 8px 10px !important;
            gap: 12px !important;
            display: flex !important;
            width: 100% !important;
        }}
        button[data-baseweb="tab"] {{
            flex: 1 1 0 !important;
            color: #E2E8F0 !important;
            font-weight: 800 !important;
            font-size: 1.25rem !important;
            min-height: 62px !important;
            padding: 14px 18px !important;
            border-radius: 10px !important;
            border: 1.5px solid rgba(255, 255, 255, 0.14) !important;
            background: rgba(30, 41, 59, 0.70) !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
            transition: all 0.2s ease !important;
            text-align: center !important;
            justify-content: center !important;
            white-space: normal !important;
        }}
        button[data-baseweb="tab"]:hover {{
            background: rgba(59, 130, 246, 0.30) !important;
            border-color: rgba(96, 165, 250, 0.70) !important;
            color: #FFFFFF !important;
            transform: translateY(-2px) !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: #FFFFFF !important;
            font-weight: 900 !important;
            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 55%, #3B82F6 100%) !important;
            border: 2px solid #93C5FD !important;
            box-shadow: 0 6px 24px rgba(37, 99, 235, 0.65) !important;
            transform: translateY(-2px) !important;
        }}
        button[data-baseweb="tab"] p,
        button[data-baseweb="tab"] div,
        button[data-baseweb="tab"] span {{
            font-size: 1.25rem !important;
            font-weight: inherit !important;
            color: inherit !important;
            line-height: 1.3 !important;
            text-align: center !important;
        }}

        /* =========================================================
           10. RODAPÉ DE CRÉDITOS
           ========================================================= */
        .footer-creditos {{
            margin-top: 55px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.16);
            text-align: center;
            color: #E2E8F0 !important;
            font-size: 0.95rem;
            line-height: 1.6;
            position: relative;
            z-index: 1;
        }}
        .footer-creditos b {{
            color: #FFFFFF !important;
            font-size: 1.05rem;
            font-weight: 800;
        }}
        .footer-creditos span {{
            color: #CBD5E1 !important;
            font-weight: 600;
            font-size: 0.92rem;
        }}
    </style>
    """
    return css_completo

def aplicar_papel_de_parede_e_estilo():
    """
    Aplica o papel de parede 'fundo' em tela cheia com overlay suave para conforto visual,
    e estiliza globalmente todos os containers, métricas, tabelas, formulários e cartões
    com Glassmorphism semi-opaco.
    Bloqueia traduções indevidas do navegador (ex: Google Tradutor traduzindo 'Recibos' para 'Receitas').
    """
    bloqueio_traducao = """
    <meta name="google" content="notranslate">
    <meta name="googlebot" content="notranslate">
    <script>
        try {
            document.documentElement.setAttribute('lang', 'pt-BR');
            document.documentElement.setAttribute('translate', 'no');
            document.documentElement.classList.add('notranslate');
            if (window.parent && window.parent.document) {
                window.parent.document.documentElement.setAttribute('lang', 'pt-BR');
                window.parent.document.documentElement.setAttribute('translate', 'no');
                window.parent.document.documentElement.classList.add('notranslate');
            }
        } catch(e) {}
    </script>
    """
    st.markdown(bloqueio_traducao + gerar_css_estilo_completo(), unsafe_allow_html=True)

