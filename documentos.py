"""
Módulo de Recibos — Sistema de Controle de Materiais
Controle sequencial, emissão para assinatura física e gestão de pendências de recibos.
Projeto demonstrativo para portfólio — dados fictícios.
"""

import html
import io
import json
import math
import os
import re
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

# Garante acesso aos módulos da raiz (ex.: visual_theme)
DIRETORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_MODULOS = DIRETORIO_RAIZ
if DIRETORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRETORIO_RAIZ)

import visual_theme

# =========================================================
# MODO OFFLINE — Dados armazenados apenas localmente (CSV)
# =========================================================
GOOGLE_SHEETS_HABILITADO = False
URL_PLANILHA_GOOGLE_RECIBOS = ""  # Não utilizado no modo offline

# =========================================================
# CAMINHOS LOCAIS (modo offline — sem integração com rede)
# =========================================================
CAMINHO_RECIBOS_REDE = ""        # Não utilizado
CAMINHO_DIGITALIZADOS_REDE = ""   # Não utilizado
ARQUIVO_CSV_REDE = ""             # Não utilizado

DIR_DADOS_LOCAL = os.environ.get("DIR_DADOS_RECIBOS", "").strip() or os.path.join(DIRETORIO_RAIZ, "dados", "recibos")
DIR_DIGITALIZADOS_LOCAL = os.path.join(DIR_DADOS_LOCAL, "digitalizados")

ARQUIVO_CSV_LOCAL = os.path.join(DIR_DADOS_LOCAL, "controle_recibos.csv")

COLUNAS_RECIBOS = [
    "numero",
    "numerador_completo",
    "data_elaboracao",
    "horario_elaboracao",
    "gerador_posto",
    "gerador_re",
    "gerador_nome",
    "gerador_completo",
    "gerador_unidade",
    "recebedor_posto",
    "recebedor_re",
    "recebedor_nome",
    "recebedor_completo",
    "recebedor_unidade",
    "destinatario",
    "assunto",
    "descricao_itens",
    "status_assinatura",  # "pendencia de assinatura" ou "Assinado"
    "nome_arquivo",
    "caminho_arquivo",
    "data_upload"
]

POSTOS_GRADUACOES = [
    "Assistente",
    "Analista",
    "Técnico",
    "Encarregado",
    "Supervisor",
    "Coordenador",
    "Gerente",
    "Diretor"
]

DESTINATARIOS_PREDEFINIDOS = [
    "Unidade Exemplo – Setor Administrativo",
    "Unidade Exemplo – Setor de Suprimentos",
    "Unidade Exemplo – Setor de Manutenção",
    "Unidade Exemplo – Setor de TI",
    "Unidade Exemplo – Operações",
    "Unidade Exemplo – Coordenação",
    "Unidade Exemplo – Almoxarifado Central",
    "Unidade Exemplo – Recursos Humanos",
    "Unidade Exemplo – Financeiro",
    "Unidade Exemplo – Diretoria Geral",
    "Unidade Exemplo – Logística",
    "Outro (Digitar manualmente)"
]

MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}


# =========================================================
# FUNÇÕES DE REDE E PERSISTÊNCIA DE RECIBOS
# =========================================================

def verificar_acesso_rede() -> bool:
    """Modo offline — sem acesso à rede."""
    return False

def garantir_diretorios():
    """Cria os diretórios locais de controle e armazenamento."""
    os.makedirs(DIR_DADOS_LOCAL, exist_ok=True)
    os.makedirs(DIR_DIGITALIZADOS_LOCAL, exist_ok=True)



def obter_maior_numero_recibo(df: pd.DataFrame) -> int:
    """Identifica o maior número existente a partir do histórico CSV local."""
    maior = 0
    if df is not None and not df.empty and "numero" in df.columns:
        s_num = pd.Series(df["numero"])
        nums_df = pd.to_numeric(s_num, errors="coerce").dropna()
        if not nums_df.empty:
            maior = max(maior, int(nums_df.max()))
    return maior

def obter_cliente_gspread():
    """Modo offline — sem integração com sistema."""
    return None, None


@st.cache_data(show_spinner=False, ttl=60)
def carregar_dados_planilha_recibos() -> tuple[list[dict], int, int, str | None]:
    """Modo offline — retorna lista vazia (dados carregados do CSV local)."""
    return [], 0, 0, "Modo offline — dados locais"


def salvar_recibo_na_planilha_google(
    numero: int,
    data_formatada: str,
    assunto: str,
    recebido_por: str,
    fornecido_por: str,
) -> tuple[bool, str, int | None]:
    """Modo offline — gravação apenas local (stub)."""
    return True, "Salvo localmente", 0


def atualizar_arquivo_na_planilha_google(numero: int, nome_arquivo: str) -> tuple[bool, str]:
    """Modo offline — atualização apenas local (stub)."""
    return True, "Atualizado localmente"


def excluir_recibo_na_planilha_google(numero: int) -> tuple[bool, str, int | None]:
    """Modo offline — exclusão apenas local (stub)."""
    try:
        carregar_dados_planilha_recibos.clear()
    except Exception:
        pass
    return True, "Excluído localmente", 0


def calcular_proximo_numero_recibo(df: pd.DataFrame) -> int:
    """Calcula o próximo número sequencial contínuo (modo offline)."""
    maior = obter_maior_numero_recibo(df)
    return maior + 1 if maior > 0 else 1


@st.cache_data(show_spinner=False, ttl=15)
def mapear_arquivos_digitalizados(rede_online: bool) -> dict[int, tuple[str, str]]:
    """Mapeia arquivos digitalizados apenas da pasta local."""
    EXTENSOES_VALIDAS = (".pdf", ".png", ".jpg", ".jpeg")
    mapa: dict[int, tuple[str, str]] = {}
    try:
        if os.path.isdir(DIR_DIGITALIZADOS_LOCAL):
            for nome_arq in os.listdir(DIR_DIGITALIZADOS_LOCAL):
                if not nome_arq.lower().endswith(EXTENSOES_VALIDAS):
                    continue
                m = re.match(r"^(\d{1,5})(?:[\.\-\s_]|$)", nome_arq.strip())
                if not m:
                    continue
                num_arq = int(m.group(1))
                caminho_arq = os.path.join(DIR_DIGITALIZADOS_LOCAL, nome_arq)
                if os.path.isfile(caminho_arq):
                    mapa[num_arq] = (nome_arq, caminho_arq)
    except Exception:
        pass
    return mapa


def carregar_historico_recibos() -> tuple[pd.DataFrame, bool, bool]:
    """
    Carrega o histórico de recibos do CSV local.
    Se não houver CSV, carrega os dados de exemplo (dados_exemplo.json).
    Retorna (df_recibos, rede_online=False, gsheets_online=False).
    """
    garantir_diretorios()

    df = pd.DataFrame(columns=COLUNAS_RECIBOS)

    # Tenta carregar do CSV local
    if os.path.exists(ARQUIVO_CSV_LOCAL):
        try:
            df = pd.read_csv(ARQUIVO_CSV_LOCAL, encoding="utf-8-sig")
        except Exception:
            pass

    # Se não houver dados no CSV, carrega os dados de exemplo
    if df.empty:
        caminho_exemplo = os.path.join(DIRETORIO_RAIZ, "dados_exemplo.json")
        if os.path.exists(caminho_exemplo):
            try:
                import json as _json
                with open(caminho_exemplo, "r", encoding="utf-8") as f_ex:
                    registros = _json.load(f_ex)
                df = pd.DataFrame(registros)
                # Salva como CSV para uso futuro
                salvar_historico_recibos(df)
            except Exception:
                pass

    for c in COLUNAS_RECIBOS:
        if c not in df.columns:
            df[c] = ""
    df = df.fillna("")

    if not df.empty and "numero" in df.columns:
        df["numero"] = pd.to_numeric(pd.Series(df["numero"]), errors="coerce").fillna(0).astype(int)

        # Sincroniza com arquivos digitalizados encontrados localmente
        arquivos_dig = mapear_arquivos_digitalizados(False)
        if arquivos_dig:
            for idx_row, row_d in df.iterrows():
                num_row = int(row_d["numero"])
                if num_row > 0 and num_row in arquivos_dig:
                    nome_dig, cam_dig = arquivos_dig[num_row]
                    df.at[idx_row, "status_assinatura"] = "Assinado"
                    nome_atual = str(row_d.get("nome_arquivo", "")).strip()
                    if not nome_atual:
                        df.at[idx_row, "nome_arquivo"] = nome_dig
                        df.at[idx_row, "caminho_arquivo"] = cam_dig

        df = df.sort_values(by="numero", ascending=False).reset_index(drop=True)

    return df, False, False


