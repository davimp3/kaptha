import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# --- [CORREÇÃO DE IMPORTAÇÃO] ---
# Adiciona a pasta raiz (kaptha/) ao caminho do sistema
# Isso permite que o app em 'pages/' encontre a pasta 'data_loader/'
# (Vamos manter esta linha por segurança, embora a importação limpa deva funcionar)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- FIM DA CORREÇÃO ---

# [ALTERAÇÃO] Importando do NOVO ficheiro loader_op.py
from data_loader.loader_op import load_operacional_data


# Configuração inicial da página
st.set_page_config(page_title="Dashboard Operacional", layout="wide")

# --- AJUSTE DE CSS PARA REMOVER PADDING SUPERIOR ---
st.markdown("""
    <style>
        /* [ALTERAÇÃO] Remove TODO padding, margin e border do container principal para o topo */
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }
        [data-testid="stAppViewContainer"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }

        /* [REMOVIDO] O bloco 'header' que escondia a sidebar foi removido. */

        /* [ALTERAÇÃO] Ajusta padding geral da página para quase zero */
        .stApp {
            padding: 0.05rem !important;
        }
        /* [ALTERAÇÃO] Reduz o gap (espaço) entre as colunas */
        [data-testid="stHorizontalBlock"] {
            gap: 0.1rem !important;
        }
        /* [ALTERAÇÃO] Reduz o padding dos containers de borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.1rem !important;
        }
        /* Reduz o padding dos containers de métrica */
        [data-testid="stMetric"] {
            padding: 0px !important;
            margin: 0px !important;
        }
        /* [ALTERAÇÃO] Reduz o tamanho das fontes de título h6 e h5 */
        h6 { font-size: 0.8rem !important; margin: 0 !important; }
        h5 { font-size: 1.0rem !important; margin: 0 !important; }
        /* [ALTERAÇÃO] Reduz o tamanho das legendas */
        [data-testid="stCaption"] {
            font-size: 0.6rem !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        /* Reduz o espaço dos separadores (---) */
        hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
# --- FIM DO AJUSTE DE CSS ---


# --- FUNÇÕES DE FORMATAÇÃO ---

def format_percentage(value, decimals=2):
    """[CORRETO] Formata um valor decimal (ex: 0.0540) como porcentagem (ex: 5,40%)."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "0,00%"
        # Multiplica por 100 para converter decimal em porcentagem
        percentage_value = numeric_value * 100
        return f"{percentage_value:,.{decimals}f}%".replace('.', ',')
    except (ValueError, TypeError):
        return "0,00%"

def format_delta_percentage(current, previous, decimals=2):
    """[CORRETO] Cria a string de delta para métricas de porcentagem (valores decimais)."""
    if pd.isna(current): current = 0.0
    if pd.isna(previous): previous = 0.0
    else:
        try:
            previous = float(previous)
        except (ValueError, TypeError):
             previous = 0.0

    if previous == 0:
        return f"{format_percentage(current, decimals)} (Novo)" if current != 0 else "0,00% (0.0%)"

    # Multiplica os valores por 100 para calcular a diferença de p.p.
    delta_val = (float(current) * 100) - (previous * 100)
    delta_pct_points = delta_val

    delta_formatted = f"{delta_pct_points:,.{decimals}f} p.p.".replace('.', ',')
    if delta_pct_points > 0: delta_formatted = f"+{delta_formatted}"
    return f"{delta_formatted}"

# [NOVO] Função para formatar CPR (assumindo que é moeda)
def format_cpr(value):
    """Formata um valor numérico como moeda BRL para CPR."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "R$ 0,00"
        # Formata o número para o padrão brasileiro
        return f"R$ {numeric_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

# [NOVO] Função para criar delta de CPR (valor absoluto e percentual)
def format_delta_cpr(current, previous):
    """Cria a string de delta para métricas de CPR (moeda)."""
    if pd.isna(current): current = 0.0
    if pd.isna(previous) or previous == 0:
        return f"{format_cpr(current)} (Novo)" if current > 0 else "R$ 0,00 (0.0%)"

    delta_val = current - previous
    # Evita divisão por zero se previous for zero
    delta_pct = (delta_val / previous) * 100 if previous != 0 else 0

    delta_val_formatted = f"{delta_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    if delta_val > 0: delta_val_formatted = f"+{delta_val_formatted}"

    # Retorna valor absoluto e percentual
    return f"R$ {delta_val_formatted} ({delta_pct:+.1f}%)".replace('.', ',') # Ajusta formato percentual


# --- CARREGA OS DADOS ---
df_operacional = load_operacional_data() # Agora vindo do loader_op.py

# --- [REMOVIDO] PRÉ-CÁLCULOS GERAIS ---
# A lógica de ordenação de 'Mes' foi removida pois não é necessária.

# --- [REMOVIDO] SIDEBAR DE FILTROS ---
# O filtro de 'Mes' foi removido. A planilha já traz os dados corretos.
# st.sidebar.header("Filtros Operacional")
# ... (lógica de filtro removida) ...


# --- CORPO PRINCIPAL DO DASHBOARD ---
# [ALTERAÇÃO] Verifica apenas se o DataFrame não está vazio.
if not df_operacional.empty:

    # [ALTERAÇÃO] Pega a primeira (e única) linha da planilha
    data_row = df_operacional.iloc[0]

    # --- SEÇÃO INDICADORES GOOGLE E META ---
    col1, col2 = st.columns(2)

    # Coluna 1: Google Ads
    with col1:
        st.markdown("<h6 style='text-align: center;'>Google Ads</h6>", unsafe_allow_html=True)

        # Extrai os valores do Google
        ctr_google_atual = data_row.get('ctr google mes atual', pd.NA)
        ctr_google_anterior = data_row.get('ctr google mes anterior', pd.NA)
        cpr_google_atual = data_row.get('cpr google mes atual', pd.NA)
        cpr_google_anterior = data_row.get('cpr google mes anterior', pd.NA)

        # Calcula os deltas
        delta_ctr_google_str = format_delta_percentage(ctr_google_atual, ctr_google_anterior)
        delta_cpr_google_str = format_delta_cpr(cpr_google_atual, cpr_google_anterior)

        # Exibe as métricas
        with st.container(border=True):
            st.metric(
                label="CTR Atual",
                value=format_percentage(ctr_google_atual),
                delta=delta_ctr_google_str,
                # delta_color="inverse" # Se CTR menor for melhor
            )
        with st.container(border=True):
            st.metric(
                label="CPR Atual",
                value=format_cpr(cpr_google_atual),
                delta=delta_cpr_google_str,
                delta_color="inverse" # Geralmente CPR menor é melhor
            )

    # Coluna 2: Meta Ads
    with col2:
        st.markdown("<h6 style='text-align: center;'>Meta Ads</h6>", unsafe_allow_html=True)

        # Extrai os valores do Meta
        ctr_meta_atual = data_row.get('ctr meta mes atual', pd.NA)
        ctr_meta_anterior = data_row.get('ctr meta mes anterior', pd.NA)
        cpr_meta_atual = data_row.get('cpr meta mes atual', pd.NA)
        cpr_meta_anterior = data_row.get('cpr meta mes anterior', pd.NA)

        # Calcula os deltas
        delta_ctr_meta_str = format_delta_percentage(ctr_meta_atual, ctr_meta_anterior)
        delta_cpr_meta_str = format_delta_cpr(cpr_meta_atual, cpr_meta_anterior)

        # Exibe as métricas
        with st.container(border=True):
            st.metric(
                label="CTR Atual",
                value=format_percentage(ctr_meta_atual),
                delta=delta_ctr_meta_str,
                 # delta_color="inverse" # Se CTR menor for melhor
            )
        with st.container(border=True):
            st.metric(
                label="CPR Atual",
                value=format_cpr(cpr_meta_atual), 
                delta=delta_cpr_meta_str,
                delta_color="inverse" # Geralmente CPR menor é melhor
            )

    st.markdown("---")

    # --- ADICIONE MAIS SEÇÕES AQUI (LEADS, VERBA, etc.) ---

else:
    st.error("Falha ao carregar os dados operacionais. Verifique a planilha ou as configurações.")

