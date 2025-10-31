import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re

def clean_brazilian_number(value):
    """
    Limpa e converte um número em formato string brasileiro (ex: "R$ 1.234,56" ou "5,40%")
    para um float (ex: 1234.56 ou 5.40).
    Também lida com erros de VLOOKUP (#N/A).
    """
    if pd.isna(value):
        return pd.NA
    
    # Converte para string para garantir que os métodos .strip() e .startswith() funcionem
    value_str = str(value).strip()
    
    # Se for um erro de planilha (como #N/A ou #REF!), retorna NA
    if value_str.startswith('#'):
        return pd.NA
        
    try:
        # Remove "R$", "%", espaços (incluindo não-quebráveis \u00A0)
        # Usa regex para remover todos os tipos de espaço
        cleaned_str = re.sub(r'\s+', '', value_str)
        cleaned_str = cleaned_str.replace('R$', '').replace('%', '')
        
        # Converte o formato brasileiro para o formato americano
        # Ex: "1.234,56" -> "1234.56"
        if '.' in cleaned_str and ',' in cleaned_str:
            # Assume formato 1.234,56
            cleaned_str = cleaned_str.replace('.', '').replace(',', '.')
        elif ',' in cleaned_str:
            # Assume formato 1,23
            cleaned_str = cleaned_str.replace(',', '.')
        
        # Tenta converter para float
        return float(cleaned_str)
        
    except (ValueError, TypeError):
        # Se falhar (ex: célula vazia "" ou texto inesperado), retorna NA
        return pd.NA

@st.cache_data(ttl=600)
def load_dashboard_data():
    """
    Carrega os dados da aba 'DADOS STREAMLIT', pedindo ao Google Sheets
    pelos valores formatados e executando fórmulas.
    """
    try:
        # Usa a conexão específica do MRR
        creds = st.secrets["connections"]["gsheets_mrr"] 
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(creds["spreadsheet"])
        
        worksheet = spreadsheet.worksheet("DADOS STREAMLIT")
        
        # Pede ao Google para EXECUTAR as fórmulas (PROCV) e nos dar o valor formatado (a string)
        df = get_as_dataframe(worksheet, header=0, value_render_option='FORMATTED_VALUE', evaluate_formulas=True)

        # Garante que os nomes das colunas não tenham espaços
        df.columns = df.columns.str.strip()

        # Remove linhas que possam estar completamente vazias
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
            # [NOVAS COLUNAS ADICIONADAS]
            'Churn Orcado Mensal', 'Churn Realizado Mensal' 
        ]

        # Limpa e converte apenas as colunas numéricas que existem no DataFrame
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_brazilian_number)
            # else:
            #     print(f"Aviso: A coluna numérica '{col}' não foi encontrada na planilha.")

        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados da aba 'DADOS STREAMLIT' (MRR): {e}")
        return pd.DataFrame()

