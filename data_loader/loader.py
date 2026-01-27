import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re

def clean_brazilian_number(value):
    if pd.isna(value):
        return pd.NA
    value_str = str(value).strip()
    if value_str.startswith('#'):
        return pd.NA
    try:
        cleaned_str = re.sub(r'\s+', '', value_str)
        cleaned_str = cleaned_str.replace('R$', '').replace('%', '')
        if '.' in cleaned_str and ',' in cleaned_str:
            cleaned_str = cleaned_str.replace('.', '').replace(',', '.')
        elif ',' in cleaned_str:
            cleaned_str = cleaned_str.replace(',', '.')
        return float(cleaned_str)
    except (ValueError, TypeError):
        return pd.NA

@st.cache_data(ttl=600)
def load_dashboard_data():
    # Removemos o try/except interno para que o erro apareça no seu main.py
    creds_dict = dict(st.secrets["connections"]["gsheets_mrr"])
    
    # AJUSTE TÉCNICO: O Streamlit Cloud às vezes interpreta as quebras de linha da chave de forma errada.
    # Isso garante que a chave privada seja lida corretamente pelo Google.
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # Autenticação
    gc = gspread.service_account_from_dict(creds_dict)
    spreadsheet = gc.open_by_url(creds_dict["spreadsheet"])
    
    # Se o erro for no nome da aba, ele vai "estourar" aqui e você verá no sidebar
    worksheet = spreadsheet.worksheet("DADOS STREAMLIT")
    
    df = get_as_dataframe(worksheet, header=0, value_render_option='FORMATTED_VALUE', evaluate_formulas=True)

    df.columns = df.columns.str.strip()
    df.dropna(how='all', inplace=True)

    numeric_columns = [
        'Receita Orcada', 'Receita Realizada', 'Receita Diferenca',
        'Essencial Orcado', 'Essencial Realizado', 'Essencial Diferenca',
        'Vender Orcado', 'Vender Realizado', 'Vender Diferenca',
        'Avancado Orcado', 'Avancado Realizado', 'Avancado Diferenca',
        'Receita Essencial', 'Receita Vender', 'Receita Avancado',
        'Receita Essencial Mensal', 'Receita Vender Mensal', 'Receita Avancado Mensal',
        'Churn Orcado', 'Churn Realizado', 'Churn Diferenca',
        'Total de Clientes Orcados', 'Total de Clientes Realizados',
        'Churn Orcado Mensal', 'Churn Realizado Mensal' 
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_brazilian_number)

    return df