def sanitizar_dataframe_para_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Higieniza dados contra CSV / Formula Injection (Excel / LibreOffice)."""
    df_sanitizado = df.copy()
    for col in df_sanitizado.select_dtypes(include=["object"]).columns:
        df_sanitizado[col] = df_sanitizado[col].apply(
            lambda v: f"'{v}" if isinstance(v, str) and v.startswith(("=", "+", "@", "\t")) else v
        )
    return df_sanitizado


def salvar_historico_recibos(df: pd.DataFrame) -> bool:
    """Salva o DataFrame de recibos no CSV local com proteção contra Formula Injection."""
    garantir_diretorios()
    df_seguro = sanitizar_dataframe_para_csv(df)
    df_seguro.to_csv(ARQUIVO_CSV_LOCAL, index=False, encoding="utf-8-sig")
    return True

def sanitizar_nome_arquivo(texto: str) -> str:
    """Higieniza o nome para evitar caracteres proibidos e ataques de Path Traversal."""
    texto = str(texto or "").strip()
    texto = texto.replace("/", "-").replace("\\", "-").replace(":", " -")
    texto = re.sub(r'[<>*?"|]', '', texto)
    texto = re.sub(r'\.{2,}', '', texto)  # Remove sequências '..' contra path traversal
    texto = re.sub(r'\s+', ' ', texto).strip(" .")
    texto = os.path.basename(texto)
    return texto if texto else "RECIBO"


def formatar_data_extenso(data_obj) -> str:
    """Retorna data por extenso no formato formal de correspondência."""
    try:
        dia = data_obj.day
        mes = MESES_PT.get(data_obj.month, "novembro")
        ano = data_obj.year
        return f"{dia:02d} de {mes} de {ano}"
    except Exception:
        return datetime.now().strftime("%d/%m/%Y")


# =========================================================
# ESTILOS VISUAIS E IMPRESSÃO (A4 OFICIAL)
# =========================================================
def _injetar_estilos_recibos():
    st.markdown("""
    <style>
        .badge-pendencia-assinatura {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(239, 68, 68, 0.22);
            border: 1.5px solid #EF4444;
            color: #F87171 !important;
            font-size: 0.80rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.25);
        }
        .badge-assinado-verde {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.22);
            border: 1.5px solid #10B981;
            color: #34D399 !important;
            font-size: 0.80rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-doc-online {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.20);
            border: 1px solid rgba(52, 211, 153, 0.60);
            color: #6EE7B7 !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 9999px;
            letter-spacing: 0.4px;
        }
        .badge-doc-local {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(245, 158, 11, 0.20);
            border: 1px solid rgba(251, 191, 36, 0.60);
            color: #FCD34D !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 9999px;
            letter-spacing: 0.4px;
        }
        .card-metrica-recibo {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 14px 18px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        }
        .card-metrica-recibo .numero {
            font-size: 1.85rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .card-metrica-recibo .rotulo {
            font-size: 0.85rem;
            font-weight: 700;
            color: #CBD5E1;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }

        /* ── BOTÕES SUPERIORES DE NAVEGAÇÃO DO RECIBO (RIGIDAMENTE ALINHADOS E MESMA ALTURA) ── */
        div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_nav_tab_"]) {
            align-items: stretch !important;
            display: flex !important;
        }

        div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_nav_tab_"]) [data-testid="stColumn"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: stretch !important;
            height: auto !important;
        }

        div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_nav_tab_"]) .stButton,
        div[class*="st-key-btn_nav_tab_"] {
            display: flex !important;
            width: 100% !important;
            height: 100% !important;
        }

        div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_nav_tab_"]) .stButton > button,
        div[class*="st-key-btn_nav_tab_"] button {
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            height: 64px !important;
            min-height: 64px !important;
            max-height: 64px !important;
            padding: 8px 12px !important;
            border-radius: 10px !important;
            letter-spacing: 0.3px !important;
            line-height: 1.2 !important;
            text-align: center !important;
            justify-content: center !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.40) !important;
            transition: all 0.2s ease-in-out !important;
            border: 2px solid rgba(255, 255, 255, 0.20) !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }

        div[class*="st-key-btn_nav_tab_"] button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.60) !important;
            border-color: #93C5FD !important;
        }

        div[class*="st-key-btn_nav_tab_"] button[kind="primary"],
        div[class*="st-key-btn_nav_tab_"] button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 55%, #3B82F6 100%) !important;
            color: #FFFFFF !important;
            border: 2px solid #93C5FD !important;
            box-shadow: 0 6px 22px rgba(37, 99, 235, 0.70) !important;
        }

        div[class*="st-key-btn_nav_tab_"] button[kind="secondary"],
        div[class*="st-key-btn_nav_tab_"] button[data-testid="stBaseButton-secondary"] {
            background: rgba(30, 41, 59, 0.90) !important;
            color: #E2E8F0 !important;
        }

        div[class*="st-key-btn_nav_tab_"] button * {
            font-size: 1.10rem !important;
            font-weight: 800 !important;
            text-align: center !important;
            color: inherit !important;
        }

        /* ── BOTÃO DE GERAR RECIBO: ELEVADO, RIGIDAMENTE ALINHADO E DE ALTA VISIBILIDADE ── */
        [data-testid="stFormSubmitButton"] > button,
        div[class*="st-key-btn_submeter_recibo"] button {
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            padding: 12px 24px !important;
            height: 56px !important;
            min-height: 56px !important;
            max-height: 56px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 55%, #3B82F6 100%) !important;
            color: #FFFFFF !important;
            border: 2px solid rgba(147, 197, 253, 0.7) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.55) !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            transition: all 0.2s ease-in-out !important;
            margin-top: 12px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
        }

        [data-testid="stFormSubmitButton"] > button:hover,
        div[class*="st-key-btn_submeter_recibo"] button:hover {
            transform: translateY(-2px) !important;
            background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 50%, #60A5FA 100%) !important;
            box-shadow: 0 8px 28px rgba(37, 99, 235, 0.75) !important;
            border-color: #BFDBFE !important;
        }

        div[class*="st-key-btn_submeter_recibo"] button * {
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
        }

        /* ── CHECKBOX PREENCHER FISICAMENTE: MESMO TAMANHO E NEGRITO DO TÍTULO ── */
        div[class*="st-key-chk_preencher_fisicamente"] {
            margin-bottom: 0 !important;
        }
        div[class*="st-key-chk_preencher_fisicamente"] label {
            align-items: center !important;
            gap: 8px !important;
        }
        div[class*="st-key-chk_preencher_fisicamente"] label p,
        div[class*="st-key-chk_preencher_fisicamente"] label span,
        div[class*="st-key-chk_preencher_fisicamente"] label strong {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }

        /* ── BOTÕES DE SELEÇÃO DO FORMATO DOS MATERIAIS (ALTURA E ALINHAMENTO IDÊNTICOS) ── */
        div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_formato_"]) button {
            font-size: 1.05rem !important;
            font-weight: 750 !important;
            padding: 10px 18px !important;
            height: 52px !important;
            min-height: 52px !important;
            max-height: 52px !important;
            border-radius: 10px !important;
            letter-spacing: 0.4px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
        }

        /* ── ABAS SUPERIORES (ST.TABS): BOTÕES GRANDES DE LARGURA TOTAL E ALTA VISIBILIDADE ── */
        div[data-testid="stTabs"] div[role="tablist"],
        div[data-testid="stTabs"] div[data-baseweb="tab-list"] {
            display: flex !important;
            width: 100% !important;
            gap: 12px !important;
            padding: 6px 0 !important;
            border-bottom: none !important;
            margin-bottom: 24px !important;
        }

        div[data-testid="stTabs"] button[role="tab"],
        button[data-baseweb="tab"] {
            flex: 1 1 0 !important;
            font-size: 1.25rem !important;
            font-weight: 800 !important;
            padding: 16px 14px !important;
            min-height: 64px !important;
            border-radius: 12px !important;
            background: rgba(30, 41, 59, 0.85) !important;
            color: #E2E8F0 !important;
            border: 2px solid rgba(255, 255, 255, 0.20) !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
            transition: all 0.2s ease-in-out !important;
            cursor: pointer !important;
            text-align: center !important;
            justify-content: center !important;
            white-space: normal !important;
        }

        div[data-testid="stTabs"] button[role="tab"]:hover,
        button[data-baseweb="tab"]:hover {
            background: rgba(59, 130, 246, 0.35) !important;
            border-color: rgba(96, 165, 250, 0.75) !important;
            color: #FFFFFF !important;
            transform: translateY(-2px) !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 55%, #3B82F6 100%) !important;
            color: #FFFFFF !important;
            font-weight: 900 !important;
            border: 2.5px solid #93C5FD !important;
            box-shadow: 0 6px 26px rgba(37, 99, 235, 0.65) !important;
            transform: translateY(-2px) scale(1.01) !important;
        }

        /* Oculta linhas nativas de highlight do BaseWeb */
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"],
        div[data-testid="stTabs"] div[data-baseweb="tab-border"] {
            display: none !important;
        }

        /* Força herança de tamanho e peso para qualquer elemento de texto filho da aba */
        div[data-testid="stTabs"] button[role="tab"] *,
        button[data-baseweb="tab"] * {
            font-size: 1.25rem !important;
            font-weight: 800 !important;
            color: inherit !important;
            line-height: 1.3 !important;
            white-space: normal !important;
            text-align: center !important;
        }

        /* Folha-recibo: estilos agora embutidos diretamente no HTML gerado por gerar_html_recibo(). */
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# GERADOR DE MINUTA DO RECIBO — AUTO-CONTIDO (CSS INLINE + <style> EMBUTIDO)
# Layout por tabelas + position:absolute — funciona tanto no Streamlit
# quanto ao ser baixado/aberto isoladamente no navegador ou Word.
# =========================================================

# Estilos CSS embutidos que acompanham o HTML gerado (completamente independentes do Streamlit)
_CSS_RECIBO_EMBUTIDO = """
<style>
  @page {
    size: A4 portrait;
    margin: 0;
  }

  /* ── Wrapper principal da folha A4 (Tela) ── */
  .rec-folha {
    width: 210mm;
    max-width: 210mm;
    height: 297mm;
    min-height: 297mm;
    max-height: 297mm;
    overflow: hidden;
    box-sizing: border-box;
    position: relative;
    background: #FFFFFF !important;
    color: #000000 !important;
    font-family: 'Times New Roman', Times, serif !important;
    padding: 20mm 15mm 13mm 30mm;
    margin: 18px auto;
    border: 1px solid #D1D5DB;
    box-shadow: 0 8px 30px rgba(0,0,0,0.40);
    border-radius: 2px;
  }
  .rec-folha * {
    font-family: 'Times New Roman', Times, serif !important;
    color: #000000 !important;
    box-sizing: border-box;
  }

  /* ── Título centralizado ── */
  .rec-titulo {
    width: 100%;
    text-align: center;
    font-size: 26pt;
    font-weight: normal;
    margin: 26px 0 32px 0;
    letter-spacing: 0.2px;
  }

  /* ── Bloco inferior fixo no fundo ── */
  .rec-inferior {
    position: absolute;
    bottom: 13mm;
    left: 30mm;
    right: 15mm;
  }

  /* ── Tabela de assinaturas ── */
  .rec-tab-ass {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    font-size: 11pt;
    line-height: 1.55;
  }
  .rec-tab-ass td.rec-cell-ass {
    width: 48%;
    border: 1pt solid #000000 !important;
    vertical-align: top;
    padding: 6px 8px;
  }
  .rec-tab-ass td.rec-cell-sep {
    width: 4%;
  }

  /* ── Rodapé institucional ── */
  .rec-rodape {
    border-top: 1pt solid #000000;
    padding-top: 5px;
    text-align: center;
    font-size: 7.2pt;
    font-style: italic;
    width: 100%;
    line-height: 1.3;
  }

  /* ── Regras de impressão estritas para 1 ou múltiplas páginas ── */
  @media print {
    html, body {
      width: 210mm !important;
      height: auto !important;
      margin: 0 !important;
      padding: 0 !important;
      background: #FFFFFF !important;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body > *:not(#rec-print-root) { display: none !important; }
    #rec-print-root, #rec-print-root * { visibility: visible !important; }
    #rec-print-root {
      display: block !important;
      width: 210mm !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    .rec-folha {
      position: relative !important;
      width: 210mm !important;
      height: 297mm !important;
      min-height: 297mm !important;
      max-height: 297mm !important;
      margin: 0 !important;
      padding: 20mm 15mm 13mm 30mm !important;
      box-shadow: none !important;
      border: none !important;
      overflow: hidden !important;
      page-break-after: always !important;
      break-after: page !important;
      page-break-inside: avoid !important;
      break-inside: avoid !important;
    }
    .rec-folha:last-child {
      page-break-after: avoid !important;
      break-after: avoid !important;
    }
    .no-print, header, footer, nav, aside,
    .stAppHeader, .stToolbar, .stButton,
    [data-testid="stSidebar"] { display: none !important; }
  }
</style>
"""


def _gerar_html_conteudo_itens(itens, eh_tabela=False, titulo_tabela="", eh_primeira_folha=True) -> str:
    """Gera o HTML dos itens do recibo: como lista tradicional ou como grade/tabela estruturada."""
    if not eh_tabela:
        itens_html = "<br>".join([html.escape(str(p)) for p in itens]) if itens else ""
        return f"""
    <div style="font-size:12pt;line-height:1.6;margin-left:22mm;margin-bottom:20px;
                text-align:justify;font-family:'Times New Roman',Times,serif;color:#000;">
      {itens_html}
    </div>
"""

    linhas_tr = []
    if titulo_tabela and eh_primeira_folha:
        linhas_tr.append(f"""
      <tr>
        <td colspan="2" style="border:1pt solid #000000;text-align:center;font-weight:bold;font-size:12pt;padding:6px 8px;letter-spacing:0.5px;background:#F9FAFB;font-family:'Times New Roman',Times,serif;color:#000;">
          {html.escape(titulo_tabela)}
        </td>
      </tr>
""")

    linhas_tr.append("""
      <tr style="background:#F3F4F6;">
        <th style="border:1pt solid #000000;width:60px;text-align:center;padding:5px 6px;font-size:10pt;font-weight:bold;font-family:'Times New Roman',Times,serif;color:#000;">QTD</th>
        <th style="border:1pt solid #000000;text-align:left;padding:5px 12px;font-size:10pt;font-weight:bold;font-family:'Times New Roman',Times,serif;color:#000;">DISCRIMINAÇÃO DO MATERIAL</th>
      </tr>
""")

    for item in itens:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            qtd, mat = str(item[0]), str(item[1])
        elif isinstance(item, str) and "|" in item:
            partes = item.split("|", 1)
            qtd, mat = partes[0].strip(), partes[1].strip()
        else:
            qtd, mat = "", str(item)

        linhas_tr.append(f"""
      <tr>
        <td style="border:1pt solid #000000;width:60px;text-align:center;font-weight:bold;padding:5px 6px;vertical-align:middle;font-size:10.5pt;font-family:'Times New Roman',Times,serif;color:#000;">
          {html.escape(qtd)}
        </td>
        <td style="border:1pt solid #000000;padding:5px 12px;text-align:left;vertical-align:middle;font-size:10.5pt;font-family:'Times New Roman',Times,serif;color:#000;">
          {html.escape(mat)}
        </td>
      </tr>
""")

    return f"""
    <table border="0" cellspacing="0" cellpadding="0"
           style="width:calc(100% - 22mm);margin-left:22mm;border-collapse:collapse;margin-bottom:20px;
                  font-family:'Times New Roman',Times,serif;border:1pt solid #000000;color:#000;">
      {''.join(linhas_tr)}
    </table>
"""


