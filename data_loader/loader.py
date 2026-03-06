import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re

def clean_brazilian_number(value):
    """
    Limpa e converte um número em formato string brasileiro (ex: "R$ 1.234,56" ou "5,40%")
    para um float (ex: 1234.56 ou 5.40).
    """
    if isinstance(value, (int, float)):
        return float(value)

    if pd.isna(value) or value == "":
        return pd.NA
    
    value_str = str(value).strip()
    
    if value_str.startswith('#'):
        return pd.NA
        
    try:
        cleaned_str = re.sub(r'[R$\s%]', '', value_str)
        
        if '.' in cleaned_str and ',' in cleaned_str:
            cleaned_str = cleaned_str.replace('.', '').replace(',', '.')
        elif ',' in cleaned_str:
            cleaned_str = cleaned_str.replace(',', '.')

        return float(cleaned_str)
        
    except (ValueError, TypeError):
        return pd.NA

@st.cache_data(ttl=600)
def load_dashboard_data():
    """
    Carrega os dados da aba 'DADOS STREAMLIT', convertendo valores para float.
    """
    try:
        creds = st.secrets["connections"]["gsheets_mrr"] 
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(creds["spreadsheet"])
        
        worksheet = spreadsheet.worksheet("DADOS STREAMLIT")
        
        df = get_as_dataframe(worksheet, header=0, value_render_option='FORMATTED_VALUE', evaluate_formulas=True)

        df.columns = df.columns.str.strip()
        df.dropna(how='all', inplace=True)

        # Lista de todas as colunas que esperamos que sejam numéricas
        numeric_columns = [
            'Receita Orcada', 'Receita Realizada', 'Receita Diferenca',
            'Essencial Orcado', 'Essencial Realizado', 'Essencial Diferenca',
            'Vender Orcado', 'Vender Realizado', 'Vender Diferenca',
            'Avancado Orcado', 'Avancado Realizado', 'Avancado Diferenca',
            'Receita Essencial', 'Receita Vender', 'Receita Avancado',
            'Receita Essencial Mensal', 'Receita Vender Mensal', 'Receita Avancado Mensal',
            'Churn Orcado', 'Churn Realizado', 'Churn Diferenca',
            'Total de Clientes Orcados', 'Total de Clientes Realizados',
            'Churn Orcado Mensal', 'Churn Realizado Mensal',
            'Churn % Orcado', 'Churn % Realizado',
            'TM Geral',
            'LTV Essencial', 'LTV Vender', 'LTV Avancado',
            'LTV Essencial Total', 'LTV Vender Total', 'LTV Avancado Total'
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_brazilian_number)

        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados da aba 'DADOS STREAMLIT' (MRR): {e}")
        return pd.DataFrame()