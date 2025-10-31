import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re

@st.cache_data(ttl=600)
def load_operacional_data():
    """
    Carrega os dados da aba 'DADOS OPERACIONAL', pedindo ao Google Sheets
    pelos valores numéricos brutos (UNFORMATTED_VALUE).
    Isto é mais confiável para decimais (porcentagens) e números.
    """
    try:
        # Conecta na API correta
        creds = st.secrets["connections"]["gsheets_operacional"]
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(creds["spreadsheet"])
        
        # TENTE MUDAR "DADOS OPERACIONAL" se o nome da sua aba for outro
        worksheet = spreadsheet.worksheet("DADOS OPERACIONAL")
        
        # [A CHAVE ESTÁ AQUI]
        # Pede o valor NÚMERICO puro (ex: 0.0540 para 5.40%, e 66.81 para 66,81)
        df = get_as_dataframe(worksheet, 
                              header=0, 
                              value_render_option='UNFORMATTED_VALUE', 
                              evaluate_formulas=True) # Garante que PROCV/fórmulas funcionam

        # Garante que os nomes das colunas não tenham espaços
        df.columns = df.columns.str.strip()

        # Remove linhas que possam estar completamente vazias
        df.dropna(how='all', inplace=True)

        # Não faz nenhuma conversão/limpeza, confia no UNFORMATTED_VALUE
        
        print("[loader_op.py] Dados carregados com sucesso.")
        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados do loader_op.py: {e}")
        st.error(f"Erro no loader_op.py: {e}")
        return pd.DataFrame()