def gerar_html_recibo(dados: dict, brasao_b64: str) -> str:
    """Gera HTML completamente auto-contido do recibo oficial do Unidade Exemplo.

    Regra de Paginação e Posicionamento de Assinaturas:
      • Se até 20 linhas de materiais: cabe em 1 folha A4 com assinaturas e rodapé
        fixados na base da folha.
      • Se mais de 20 linhas: a assinatura muda-se para onde acabar a lista de materiais.
        Se houver sobreposição / excesso na primeira folha, as assinaturas passam para a
        segunda folha (Folha 2), e abaixo da assinatura no rodapé constam os dizeres:
        "Nós, colaboradores, sob a proteção de Deus, estamos compromissados com a
         Defesa da Integridade e Controle Eficiente de Materiais."
    """
    numero          = dados.get("numero", "000")
    data_extenso    = dados.get("data_extenso", "")
    descricao_itens = str(dados.get("descricao_itens", "")).strip()

    fornecedor_posto   = html.escape(dados.get("fornecedor_posto",   "Assistente"))
    fornecedor_re      = html.escape(dados.get("fornecedor_re",      ""))
    fornecedor_nome    = html.escape(dados.get("fornecedor_nome",    ""))
    fornecedor_unidade = html.escape(dados.get("fornecedor_unidade", "Unidade Exemplo – Setor de Logística"))

    recebedor_posto    = html.escape(dados.get("recebedor_posto",    "Analista"))
    recebedor_re       = html.escape(dados.get("recebedor_re",       ""))
    recebedor_nome     = html.escape(dados.get("recebedor_nome",     ""))
    recebedor_unidade  = html.escape(dados.get("recebedor_unidade",  "Unidade Exemplo – Setor B"))

    fornecedor_re_nome = f"{fornecedor_re} {fornecedor_nome}".strip()
    recebedor_re_nome  = f"{recebedor_re} {recebedor_nome}".strip()

    # --- Logo ---
    img_brasao = (
        f'<img src="{brasao_b64}" '
        f'style="width:78px;height:90px;object-fit:contain;display:block;margin:0 auto;" '
        f'alt="Brasão Organização">'
        if brasao_b64 else
        '<div style="font-size:38px;text-align:center;">🛡️</div>'
    )
    img_brasao_menor = (
        f'<img src="{brasao_b64}" '
        f'style="width:65px;height:75px;object-fit:contain;display:block;margin:0 auto;" '
        f'alt="Brasão Organização">'
        if brasao_b64 else
        '<div style="font-size:32px;text-align:center;">🛡️</div>'
    )

    # ── Estilos inline repetidos para garantir sobrevivência de classe ──
    S_FOLHA = (
        "width:210mm;max-width:210mm;height:297mm;min-height:297mm;max-height:297mm;"
        "overflow:hidden;box-sizing:border-box;position:relative;"
        "background:#FFFFFF;color:#000000;"
        "font-family:'Times New Roman',Times,serif;"
        "padding:20mm 15mm 13mm 30mm;"
        "margin:18px auto;"
        "border:1px solid #D1D5DB;"
        "box-shadow:0 8px 30px rgba(0,0,0,0.40);"
        "border-radius:2px;"
    )
    S_TITULO = (
        "width:100%;text-align:center;font-size:26pt;font-weight:normal;"
        "margin:26px 0 32px 0;letter-spacing:0.2px;"
        "font-family:'Times New Roman',Times,serif;color:#000;"
    )
    S_INFERIOR = (
        "position:absolute;bottom:13mm;left:30mm;right:15mm;"
    )
    S_CELL_ASS = (
        "width:48%;border:1pt solid #000000;vertical-align:top;"
        "padding:6px 8px;font-size:11pt;line-height:1.55;"
        "font-family:'Times New Roman',Times,serif;color:#000;"
    )
    S_RODAPE = (
        "border-top:1pt solid #000000;padding-top:5px;text-align:center;"
        "font-size:7.2pt;font-style:italic;width:100%;color:#000;line-height:1.3;"
        "font-family:'Times New Roman',Times,serif;"
        "-webkit-print-color-adjust:exact;print-color-adjust:exact;"
    )

    tabela_assinaturas_html = f"""
    <table class="rec-tab-ass" border="0" cellspacing="0" cellpadding="0"
           style="width:100%;border-collapse:collapse;margin-bottom:20px;
                  font-size:11pt;line-height:1.55;
                  font-family:'Times New Roman',Times,serif;color:#000;">
      <tr>
        <td class="rec-cell-ass" style="{S_CELL_ASS}">
          <div style="text-align:center;margin-bottom:4px;font-weight:bold;">FORNECIDO POR:</div>
          <div style="margin:2px 0;">FUNÇÃO:&nbsp;{fornecedor_posto}</div>
          <div style="margin:2px 0;">MATRÍCULA/NOME:&nbsp;{fornecedor_re_nome}</div>
          <div style="margin:2px 0;">ASS: ___________________________________</div>
          <div style="margin:2px 0;">UNIDADE:&nbsp;{fornecedor_unidade}</div>
        </td>
        <td style="width:4%;"></td>
        <td class="rec-cell-ass" style="{S_CELL_ASS}">
          <div style="text-align:center;margin-bottom:4px;font-weight:bold;">RECEBIDO POR:</div>
          <div style="margin:2px 0;">FUNÇÃO:&nbsp;{recebedor_posto}</div>
          <div style="margin:2px 0;">MATRÍCULA/NOME:&nbsp;{recebedor_re_nome}</div>
          <div style="margin:2px 0;">ASS: ___________________________________</div>
          <div style="margin:2px 0;">UNIDADE:&nbsp;{recebedor_unidade}</div>
        </td>
      </tr>
    </table>
"""

    rodape_frase_html = f"""
    <div class="rec-rodape" style="{S_RODAPE}">
      &ldquo;Sistema de controle de recibos e materiais — Projeto demonstrativo.&rdquo;
    </div>
"""

    # --- Análise e distribuição dos itens ---
    linhas_brutas = [p.strip() for p in descricao_itens.split("\n") if p.strip()]
    if not linhas_brutas:
        linhas_brutas = ["01 (UM) MATERIAL CONFORME ESPECIFICADO."]

    eh_tabela = False
    titulo_tabela = ""
    itens_processados = []

    if linhas_brutas and (linhas_brutas[0].startswith("[TABELA") or linhas_brutas[0].startswith("[GRADE")):
        eh_tabela = True
        cab = linhas_brutas[0]
        if ":" in cab and cab.endswith("]"):
            titulo_tabela = cab[cab.find(":") + 1 : -1].strip()
        for l in linhas_brutas[1:]:
            if "|" in l:
                pt = l.split("|", 1)
                itens_processados.append((pt[0].strip(), pt[1].strip()))
            else:
                itens_processados.append(("", l.strip()))
        if not itens_processados:
            itens_processados = [("01", "MATERIAL CONFORME ESPECIFICADO.")]
    else:
        itens_processados = linhas_brutas

    total_linhas_estimadas = len(itens_processados) if eh_tabela else sum(max(1, math.ceil(len(l) / 75)) for l in linhas_brutas)

    barra_imprimir = """
<div class="no-print" style="text-align:center;margin:15px auto;max-width:210mm;">
  <button onclick="window.print()" style="padding:9px 22px;font-size:13.5px;font-weight:bold;cursor:pointer;background:#1E3A8A;color:#FFFFFF;border:none;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.25);">
    🖨️ Clique Aqui para Imprimir / Salvar em PDF (ou Ctrl+P)
  </button>
</div>
"""

    cabecalho_folha1 = f"""
  <table border="0" cellspacing="0" cellpadding="0"
         style="width:100%;border-collapse:collapse;margin-bottom:22px;font-family:'Times New Roman',Times,serif;color:#000;">
    <tr>
      <td width="110" valign="top" align="center"
          style="width:110px;vertical-align:top;text-align:center;">
        {img_brasao}
        <div style="font-size:7.5pt;text-align:center;line-height:1.25;margin-top:4px;
                    font-family:'Times New Roman',Times,serif;color:#000;">
          www.exemplo.com.br<br>
          contato@exemplo.com.br
        </div>
      </td>
      <td valign="top"
          style="vertical-align:top;padding-left:20px;padding-top:2px;
                 font-family:'Times New Roman',Times,serif;color:#000;">
        <div style="font-size:13.5pt;font-weight:bold;line-height:1.35;
                    text-transform:uppercase;color:#000;
                    font-family:'Times New Roman',Times,serif;">
          ORGANIZAÇÃO EXEMPLO<br>
          SISTEMA DE CONTROLE DE MATERIAIS
        </div>
        <div style="font-size:11.5pt;line-height:1.45;margin-top:14px;
                    font-family:'Times New Roman',Times,serif;color:#000;">
          São Paulo,&nbsp;{html.escape(data_extenso)}.
        </div>
      </td>
    </tr>
  </table>
"""

    titulo_html = f"""
  <div class="rec-titulo" style="{S_TITULO}">
    RECIBO Nº&nbsp;{html.escape(str(numero))}/2026
  </div>
"""

    declaracao_html = """
  <div style="font-size:12pt;line-height:1.5;margin-left:22mm;margin-bottom:16px;
              text-align:justify;font-family:'Times New Roman',Times,serif;color:#000;">
    Recebi do Setor de Logística, o material abaixo relacionado:
  </div>
"""

    # CASO 1: Até 20 linhas -> Folha Única A4 (modelo padrão oficial com assinaturas na base)
    if total_linhas_estimadas <= 20:
        corpo_itens_f1 = _gerar_html_conteudo_itens(
            itens_processados,
            eh_tabela=eh_tabela,
            titulo_tabela=titulo_tabela,
            eh_primeira_folha=True
        )

        html_completo = f"""{_CSS_RECIBO_EMBUTIDO}
{barra_imprimir}
<div id="rec-print-root">
  <div class="rec-folha" style="{S_FOLHA}">
    {cabecalho_folha1}
    {titulo_html}
    {declaracao_html}

    {corpo_itens_f1}

    <!-- Bloco inferior de assinaturas + rodapé oficial na base da folha -->
    <div class="rec-inferior" style="{S_INFERIOR}">
      {tabela_assinaturas_html}
      {rodape_frase_html}
    </div>
  </div>
</div>
"""
        return html_completo

    # CASO 2: Mais de 20 linhas -> divide os itens em folhas
    # As assinaturas mudam para onde acabar a lista na última folha, com rodapé na base
    LIMITE_F1 = 20
    LIMITE_FN = 20

    paginas_itens = []
    f1_itens = itens_processados[:LIMITE_F1]
    paginas_itens.append(f1_itens)
    resto = itens_processados[LIMITE_F1:]

    while resto:
        chunk = resto[:LIMITE_FN]
        resto = resto[LIMITE_FN:]
        paginas_itens.append(chunk)

    # Se exatamente entre 16 e 20 itens (todos na folha 1), adiciona Folha 2 para assinaturas se necessário
    if len(paginas_itens) == 1:
        paginas_itens.append([])

    total_paginas = len(paginas_itens)
    folhas_html = []

    for idx_pag, itens_pag in enumerate(paginas_itens, start=1):
        num_pag = idx_pag
        eh_primeira = (num_pag == 1)
        eh_ultima = (num_pag == total_paginas)

        corpo_itens_pag = _gerar_html_conteudo_itens(
            itens_pag,
            eh_tabela=eh_tabela,
            titulo_tabela=titulo_tabela,
            eh_primeira_folha=eh_primeira
        )

        if eh_primeira:
            corpo_folha = f"""
    {cabecalho_folha1}
    {titulo_html}
    {declaracao_html}

    {corpo_itens_pag}

    <div class="rec-inferior" style="{S_INFERIOR}">
      <div style="text-align:right;font-size:8pt;font-style:italic;color:#4B5563;margin-bottom:4px;">
        (Continua na folha {num_pag + 1} &mdash; Termo de Assinaturas)
      </div>
      {rodape_frase_html}
    </div>
"""
        elif not eh_ultima:
            cabecalho_intermediario = f"""
  <table border="0" cellspacing="0" cellpadding="0"
         style="width:100%;border-collapse:collapse;margin-bottom:22px;font-family:'Times New Roman',Times,serif;color:#000;">
    <tr>
      <td width="90" valign="top" align="center" style="width:90px;vertical-align:top;text-align:center;">
        {img_brasao_menor}
        <div style="font-size:7pt;text-align:center;line-height:1.2;margin-top:3px;font-family:'Times New Roman',Times,serif;color:#000;">
          Unidade Exemplo – Setor de Logística
        </div>
      </td>
      <td valign="top" style="vertical-align:top;padding-left:18px;padding-top:2px;font-family:'Times New Roman',Times,serif;color:#000;">
        <div style="font-size:12pt;font-weight:bold;line-height:1.35;text-transform:uppercase;color:#000;font-family:'Times New Roman',Times,serif;">
          ORGANIZAÇÃO EXEMPLO<br>SISTEMA DE CONTROLE DE MATERIAIS
        </div>
        <div style="font-size:11pt;line-height:1.4;margin-top:6px;font-weight:bold;font-family:'Times New Roman',Times,serif;color:#000;">
          RECIBO Nº&nbsp;{html.escape(str(numero))}/2026 &mdash; Folha {num_pag}
        </div>
      </td>
    </tr>
  </table>
"""
            corpo_folha = f"""
    {cabecalho_intermediario}
    <div style="font-size:11.5pt;font-weight:bold;margin-left:22mm;margin-bottom:8px;text-decoration:underline;font-family:'Times New Roman',Times,serif;color:#000;">
      Continuação dos materiais relacionados:
    </div>
    {corpo_itens_pag}
    <div class="rec-inferior" style="{S_INFERIOR}">
      <div style="text-align:right;font-size:8pt;font-style:italic;color:#4B5563;margin-bottom:4px;">
        (Continua na folha {num_pag + 1})
      </div>
      {rodape_frase_html}
    </div>
"""
        else:
            # Folha final com assinaturas onde acabar a lista e rodapé na base
            cabecalho_final = f"""
  <table border="0" cellspacing="0" cellpadding="0"
         style="width:100%;border-collapse:collapse;margin-bottom:22px;font-family:'Times New Roman',Times,serif;color:#000;">
    <tr>
      <td width="90" valign="top" align="center" style="width:90px;vertical-align:top;text-align:center;">
        {img_brasao_menor}
        <div style="font-size:7pt;text-align:center;line-height:1.2;margin-top:3px;font-family:'Times New Roman',Times,serif;color:#000;">
          Unidade Exemplo – Setor de Logística
        </div>
      </td>
      <td valign="top" style="vertical-align:top;padding-left:18px;padding-top:2px;font-family:'Times New Roman',Times,serif;color:#000;">
        <div style="font-size:12pt;font-weight:bold;line-height:1.35;text-transform:uppercase;color:#000;font-family:'Times New Roman',Times,serif;">
          ORGANIZAÇÃO EXEMPLO<br>SISTEMA DE CONTROLE DE MATERIAIS
        </div>
        <div style="font-size:11pt;line-height:1.4;margin-top:6px;font-weight:bold;font-family:'Times New Roman',Times,serif;color:#000;">
          RECIBO Nº&nbsp;{html.escape(str(numero))}/2026 &mdash; Folha {num_pag} (Assinaturas)
        </div>
        <div style="font-size:9.5pt;color:#333333;margin-top:3px;font-family:'Times New Roman',Times,serif;">
          São Paulo,&nbsp;{html.escape(data_extenso)}.
        </div>
      </td>
    </tr>
  </table>
"""
            if itens_pag:
                bloco_topo_final = f"""
    <div style="font-size:11.5pt;font-weight:bold;margin-left:22mm;margin-bottom:8px;text-decoration:underline;font-family:'Times New Roman',Times,serif;color:#000;">
      Continuação dos materiais relacionados:
    </div>
    {corpo_itens_pag}
"""
            else:
                bloco_topo_final = """
    <div style="font-size:12pt;line-height:1.5;margin-left:22mm;margin-bottom:24px;text-align:justify;font-family:'Times New Roman',Times,serif;color:#000;">
      Termo de recebimento e fornecimento referente aos materiais discriminados na(s) folha(s) anterior(es):
    </div>
"""

            corpo_folha = f"""
    {cabecalho_final}
    {bloco_topo_final}

    <!-- Assinaturas posicionadas exatamente onde acaba a lista -->
    <div style="margin-left:22mm;margin-right:0mm;margin-top:12px;margin-bottom:25px;">
      {tabela_assinaturas_html}
    </div>

    <!-- Rodapé oficial fixado na base com os dizeres oficiais -->
    <div class="rec-inferior" style="{S_INFERIOR}">
      <div style="text-align:right;font-size:8pt;font-style:italic;color:#4B5563;margin-bottom:4px;">
        Folha {num_pag} / {total_paginas}
      </div>
      {rodape_frase_html}
    </div>
"""

        estilo_folha_especifico = S_FOLHA
        if not eh_primeira:
            estilo_folha_especifico += "page-break-before:always;break-before:page;"

        folhas_html.append(f"""
  <div class="rec-folha" style="{estilo_folha_especifico}">
    {corpo_folha}
  </div>
""")

    todas_folhas_unidas = "\n".join(folhas_html)
    html_completo = f"""{_CSS_RECIBO_EMBUTIDO}
{barra_imprimir}
<div id="rec-print-root">
{todas_folhas_unidas}
</div>
"""
    return html_completo


