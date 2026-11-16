"""
Sistema de Controle de Recibos de Materiais
Aplicação para emissão de recibos timbrados padrão A4 para assinatura física,
numeração sequencial contínua, upload de comprovantes assinados e controle de pendências.

Desenvolvido por: Thiago Guimarães
"""

import os
import sys
import streamlit as st

# Garante o diretório de execução correto
diretorio_base = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != diretorio_base:
    os.chdir(diretorio_base)
if diretorio_base not in sys.path:
    sys.path.insert(0, diretorio_base)

# Configuração da página Streamlit
st.set_page_config(
    page_title="Sistema de Controle de Recibos",
    page_icon="📋",
    layout="wide"
)

import importlib
import visual_theme
import documentos

# Recarrega módulos para refletir alterações instantaneamente
importlib.reload(visual_theme)
importlib.reload(documentos)

# Aplica o papel de parede e o tema visual glassmorphism
visual_theme.aplicar_papel_de_parede_e_estilo()

# Executa diretamente o módulo de recibos
documentos.executar_documentos(funcao_voltar=lambda: None)