def _ao_alternar_preenchimento_fisico():
    """Limpa ou restaura os dados individuais do recebedor ao alternar 'Preencher Fisicamente'."""
    if st.session_state.get("chk_preencher_fisicamente"):
        st.session_state["r_posto"] = ""
        st.session_state["r_re"] = ""
        st.session_state["r_nome"] = ""
    else:
        if not st.session_state.get("r_posto"):
            st.session_state["r_posto"] = "Analista"


def _montar_dados_recibo_impressao(registro) -> dict:
    """Converte um registro de recibo no dicionário esperado por gerar_html_recibo."""
    try:
        dt_obj = datetime.strptime(str(registro["data_elaboracao"])[:10], "%d/%m/%Y")
        data_ext = formatar_data_extenso(dt_obj)
    except Exception:
        data_ext = str(registro["data_elaboracao"])

    rec_posto = str(registro.get("recebedor_posto") or "").strip()
    rec_re = str(registro.get("recebedor_re") or "").strip()
    rec_nome = str(registro.get("recebedor_nome") or "").strip()
    rec_unid = str(registro.get("recebedor_unidade") or registro.get("destinatario") or "Unidade Exemplo – Setor B").strip()
    rec_comp = str(registro.get("recebedor_completo") or "").strip()

    # Preserva vazio quando foi emitido com "Preencher Fisicamente" (sem posto/RE/nome),
    # mantendo compatibilidade com registros históricos importados apenas do Sheets.
    if not rec_posto and not rec_re and not rec_nome:
        if rec_comp and rec_comp not in DESTINATARIOS_PREDEFINIDOS and not str(registro.get("gerador_posto") or "").strip():
            rec_nome = rec_comp

    return {
        "numero": int(registro["numero"]),
        "data_extenso": data_ext,
        "horario_elaboracao": str(registro.get("horario_elaboracao") or ""),
        "assunto": str(registro.get("assunto") or ""),
        "descricao_itens": str(registro.get("descricao_itens") or registro.get("assunto") or ""),
        "fornecedor_posto": str(registro.get("gerador_posto") or "Assistente"),
        "fornecedor_re": str(registro.get("gerador_re") or ""),
        "fornecedor_nome": str(registro.get("gerador_nome") or str(registro.get("gerador_completo") or "")),
        "fornecedor_unidade": str(registro.get("gerador_unidade") or "Unidade Exemplo – Setor de Logística"),
        "recebedor_posto": rec_posto,
        "recebedor_re": rec_re,
        "recebedor_nome": rec_nome,
        "recebedor_unidade": rec_unid,
    }


def _iniciar_edicao_recibo(registro_dict: dict, tab_gerar: str):
    """Prepara o estado da sessão para abrir o formulário com os dados do recibo preenchidos."""
    st.session_state["editar_recibo_preenchimento"] = registro_dict
    st.session_state.pop("recibo_editando_numero", None)
    for _k in [
        "f_posto", "f_re", "f_nome", "f_unid",
        "r_posto", "r_re", "r_nome", "r_unid_sel", "r_unid_manual",
        "chk_preencher_fisicamente", "data_recibo_input",
        "assunto_recibo", "descricao_texto_recibo", "preset_titulo_grade",
        "editor_grade_materiais"
    ]:
        st.session_state.pop(_k, None)
    st.session_state["solicitar_troca_aba_recibos"] = tab_gerar


# =========================================================
# TELA: SUB-HUB DE DOCUMENTOS
# =========================================================

def _tela_submenu_recibos(funcao_voltar, ir_para_documentos):
    df_recibos, rede_online, gsheets_online = carregar_historico_recibos()

    caminho_brasao = visual_theme.localizar_imagem("brasao_doc") or visual_theme.localizar_imagem("brasao")
    brasao_b64 = visual_theme.obter_imagem_base64(caminho_brasao) if caminho_brasao else ""

    col_nav1, col_status = st.columns([6.0, 4.0])
    with col_nav1:
        st.markdown(
            '<div style="display:flex; align-items:center; gap:12px; padding: 4px 0;">'
            '<span style="font-size:2rem;">📋</span>'
            '<div>'
            '<h2 class="notranslate" translate="no" style="margin:0; padding:0; font-size:1.6rem; color:#FFFFFF; font-weight:800;">Sistema de Controle de Recibos</h2>'
            '<p style="margin:0; padding:0; color:#94A3B8; font-size:0.88rem;">Controle Sequencial, Emissão A4 e Gestão de Assinaturas</p>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with col_status:
        st.markdown(
            '<div style="text-align: right; padding-top: 10px; display: flex; justify-content: flex-end; gap: 8px;">'
            '<span class="badge-doc-online">🟢 Modo Local (Base CSV Ativa)</span>'
            '<span class="badge-doc-online">📊 Dados Fictícios de Exemplo</span>'
            '</div>',
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown('<h1 class="notranslate" translate="no" style="font-size:2.2rem;font-weight:800;color:#FFFFFF;margin-bottom:0.2rem;">📋 Controle de Recibos de Materiais</h1>', unsafe_allow_html=True)
    st.caption("Numeração sequencial contínua, geração para assinatura física e controle estrito de pendência de assinatura.")
    st.write("")

    total_recibos = len(df_recibos)
    # Recibos sob controle de assinatura (exclusivamente registrados no sistema)
    df_controle = df_recibos[df_recibos["numero"] >= 1] if not df_recibos.empty else pd.DataFrame()
    total_assinados = len(df_controle[df_controle["status_assinatura"] == "Assinado"]) if not df_controle.empty else 0
    total_pendentes = len(df_controle[df_controle["status_assinatura"] == "pendencia de assinatura"]) if not df_controle.empty else 0
    proximo_seq = calcular_proximo_numero_recibo(df_recibos)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="card-metrica-recibo notranslate" translate="no"><div class="numero notranslate" translate="no" style="color: #60A5FA;">{total_recibos}</div><div class="rotulo notranslate" translate="no" style="color: #93C5FD; font-weight: 800;">TOTAL DE RECIBOS</div></div>',
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f'<div class="card-metrica-recibo notranslate" translate="no"><div class="numero notranslate" translate="no" style="color: #EF4444;">{total_pendentes}</div><div class="rotulo notranslate" translate="no" style="color: #F87171;">🔴 Pendência de Assinatura</div></div>',
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f'<div class="card-metrica-recibo notranslate" translate="no"><div class="numero notranslate" translate="no" style="color: #34D399;">{total_assinados}</div><div class="rotulo notranslate" translate="no">Assinados / Devolvidos</div></div>',
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f'<div class="card-metrica-recibo notranslate" translate="no"><div class="numero notranslate" translate="no" style="color: #FBBF24;">Nº {proximo_seq}</div><div class="rotulo notranslate" translate="no">Próximo Sequencial</div></div>',
            unsafe_allow_html=True
        )

    st.write("")

    TAB_GERAR = "📝 Gerar Novo Recibo"
    TAB_DEVOLVER = "📤 Devolver Assinado"
    TAB_HISTORICO = "📋 Histórico & Consulta"
    TAB_EXCLUIR = "🗑️ Excluir por Engano"
    LABELS_ABAS = [TAB_GERAR, TAB_DEVOLVER, TAB_HISTORICO, TAB_EXCLUIR]

    # Processa solicitação prévia de transição de aba (executada antes da instanciação de st.tabs)
    if "solicitar_troca_aba_recibos" in st.session_state:
        st.session_state["aba_ativa_recibos"] = st.session_state.pop("solicitar_troca_aba_recibos")

    if "aba_ativa_recibos" not in st.session_state or st.session_state["aba_ativa_recibos"] not in LABELS_ABAS:
        st.session_state["aba_ativa_recibos"] = TAB_GERAR

    aba_atual = st.session_state["aba_ativa_recibos"]

    # 4 BOTÕES SUPERIORES DE NAVEGAÇÃO: GIGANTES, CENTRALIZADOS E IMPACTANTES
    c_tab1, c_tab2, c_tab3, c_tab4 = st.columns(4)
    with c_tab1:
        if st.button(
            TAB_GERAR,
            key="btn_nav_tab_gerar",
            type="primary" if aba_atual == TAB_GERAR else "secondary",
            use_container_width=True
        ):
            st.session_state["aba_ativa_recibos"] = TAB_GERAR
            st.rerun()

    with c_tab2:
        if st.button(
            TAB_DEVOLVER,
            key="btn_nav_tab_devolver",
            type="primary" if aba_atual == TAB_DEVOLVER else "secondary",
            use_container_width=True
        ):
            st.session_state["aba_ativa_recibos"] = TAB_DEVOLVER
            st.rerun()

    with c_tab3:
        if st.button(
            TAB_HISTORICO,
            key="btn_nav_tab_historico",
            type="primary" if aba_atual == TAB_HISTORICO else "secondary",
            use_container_width=True
        ):
            st.session_state["aba_ativa_recibos"] = TAB_HISTORICO
            st.rerun()

    with c_tab4:
        if st.button(
            TAB_EXCLUIR,
            key="btn_nav_tab_excluir",
            type="primary" if aba_atual == TAB_EXCLUIR else "secondary",
            use_container_width=True
        ):
            st.session_state["aba_ativa_recibos"] = TAB_EXCLUIR
            st.rerun()

    st.write("")

    # =========================================================
    # ABA 1: GERAR NOVO RECIBO & IMPRESSÃO
    # =========================================================
    if aba_atual == TAB_GERAR:

        # ── Modo Edição: pré-preenche todos os campos se veio do botão "Editar Recibo" ──
        dados_edicao = st.session_state.pop("editar_recibo_preenchimento", None)
        if dados_edicao:
            num_editando = dados_edicao.get("numero")
            st.session_state["recibo_editando_numero"] = num_editando

            # Fornecedor
            posto_f = dados_edicao.get("gerador_posto", "Assistente")
            if posto_f in POSTOS_GRADUACOES:
                st.session_state["f_posto"] = posto_f
            st.session_state["f_re"]   = dados_edicao.get("gerador_re", "")
            st.session_state["f_nome"] = dados_edicao.get("gerador_nome", "")
            st.session_state["f_unid"] = dados_edicao.get("gerador_unidade", "Unidade Exemplo – Setor de Logística")

            # Recebedor
            posto_r = str(dados_edicao.get("recebedor_posto") or "").strip()
            re_r = str(dados_edicao.get("recebedor_re") or "").strip()
            nome_r = str(dados_edicao.get("recebedor_nome") or "").strip()
            eh_fisico = not posto_r and not re_r and not nome_r

            st.session_state["chk_preencher_fisicamente"] = eh_fisico
            if eh_fisico:
                st.session_state["r_posto"] = ""
                st.session_state["r_re"] = ""
                st.session_state["r_nome"] = ""
            else:
                st.session_state["r_posto"] = posto_r if posto_r in POSTOS_GRADUACOES else "Analista"
                st.session_state["r_re"] = re_r
                st.session_state["r_nome"] = nome_r

            unid_r = dados_edicao.get("recebedor_unidade", "") or dados_edicao.get("destinatario", "")
            if unid_r in DESTINATARIOS_PREDEFINIDOS:
                st.session_state["r_unid_sel"]    = unid_r
                st.session_state["r_unid_manual"] = ""
            else:
                st.session_state["r_unid_sel"]    = "Outro (Digitar manualmente)"
                st.session_state["r_unid_manual"] = unid_r

            # Assunto
            st.session_state["assunto_recibo"] = dados_edicao.get("assunto", "")

            # Materiais: detecta formato
            descr = dados_edicao.get("descricao_itens", "") or dados_edicao.get("assunto", "")
            linhas_d = [l.strip() for l in descr.split("\n") if l.strip()]
            if linhas_d and (linhas_d[0].startswith("[TABELA") or linhas_d[0].startswith("[GRADE")):
                st.session_state["formato_mat_recibo"] = "grade"
                cab_d = linhas_d[0]
                tit_d = ""
                if ":" in cab_d and cab_d.endswith("]"):
                    tit_d = cab_d[cab_d.find(":") + 1: -1].strip()
                st.session_state["preset_titulo_grade"] = tit_d
                rows_d = []
                for ln in linhas_d[1:]:
                    if "|" in ln:
                        pts = ln.split("|", 1)
                        rows_d.append({"Qtd": pts[0].strip(), "Material": pts[1].strip()})
                    else:
                        rows_d.append({"Qtd": "", "Material": ln})
                st.session_state["df_grade_recibo"] = pd.DataFrame(rows_d) if rows_d else pd.DataFrame([{"Qtd": "", "Material": ""}])
            else:
                st.session_state["formato_mat_recibo"] = "texto"
                st.session_state["descricao_texto_recibo"] = descr

            # Data de elaboração
            try:
                from datetime import date as _date
                data_parts = dados_edicao.get("data_elaboracao", "").split("/")
                if len(data_parts) == 3:
                    st.session_state["data_recibo_input"] = _date(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
            except Exception:
                pass

        # Detecta se está em modo edição
        num_editando = st.session_state.get("recibo_editando_numero")
        modo_edicao  = num_editando is not None

        if modo_edicao:
            st.warning(
                f"✏️ **MODO EDIÇÃO — Recibo Nº {num_editando}** | "
                f"Os dados abaixo estão pré-preenchidos com o recibo original. "
                f"Altere o que precisar e clique em **SALVAR ALTERAÇÕES**.",
                icon="✏️"
            )
            if st.button("❌ Cancelar Edição e Voltar ao Histórico", key="btn_cancelar_edicao"):
                st.session_state.pop("recibo_editando_numero", None)
                st.session_state["aba_ativa_recibos"] = TAB_HISTORICO
                st.rerun()
        else:
            st.subheader("📝 Elaboração de Recibo de Materiais")
            st.markdown(
                f"Preencha os campos abaixo. O numerador segue automaticamente o sistema. "
                f"Próximo sequencial identificado: **{proximo_seq}**."
            )

        # Alternância entre Lista em Texto e Tabela / Grade (Botões Grandes e Visíveis)
        st.markdown("##### 📐 Formato de Apresentação dos Materiais:")
        if "formato_mat_recibo" not in st.session_state:
            st.session_state["formato_mat_recibo"] = "grade"

        modo_atual = st.session_state["formato_mat_recibo"]

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button(
                "📊 GRADE / TABELA (QTD E MATERIAL)",
                type="primary" if modo_atual == "grade" else "secondary",
                use_container_width=True,
                key="btn_formato_grade"
            ):
                st.session_state["formato_mat_recibo"] = "grade"
                st.rerun()
        with col_b2:
            if st.button(
                "📝 LISTA TRADICIONAL (TEXTO LIVRE)",
                type="primary" if modo_atual == "texto" else "secondary",
                use_container_width=True,
                key="btn_formato_texto"
            ):
                st.session_state["formato_mat_recibo"] = "texto"
                st.rerun()

        formato_material = "📊 Grade / Tabela (Qtd e Material)" if modo_atual == "grade" else "📝 Lista em Texto"

        # Garante que a grade comece limpa quando NÃO está em modo edição
        # (em modo edição, o df_grade_recibo já foi preenchido pelo pré-preenchimento acima)
        num_editando = st.session_state.get("recibo_editando_numero")
        modo_edicao  = num_editando is not None
        if not modo_edicao:
            if "df_grade_recibo" not in st.session_state or (
                isinstance(st.session_state.get("df_grade_recibo"), pd.DataFrame)
                and len(st.session_state["df_grade_recibo"]) != 1
                and (st.session_state["df_grade_recibo"]["Material"].fillna("").astype(str).str.strip() == "").all()
            ) or (
                isinstance(st.session_state.get("df_grade_recibo"), pd.DataFrame)
                and "RIV" in st.session_state["df_grade_recibo"]["Material"].values
            ):
                st.session_state["df_grade_recibo"] = pd.DataFrame([{"Qtd": "", "Material": ""}])
                st.session_state.pop("preset_titulo_grade", None)

        with st.container(border=True):
            c_num, c_data = st.columns([1.8, 2.2])
            with c_num:
                if modo_edicao:
                    st.number_input(
                        "Número do Documento (Editando) *",
                        min_value=int(num_editando),
                        max_value=int(num_editando),
                        value=int(num_editando),
                        step=1,
                        disabled=True,
                        help="Número do recibo sendo editado."
                    )
                else:
                    st.number_input(
                        "Número do Documento (Sequencial Automático) *",
                        min_value=int(proximo_seq),
                        max_value=int(proximo_seq),
                        value=int(proximo_seq),
                        step=1,
                        disabled=True,
                        help="Número sequencial contínuo e automático. A alteração manual é bloqueada para manter a ordem estrita da numeração."
                    )
            with c_data:
                if "data_recibo_input" not in st.session_state:
                    st.session_state["data_recibo_input"] = datetime.now().date()
                data_informada = st.date_input(
                    "Data do Documento *",
                    format="DD/MM/YYYY",
                    key="data_recibo_input"
                )

            # Dados do Responsável pelo Fornecimento (Logística)
            st.markdown("##### 📦 Dados do Fornecedor (Logística)")
            c_f_posto, c_f_re, c_f_nome, c_f_unid = st.columns([1.5, 1.8, 2.5, 2.2])
            with c_f_posto:
                fornecedor_posto = st.selectbox("Cargo / Função *", POSTOS_GRADUACOES, index=5, key="f_posto")
            with c_f_re:
                fornecedor_re = st.text_input("Matrícula / ID *", placeholder="Ex: 10001-X", key="f_re")
            with c_f_nome:
                fornecedor_nome = st.text_input("Nome do Responsável *", placeholder="Ex: FULANO DE TAL", key="f_nome")
            with c_f_unid:
                fornecedor_unidade = st.text_input("Unidade / Setor *", value="Unidade Exemplo – Setor de Logística", key="f_unid")

            # Dados do Recebedor + Opção "Preencher Fisicamente"
            with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
                st.markdown(
                    "<h5 style='margin:0;padding:0;font-size:1.25rem;font-weight:700;'>📥 Dados do Recebedor (Destinatário)</h5>",
                    unsafe_allow_html=True,
                    width="content"
                )
                preencher_fisicamente = st.checkbox(
                    "**✍️ Preencher Fisicamente**",
                    key="chk_preencher_fisicamente",
                    on_change=_ao_alternar_preenchimento_fisico,
                    help="Quando marcado, Posto/Grad, RE e Nome de Guerra ficam em branco e não são obrigatórios."
                )

            opcoes_posto_rec = [""] + POSTOS_GRADUACOES
            if "r_posto" not in st.session_state or st.session_state["r_posto"] not in opcoes_posto_rec:
                st.session_state["r_posto"] = "" if preencher_fisicamente else "Analista"

            lbl_r_posto = "Cargo / Função" if preencher_fisicamente else "Cargo / Função *"
            lbl_r_re = "Matrícula / ID" if preencher_fisicamente else "Matrícula / ID *"
            lbl_r_nome = "Nome do Recebedor" if preencher_fisicamente else "Nome do Recebedor *"

            c_r_posto, c_r_re, c_r_nome, c_r_unid = st.columns([1.5, 1.8, 2.5, 2.2])
            with c_r_posto:
                recebedor_posto = st.selectbox(lbl_r_posto, opcoes_posto_rec, key="r_posto")
            with c_r_re:
                recebedor_re = st.text_input(
                    lbl_r_re,
                    placeholder="" if preencher_fisicamente else "Ex: 20002-Y",
                    key="r_re"
                )
            with c_r_nome:
                recebedor_nome = st.text_input(
                    lbl_r_nome,
                    placeholder="" if preencher_fisicamente else "Ex: CICLANO DA SILVA",
                    key="r_nome"
                )
            with c_r_unid:
                recebedor_unidade_sel = st.selectbox("Unidade / Cia *", DESTINATARIOS_PREDEFINIDOS, index=1, key="r_unid_sel")
                recebedor_unidade_manual = st.text_input(
                    "Se 'Outro', digite a Unidade:",
                    placeholder="Ex: Unidade Exemplo – Setor B",
                    key="r_unid_manual"
                )
                if recebedor_unidade_sel == "Outro (Digitar manualmente)":
                    recebedor_unidade = recebedor_unidade_manual.strip()
                else:
                    recebedor_unidade = recebedor_unidade_sel

            # Objeto / Assunto
            st.markdown("##### 📄 Objeto e Material")
            assunto_informado = st.text_input(
                "Assunto / Resumo do Material *",
                placeholder="Ex: MATERIAL DE ESCRITÓRIO, FERRAMENTAS, EQUIPAMENTOS, PRODUTOS DE LIMPEZA...",
                key="assunto_recibo"
            )

            if formato_material == "📝 Lista em Texto":
                if "descricao_texto_recibo" not in st.session_state:
                    st.session_state["descricao_texto_recibo"] = ""
                descricao_itens_input = st.text_area(
                    "Material Relacionado (Exatamente como constará no recibo) *",
                    placeholder="Exemplo:\n01 (UM) NOTEBOOK CORPORATIVO COM CARREGADOR.\n02 (DOIS) MONITORES 24 POL COM CABOS HDMI.",
                    height=130,
                    key="descricao_texto_recibo"
                )
            else:
                st.caption("Preencha a grade de materiais abaixo. A coluna da esquerda é para a quantidade (número) e a da direita para a discriminação do material.")
                if "preset_titulo_grade" not in st.session_state:
                    st.session_state["preset_titulo_grade"] = ""
                titulo_grade = st.text_input(
                    "Título / Identificação da Tabela (Opcional):",
                    placeholder="Ex: Identificação do bem ou veículo (se desejar título centralizado no topo)",
                    help="Se preenchido, constará centralizado em destaque no topo da tabela.",
                    key="preset_titulo_grade"
                )

                if "df_grade_recibo" not in st.session_state:
                    st.session_state["df_grade_recibo"] = pd.DataFrame([{"Qtd": "", "Material": ""}])

                editor_grade = st.data_editor(
                    st.session_state["df_grade_recibo"],
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Qtd": st.column_config.TextColumn(
                            "Qtd",
                            help="Quantidade (apenas número)",
                            width="small",
                            max_chars=12,
                            required=False
                        ),
                        "Material": st.column_config.TextColumn(
                            "Material",
                            help="Descrição do item ou equipamento",
                            width="large",
                            required=True
                        )
                    },
                    key="editor_grade_materiais"
                )

            label_botao = "💾 SALVAR ALTERAÇÕES DO RECIBO" if modo_edicao else "💾 SALVAR E GERAR RECIBO PARA IMPRESSÃO"
            submeter = st.button(label_botao, type="primary", use_container_width=True, key="btn_submeter_recibo")

        if submeter:
            # Trava 1: Bloqueio de múltiplos cliques rápidos
            if st.session_state.get("salvamento_recibo_em_progresso"):
                st.warning("⏳ Uma gravação de recibo já está em andamento. Aguarde alguns instantes...")
                st.stop()

            erros = []
            if not fornecedor_nome.strip():
                erros.append("O **Nome do Fornecedor** é obrigatório.")
            if not fornecedor_re.strip():
                erros.append("O **RE do Fornecedor** é obrigatório.")
            if not preencher_fisicamente:
                if not str(recebedor_posto or "").strip():
                    erros.append("O **Posto/Grad do Recebedor** é obrigatório (ou marque 'Preencher Fisicamente').")
                if not recebedor_nome.strip():
                    erros.append("O **Nome do Recebedor** é obrigatório.")
                if not recebedor_re.strip():
                    erros.append("O **RE do Recebedor** é obrigatório.")
            if recebedor_unidade_sel == "Outro (Digitar manualmente)" and not recebedor_unidade:
                erros.append("Informe o nome da **Unidade do Recebedor** no campo manual.")
            if not assunto_informado.strip():
                erros.append("O **Assunto** é obrigatório.")

            if formato_material == "📝 Lista em Texto":
                if not descricao_itens_input.strip():
                    erros.append("A **Discriminação do Material** é obrigatória.")
                descricao_itens = descricao_itens_input.strip().upper()
            else:
                itens_grade_validos = []
                if editor_grade is not None and not editor_grade.empty:
                    for _, r in editor_grade.iterrows():
                        q = str(r.get("Qtd", "")).strip().upper()
                        m = str(r.get("Material", "")).strip().upper()
                        if q in ("NONE", "NAN"):
                            q = ""
                        if m in ("NONE", "NAN"):
                            m = ""
                        if q or m:
                            itens_grade_validos.append((q, m))

                if not itens_grade_validos:
                    erros.append("Preencha ao menos um item na **Tabela de Materiais**.")
                    descricao_itens = ""
                else:
                    cab_tag = f"[TABELA: {titulo_grade.strip().upper()}]" if titulo_grade.strip() else "[TABELA]"
                    linhas_txt = [f"{q} | {m}" for q, m in itens_grade_validos]
                    descricao_itens = cab_tag + "\n" + "\n".join(linhas_txt)

            num_int = int(num_editando) if modo_edicao else int(proximo_seq)

            # Normalização robusta para checagem estrita de duplicidade
            import unicodedata

            def _norm_re(txt):
                if not txt:
                    return ""
                t = unicodedata.normalize("NFKD", str(txt)).encode("ASCII", "ignore").decode("ASCII")
                return re.sub(r"[^A-Za-z0-9]", "", t).strip().upper()

            def _norm_txt(txt):
                if not txt:
                    return ""
                t = unicodedata.normalize("NFKD", str(txt)).encode("ASCII", "ignore").decode("ASCII")
                t = re.sub(r"[^A-Za-z0-9\s]", "", t)
                return re.sub(r"\s+", " ", t).strip().upper()

            assunto_norm    = _norm_txt(assunto_informado)
            rec_re_norm     = _norm_re(recebedor_re)
            rec_nome_norm   = _norm_txt(recebedor_nome)
            rec_completo_norm = _norm_txt(f"{recebedor_posto} {recebedor_re} {recebedor_nome}")

            # Trava 2: Bloqueio de duplicidade (ignorada em modo edição — o registro já existe)
            if not modo_edicao and not df_recibos.empty:
                candidatos_seq = []
                df_ordenado_asc = df_recibos.sort_values(by="numero", ascending=True)
                ultimo_rec = df_ordenado_asc.iloc[-1]
                candidatos_seq.append(ultimo_rec)

                if (num_int - 1) in df_recibos["numero"].values:
                    rec_prev = df_recibos[df_recibos["numero"] == (num_int - 1)].iloc[0]
                    candidatos_seq.append(rec_prev)

                for cand in candidatos_seq:
                    cand_assunto_norm = _norm_txt(cand.get("assunto", ""))
                    if assunto_norm and cand_assunto_norm and (assunto_norm == cand_assunto_norm):
                        cand_re   = _norm_re(cand.get("recebedor_re", ""))
                        cand_nome = _norm_txt(cand.get("recebedor_nome", ""))
                        cand_comp = _norm_txt(cand.get("recebedor_completo") or cand.get("destinatario", ""))

                        mesmo_recebedor = False
                        if rec_re_norm and cand_re and (rec_re_norm == cand_re):
                            mesmo_recebedor = True
                        elif rec_nome_norm and cand_nome and (rec_nome_norm == cand_nome):
                            mesmo_recebedor = True
                        elif rec_completo_norm and cand_comp and (rec_completo_norm in cand_comp or cand_comp in rec_completo_norm):
                            mesmo_recebedor = True

                        if mesmo_recebedor:
                            erros.append(
                                f"🚫 **Bloqueio de Duplicidade em Sequência:** Não é permitido gerar dois recibos seguidos "
                                f"para o mesmo recebedor com o mesmo assunto!\n\n"
                                f"O Recibo anterior (**Nº {cand['numero']}**) já foi emitido para "
                                f"**{cand.get('recebedor_completo') or cand.get('destinatario')}** com o assunto **\"{cand.get('assunto')}\"**.\n\n"
                                f"Se este novo recibo for uma correção de um gerado por engano, exclua o recibo anterior na aba **'🗑️ Excluir Recibo por Engano'**."
                            )
                            break

            # Trava 3: Token anti-duplicidade (ignorada em modo edição)
            token_submissao = f"{num_int}_{assunto_norm}_{rec_re_norm}_{rec_nome_norm}"
            if not modo_edicao and st.session_state.get("ultimo_recibo_salvo_token") == token_submissao:
                erros.append(f"⚠️ O Recibo Nº {num_int} já foi gravado no sistema nesta sessão.")

            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                st.session_state["salvamento_recibo_em_progresso"] = True
                try:
                    spinner_msg = (
                        f"✏️ Atualizando Recibo Nº {num_int} na sistema..."
                        if modo_edicao else
                        f"💾 Gravando Recibo Nº {num_int} na sistema e sincronizando histórico..."
                    )
                    with st.spinner(spinner_msg):
                        gerador_completo = f"{fornecedor_posto} {fornecedor_re.strip()} {fornecedor_nome.strip().upper()}".strip()
                        recebedor_completo = f"{recebedor_posto} {recebedor_re.strip()} {recebedor_nome.strip().upper()}".strip()
                        numerador_completo = f"{num_int:03d}/2026"
                        data_formatada = data_informada.strftime("%d/%m/%Y")

                        recebido_por_gs = recebedor_completo if recebedor_completo else recebedor_unidade.strip()
                        fornecido_por_gs = f"{fornecedor_posto} {fornecedor_nome.strip().upper()}".strip() if fornecedor_nome.strip() else fornecedor_posto

                        sucesso_gs, msg_gs, linha_gs = salvar_recibo_na_planilha_google(
                            numero=num_int,
                            data_formatada=data_formatada,
                            assunto=assunto_informado.strip().upper(),
                            recebido_por=recebido_por_gs,
                            fornecido_por=fornecido_por_gs
                        )

                        novo_registro = {
                            "numero": num_int,
                            "numerador_completo": numerador_completo,
                            "data_elaboracao": data_formatada,
                            "horario_elaboracao": "",
                            "gerador_posto": fornecedor_posto,
                            "gerador_re": fornecedor_re.strip().upper(),
                            "gerador_nome": fornecedor_nome.strip().upper(),
                            "gerador_completo": gerador_completo,
                            "gerador_unidade": fornecedor_unidade.strip(),
                            "recebedor_posto": recebedor_posto,
                            "recebedor_re": recebedor_re.strip().upper(),
                            "recebedor_nome": recebedor_nome.strip().upper(),
                            "recebedor_completo": recebedor_completo,
                            "recebedor_unidade": recebedor_unidade.strip(),
                            "destinatario": recebedor_unidade.strip(),
                            "assunto": assunto_informado.strip().upper(),
                            "descricao_itens": descricao_itens.strip().upper(),
                            "status_assinatura": "pendencia de assinatura",
                            "nome_arquivo": "",
                            "caminho_arquivo": "",
                            "data_upload": ""
                        }

                        if not df_recibos.empty and num_int in df_recibos["numero"].values:
                            df_sem_atual = df_recibos[df_recibos["numero"] != num_int]
                            df_atualizado = pd.concat([df_sem_atual, pd.DataFrame([novo_registro])], ignore_index=True)
                        else:
                            df_atualizado = pd.concat([df_recibos, pd.DataFrame([novo_registro])], ignore_index=True)

                        salvar_historico_recibos(df_atualizado)
                        st.session_state["ultimo_recibo_salvo_token"] = token_submissao
                        st.session_state["df_grade_recibo"] = pd.DataFrame([{"Qtd": "", "Material": ""}])

                        # Limpa modo edição e campos auxiliares após salvar com sucesso
                        for _k_limpar in [
                            "recibo_editando_numero", "data_recibo_input",
                            "descricao_texto_recibo", "preset_titulo_grade",
                            "chk_preencher_fisicamente"
                        ]:
                            st.session_state.pop(_k_limpar, None)
                finally:
                    st.session_state["salvamento_recibo_em_progresso"] = False

                # Transição direta para a tela de devolução do documento assinado
                st.session_state["solicitar_troca_aba_recibos"] = TAB_DEVOLVER
                st.session_state["recibo_selecionado_upload"] = num_int
                st.session_state["msg_novo_recibo"] = (
                    (f"Recibo Nº **{num_int}** atualizado com sucesso na sistema!"
                     if modo_edicao else
                     f"Recibo Nº **{num_int}** gravado na sistema e registrado no sistema!")
                    if sucesso_gs else
                    (f"Recibo Nº **{num_int}** atualizado no sistema local!" if modo_edicao
                     else f"Recibo Nº **{num_int}** gravado no sistema local!")
                )

                st.rerun()

    # =========================================================
    # ABA 2: DEVOLVER DOCUMENTO ASSINADO (UPLOAD)
    # =========================================================
    elif aba_atual == TAB_DEVOLVER:
        msg_novo = st.session_state.pop("msg_novo_recibo", None)
        if msg_novo:
            st.success(f"✅ {msg_novo}")

        st.subheader("📤 Devolução de Documento Assinado")
        st.markdown(
            "Após coletar as assinaturas físicas do fornecedor e do recebedor, digitalize o documento e anexe-o aqui. "
            "Ao concluir o envio, a **pendência de assinatura será baixada** e o arquivo salvo no padrão oficial do Unidade."
        )

        df_para_devolucao = df_recibos[df_recibos["numero"] >= 1] if not df_recibos.empty else pd.DataFrame()

        if df_para_devolucao.empty:
            st.info("Ainda não há recibos emitidos registrados no sistema para controle de devolução. Gere um novo recibo na primeira aba.")
        else:
            df_ordenado = df_para_devolucao.sort_values(by="numero", ascending=False)
            opcoes_recibos = []
            mapa_indices = {}

            for _, r in df_ordenado.iterrows():
                tag = "✅ Assinado" if str(r.get("status_assinatura")) == "Assinado" else "🔴 pendencia de assinatura"
                label = f"Recibo Nº {r['numero']} | {r['data_elaboracao']} | {r['assunto']} [{tag}]"
                opcoes_recibos.append(label)
                mapa_indices[label] = int(r["numero"])

            alvo_upload = st.session_state.pop("recibo_selecionado_upload", None)
            if alvo_upload is not None:
                for lab in opcoes_recibos:
                    if mapa_indices.get(lab) == alvo_upload:
                        st.session_state["sel_recibo_devolver_assinado"] = lab
                        break

            if "sel_recibo_devolver_assinado" in st.session_state and st.session_state["sel_recibo_devolver_assinado"] not in opcoes_recibos:
                st.session_state["sel_recibo_devolver_assinado"] = opcoes_recibos[0]

            recibo_escolhido = st.selectbox(
                "Selecione o Recibo para Devolver Assinado:",
                opcoes_recibos,
                key="sel_recibo_devolver_assinado"
            )

            num_sel = mapa_indices[recibo_escolhido]
            dados_sel = df_recibos[df_recibos["numero"] == num_sel].iloc[0]

            with st.container(border=True):
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.markdown(f"**Número:** Recibo UNEXEMPLO- {dados_sel['numero']}/01/2026")
                    st.markdown(f"**Data de Emissão:** {dados_sel['data_elaboracao']}")
                    st.markdown(f"**Fornecedor:** {dados_sel.get('gerador_completo', '')}")
                with c_d2:
                    st.markdown(f"**Recebedor:** {dados_sel.get('recebedor_completo') or dados_sel.get('destinatario', '')}")
                    st.markdown(f"**Assunto:** {dados_sel['assunto']}")
                    status_atual = str(dados_sel.get("status_assinatura", "pendencia de assinatura"))
                    if status_atual == "Assinado":
                        st.markdown("**Status:** <span class='badge-assinado-verde'>✅ Assinado / Devolvido</span>", unsafe_allow_html=True)
                        st.markdown(f"**Arquivo:** `{dados_sel.get('nome_arquivo', '-')}`")
                    else:
                        st.markdown("**Status:** <span class='badge-pendencia-assinatura'>🔴 pendencia de assinatura</span>", unsafe_allow_html=True)

                # Botão de impressão da via do documento
                dados_recibo_imp = _montar_dados_recibo_impressao(dados_sel)
                html_recibo_sel = gerar_html_recibo(dados_recibo_imp, brasao_b64)

                st.divider()
                if status_atual != "Assinado":
                    c_btn_imp, c_btn_editar = st.columns(2)
                    with c_btn_imp:
                        st.download_button(
                            label=f"🖨️ Imprimir Recibo Nº {dados_sel['numero']}",
                            data=html_recibo_sel,
                            file_name=f"Recibo_{dados_sel['numero']}_2026.html",
                            mime="text/html",
                            use_container_width=True,
                            key=f"btn_imp_devolver_{dados_sel['numero']}"
                        )
                    with c_btn_editar:
                        if st.button(
                            "✏️ Editar Recibo",
                            key=f"btn_editar_recibo_devolver_{dados_sel['numero']}",
                            use_container_width=True,
                            help="Abre o formulário com os dados deste recibo pré-preenchidos para edição."
                        ):
                            _iniciar_edicao_recibo(dados_sel.to_dict(), TAB_GERAR)
                            st.rerun()
                else:
                    st.download_button(
                        label=f"🖨️ Imprimir Recibo Nº {dados_sel['numero']}",
                        data=html_recibo_sel,
                        file_name=f"Recibo_{dados_sel['numero']}_2026.html",
                        mime="text/html",
                        use_container_width=True,
                        key=f"btn_imp_devolver_{dados_sel['numero']}"
                    )

            st.write("")
            arquivo_upload = st.file_uploader(
                "Selecione o Recibo Digitalizado e Assinado (PDF, JPG, PNG)",
                type=["pdf", "png", "jpg", "jpeg"],
                key="uploader_recibo_assinado"
            )

            if arquivo_upload:
                # Validação de segurança: limite de 15 MB por arquivo
                if arquivo_upload.size > 15 * 1024 * 1024:
                    st.error("⚠️ O arquivo enviado excede o limite máximo permitido de 15 MB.")
                    st.stop()

                extensao = os.path.splitext(arquivo_upload.name)[1].lower()
                assunto_limpo = sanitizar_nome_arquivo(dados_sel["assunto"])

                # Padrão do arquivo: "001.MATERIAL DE ESCRITORIO Analista 20002-Y CICLANO DA SILVA.pdf"
                rec_posto = str(dados_sel.get("recebedor_posto") or "").strip()
                rec_re = str(dados_sel.get("recebedor_re") or "").strip()
                rec_nome = str(dados_sel.get("recebedor_nome") or "").strip()

                if rec_posto or rec_re or rec_nome:
                    detalhes_rec = f"{rec_posto} {rec_re} {rec_nome}".strip()
                else:
                    detalhes_rec = str(dados_sel.get("recebedor_completo") or dados_sel.get("destinatario") or "").strip()

                detalhes_rec = sanitizar_nome_arquivo(detalhes_rec)

                if detalhes_rec:
                    nome_padronizado = f"{dados_sel['numero']}.{assunto_limpo} {detalhes_rec}{extensao}"
                else:
                    nome_padronizado = f"{dados_sel['numero']}.{assunto_limpo}{extensao}"

                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(96, 165, 250, 0.4); border-radius: 8px; padding: 12px 16px; margin: 10px 0;">
                    <div style="color: #93C5FD; font-size: 0.85rem; font-weight: 700; text-transform: uppercase;">Renomeação Automática Padrão do Sistema:</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; font-family: monospace; margin-top: 4px;">{nome_padronizado}</div>
                    <div style="color: #94A3B8; font-size: 0.82rem; margin-top: 4px;">Destino oficial: <code>dados/recibos/digitalizados/</code></div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("💾 Confirmar Devolução e Baixar Pendência de Assinatura", type="primary", use_container_width=True):
                    if extensao not in (".pdf", ".png", ".jpg", ".jpeg"):
                        st.error("⚠️ Extensão de arquivo não permitida. Envie apenas PDF, PNG ou JPG.")
                        st.stop()

                    conteudo_bytes = arquivo_upload.read()

                    garantir_diretorios()
                    caminho_local_arq = os.path.abspath(os.path.join(DIR_DIGITALIZADOS_LOCAL, nome_padronizado))
                    dir_permitido = os.path.abspath(DIR_DIGITALIZADOS_LOCAL)

                    # Prevenção rigorosa contra Path Traversal no upload
                    if os.path.commonpath([caminho_local_arq, dir_permitido]) != dir_permitido:
                        st.error("⚠️ Tentativa de caminho inválido detectada.")
                        st.stop()

                    with open(caminho_local_arq, "wb") as fl:
                        fl.write(conteudo_bytes)

                    # Armazena caminho relativo portátil e seguro (não expõe pastas pessoais do usuário)
                    caminho_relativo = os.path.join("dados", "recibos", "digitalizados", nome_padronizado).replace("\\", "/")

                    data_upload_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    idx_registro = df_recibos[df_recibos["numero"] == num_sel].index[0]
                    df_recibos.at[idx_registro, "status_assinatura"] = "Assinado"
                    df_recibos.at[idx_registro, "nome_arquivo"] = nome_padronizado
                    df_recibos.at[idx_registro, "caminho_arquivo"] = caminho_relativo
                    df_recibos.at[idx_registro, "data_upload"] = data_upload_str

                    salvar_historico_recibos(df_recibos)
                    try:
                        mapear_arquivos_digitalizados.clear()
                    except Exception:
                        pass

                    # Atualiza a Coluna C (SEI / Anexo) na planilha sistema com o arquivo assinado
                    sucesso_gs_arq, msg_gs_arq = atualizar_arquivo_na_planilha_google(num_sel, nome_padronizado)

                    msg_sucesso = f"🎉 Recibo Nº **{num_sel}** assinado e arquivado"
                    msg_sucesso += " com sucesso!"

                    

                    st.success(f"{msg_sucesso} Pendência baixada.")

                    st.rerun()

            if str(dados_sel.get("status_assinatura")) == "Assinado" and str(dados_sel.get("nome_arquivo")):
                nome_arq = str(dados_sel.get("nome_arquivo"))
                caminhos_busca = [
                    os.path.join(CAMINHO_DIGITALIZADOS_REDE, nome_arq),
                    os.path.join(DIR_DIGITALIZADOS_LOCAL, nome_arq),
                    str(dados_sel.get("caminho_arquivo", ""))
                ]
                achado = next((p for p in caminhos_busca if os.path.isfile(p)), None)
                if achado:
                    st.write("")
                    with open(achado, "rb") as fa:
                        bytes_down = fa.read()
                    st.download_button(
                        label=f"📥 Baixar Via Assinada ({nome_arq})",
                        data=bytes_down,
                        file_name=nome_arq,
                        use_container_width=True
                    )

    # =========================================================
    # ABA 3: HISTÓRICO GERAL & CONSULTA
    # =========================================================
    elif aba_atual == TAB_HISTORICO:
        st.subheader("📋 Histórico Geral e Controle de Pendências")

        if df_recibos.empty:
            st.info("Nenhum recibo cadastrado até o momento.")
        else:
            col_busca, col_filtro = st.columns([7, 3])
            with col_busca:
                termo_busca = st.text_input(
                    "🔍 Busca textual:",
                    placeholder="Pesquise por número, fornecedor, recebedor, assunto ou material...",
                    key="busca_texto_recibos"
                )
            with col_filtro:
                filtro_status = st.selectbox(
                    "Filtrar por Status de Assinatura:",
                    [
                        "Todos",
                        "🔴 Pendência de Assinatura",
                        "✅ Assinados / Devolvidos"
                    ]
                )

            df_filtrado = df_recibos.copy()

            if "Pendência" in filtro_status:
                df_filtrado = df_filtrado[df_filtrado["status_assinatura"] == "pendencia de assinatura"]
            elif "Assinados" in filtro_status:
                df_filtrado = df_filtrado[df_filtrado["status_assinatura"] == "Assinado"]

            if termo_busca.strip():
                termo = termo_busca.strip().lower()
                mascara = df_filtrado.astype(str).apply(
                    lambda linha: linha.str.lower().str.contains(termo, regex=False, na=False).any(),
                    axis=1
                )
                df_filtrado = pd.DataFrame(df_filtrado[mascara])

            df_filtrado = pd.DataFrame(df_filtrado.sort_values(by="numero", ascending=False))

            st.caption(f"Exibindo **{len(df_filtrado)}** de **{len(df_recibos)}** recibo(s) registrado(s).")

            df_tabela = pd.DataFrame()
            df_tabela["Nº"] = df_filtrado["numero"]
            df_tabela["Data"] = df_filtrado["data_elaboracao"]
            df_tabela["Fornecedor (Logística)"] = df_filtrado["gerador_completo"]
            df_tabela["Recebedor"] = df_filtrado["recebedor_completo"].replace("", None).fillna(df_filtrado["destinatario"])
            df_tabela["Assunto"] = df_filtrado["assunto"]

            def formatar_status_tabela(s):
                if str(s).strip() == "Assinado":
                    return "✅ Assinado"
                return "🔴 Pendência de Assinatura"

            df_tabela["Status Assinatura"] = [
                formatar_status_tabela(r["status_assinatura"])
                for _, r in df_filtrado.iterrows()
            ]
            df_tabela["Arquivo Assinado"] = df_filtrado["nome_arquivo"].replace("", "-")

            st.dataframe(
                df_tabela,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.markdown("#### ⚡ Ações por Registro")
            nums_disp = df_filtrado["numero"].tolist()
            if nums_disp:
                num_act = st.selectbox(
                    "Selecione o Nº do Recibo para Ações:",
                    nums_disp,
                    format_func=lambda n: f"Recibo Nº {n} | {df_recibos.loc[df_recibos['numero'] == n, 'assunto'].iloc[0] if (df_recibos['numero'] == n).any() else ''}"
                )
            else:
                num_act = None

            if num_act is not None:
                registro_sel = df_recibos[df_recibos["numero"] == num_act].iloc[0]
                status_sel = str(registro_sel.get("status_assinatura", ""))
                dados_recibo_hist = _montar_dados_recibo_impressao(registro_sel)
                html_recibo_h = gerar_html_recibo(dados_recibo_hist, brasao_b64)

                if status_sel == "Assinado":
                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        st.download_button(
                            label=f"🖨️ Imprimir Recibo Nº {registro_sel['numero']}",
                            data=html_recibo_h,
                            file_name=f"Recibo_{registro_sel['numero']}_2026.html",
                            mime="text/html",
                            use_container_width=True,
                            key=f"btn_imp_hist_{registro_sel['numero']}"
                        )
                    with c_act2:
                        nome_f = str(registro_sel.get("nome_arquivo"))
                        caminhos = [
                            os.path.join(DIR_DIGITALIZADOS_LOCAL, nome_f),
                            str(registro_sel.get("caminho_arquivo", ""))
                        ]
                        achou = next((p for p in caminhos if os.path.isfile(p)), None)
                        if achou:
                            with open(achou, "rb") as fa:
                                b_arq = fa.read()
                            st.download_button(
                                label="📥 Baixar Documento Assinado",
                                data=b_arq,
                                file_name=nome_f,
                                use_container_width=True,
                                key=f"btn_dl_hist_{registro_sel['numero']}"
                            )
                        else:
                            st.caption("Ficheiro não localizado")
                else:
                    c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                    with c_act1:
                        st.download_button(
                            label=f"🖨️ Imprimir Minuta",
                            data=html_recibo_h,
                            file_name=f"Recibo_{registro_sel['numero']}_2026.html",
                            mime="text/html",
                            use_container_width=True,
                            key=f"btn_imp_hist_{registro_sel['numero']}"
                        )
                    with c_act2:
                        if st.button("📤 Devolver Assinado", key="btn_ir_upload_direto", use_container_width=True):
                            st.session_state["solicitar_troca_aba_recibos"] = TAB_DEVOLVER
                            st.session_state["recibo_selecionado_upload"] = int(registro_sel["numero"])
                            st.rerun()
                    with c_act3:
                        if st.button("✏️ Editar Recibo", key="btn_editar_recibo_direto", use_container_width=True):
                            _iniciar_edicao_recibo(registro_sel.to_dict(), TAB_GERAR)
                            st.rerun()
                    with c_act4:
                        if st.button("🗑️ Excluir Recibo", key="btn_ir_excluir_direto", use_container_width=True):
                            st.session_state["solicitar_troca_aba_recibos"] = TAB_EXCLUIR
                            st.session_state["recibo_selecionado_exclusao"] = int(registro_sel["numero"])
                            st.rerun()

            st.write("")
            csv_completo = df_recibos.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 Exportar Histórico de Recibos em CSV",
                data=csv_completo,
                file_name="controle_recibos_2026_completo.csv",
                mime="text/csv",
                use_container_width=True
            )

    # =========================================================
    # ABA 4: EXCLUIR RECIBO POR ENGANO (COM LIMPEZA NO GOOGLE SHEETS)
    # =========================================================
    elif aba_atual == TAB_EXCLUIR:
        msg_del = st.session_state.pop("msg_sucesso_exclusao", None)
        if msg_del:
            st.success(f"✅ {msg_del}")

        st.subheader("🗑️ Cancelamento e Exclusão de Recibo Emitido por Engano")
        st.markdown(
            "Esta ferramenta permite **cancelar e excluir permanentemente** recibos gerados incorretamente ou em duplicidade.\n\n"
            "Ao confirmar a exclusão:\n"
            "1. Os dados da linha correspondente serão **totalmente removidos da sistema**;\n"
            "2. O registro será apagado do banco de dados do sistema (local e rede);\n"
            "3. O próximo sequencial do sistema será recalculado automaticamente para reaproveitamento do número."
        )

        df_ativos = df_recibos[df_recibos["numero"] > 0] if not df_recibos.empty else pd.DataFrame()

        if df_ativos.empty:
            st.info("Nenhum recibo cadastrado no sistema.")
        else:
            c_filtro1, c_filtro2 = st.columns([6.0, 4.0])
            with c_filtro2:
                incluir_historicos = st.checkbox("Exibir também recibos anteriores ao Nº 1", value=False, key="chk_inc_hist_del")

            if not incluir_historicos:
                df_candidatos = pd.DataFrame(df_ativos[df_ativos["numero"] >= 1])
            else:
                df_candidatos = df_ativos

            if df_candidatos.empty:
                st.info("Não há recibos emitidos registrados no sistema disponíveis para exclusão.")
            else:
                df_candidatos_ord = pd.DataFrame(df_candidatos.sort_values(by="numero", ascending=False))
                opcoes_del = []
                mapa_del = {}
                for _, r in df_candidatos_ord.iterrows():
                    tag_s = "✅ Assinado" if str(r.get("status_assinatura")) == "Assinado" else "🔴 Pendência"
                    rec_lbl = f"Recibo Nº {r['numero']} | {r['data_elaboracao']} | {r['assunto']} | Destino: {r.get('recebedor_completo') or r.get('destinatario', '')} [{tag_s}]"
                    opcoes_del.append(rec_lbl)
                    mapa_del[rec_lbl] = int(r["numero"])

                alvo_del = st.session_state.pop("recibo_selecionado_exclusao", None)
                if alvo_del is not None:
                    for lab in opcoes_del:
                        if mapa_del.get(lab) == alvo_del:
                            st.session_state["sel_recibo_excluir_assinado"] = lab
                            break

                if "sel_recibo_excluir_assinado" in st.session_state and st.session_state["sel_recibo_excluir_assinado"] not in opcoes_del:
                    st.session_state["sel_recibo_excluir_assinado"] = opcoes_del[0]

                recibo_sel_txt = st.selectbox(
                    "Selecione o Recibo para Excluir:",
                    opcoes_del,
                    key="sel_recibo_excluir_assinado"
                )

                num_excluir = mapa_del[recibo_sel_txt]
                dados_del = df_recibos[df_recibos["numero"] == num_excluir].iloc[0]

                with st.container(border=True):
                    st.markdown(f"#### ⚠️ Conferência do Recibo Nº {num_excluir}")
                    c_e1, c_e2 = st.columns(2)
                    with c_e1:
                        st.markdown(f"**Número:** Recibo UNEXEMPLO- {dados_del['numero']}/01/2026")
                        st.markdown(f"**Data de Emissão:** {dados_del['data_elaboracao']}")
                        st.markdown(f"**Fornecedor:** {dados_del.get('gerador_completo', '')}")
                    with c_e2:
                        st.markdown(f"**Recebedor:** {dados_del.get('recebedor_completo') or dados_del.get('destinatario', '')}")
                        st.markdown(f"**Assunto:** {dados_del['assunto']}")
                        st.markdown(f"**Status da Assinatura:** `{dados_del.get('status_assinatura', '')}`")
                        if dados_del.get("nome_arquivo"):
                            st.markdown(f"**Arquivo Anexo:** `{dados_del['nome_arquivo']}`")

                    st.markdown("---")
                    st.caption("A exclusão é irreversível. Para segurança, confirme no checkbox abaixo:")
                    confirmou_exclusao = st.checkbox(
                        f"🚨 Confirmo expressamente a exclusão do Recibo Nº {num_excluir} e a limpeza de seus dados na sistema.",
                        key=f"chk_confirma_del_{num_excluir}"
                    )

                    btn_del = st.button(
                        f"🗑️ Confirmar Exclusão Definitiva do Recibo Nº {num_excluir}",
                        type="primary",
                        disabled=not confirmou_exclusao,
                        use_container_width=True,
                        key=f"btn_executar_del_{num_excluir}"
                    )

                    if btn_del:
                        with st.spinner(f"Excluindo Recibo Nº {num_excluir} na sistema e sincronizando base..."):
                            # 1. sistema
                            sucesso_gs_del, msg_gs_del, linha_del = excluir_recibo_na_planilha_google(num_excluir)

                            # 2. Base local / rede (CSV)
                            df_atualizado_del = pd.DataFrame(df_recibos[df_recibos["numero"] != num_excluir])
                            salvar_historico_recibos(df_atualizado_del)

                            # 3. Remover arquivo físico se houver (com validação estrita de diretório)
                            arq_del = os.path.basename(str(dados_del.get("nome_arquivo", "")).strip())
                            if arq_del:
                                caminho_arq = os.path.join(DIR_DIGITALIZADOS_LOCAL, arq_del)
                                dir_permitido = os.path.abspath(DIR_DIGITALIZADOS_LOCAL)
                                # Garante que o arquivo a ser removido está estritamente dentro da pasta permitida
                                if os.path.commonpath([os.path.abspath(caminho_arq), dir_permitido]) == dir_permitido:
                                    if os.path.isfile(caminho_arq):
                                        try:
                                            os.remove(caminho_arq)
                                        except Exception:
                                            pass
                            try:
                                mapear_arquivos_digitalizados.clear()
                            except Exception:
                                pass

                            msg_sucesso_del = f"Recibo Nº **{num_excluir}** cancelado e removido do sistema com sucesso!"

                            st.session_state["msg_sucesso_exclusao"] = msg_sucesso_del
                            st.rerun()

    st.write("")
    st.markdown("""
    <div class="footer-creditos">
        Desenvolvido por: <b>Thiago Guimarães</b>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# FUNÇÃO PRINCIPAL DE EXECUÇÃO DO MÓDULO DOCUMENTOS
# =========================================================
def executar_documentos(funcao_voltar):
    """Ponto de entrada do módulo Gestão de Documentos (abre no Hub de Gestão de Documentos)."""
    _injetar_estilos_recibos()

    if "tela_documentos" not in st.session_state:
        st.session_state.tela_documentos = "hub"

    def ir_para_documentos(nome_da_tela):
        st.session_state.tela_documentos = nome_da_tela

    # No modo portfólio, direciona diretamente para o fluxo completo de Recibos
    _tela_submenu_recibos(funcao_voltar, ir_para_documentos)
