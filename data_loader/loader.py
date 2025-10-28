import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re # Para limpeza avançada

# Define quais colunas esperamos que sejam numéricas
# Vamos limpar e converter apenas estas colunas
numeric_columns = [
    # MRR
    'Receita Orcada', 'Receita Realizada', 'Receita Diferenca',
    # Clientes (Contagem)
    'Essencial Orcado', 'Essencial Realizado', 'Essencial Diferenca',
    'Vender Orcado', 'Vender Realizado', 'Vender Diferenca',
    'Avancado Orcado', 'Avancado Realizado', 'Avancado Diferenca',
    # Receita por Plano (Geral)
    'Receita Essencial', 'Receita Vender', 'Receita Avancado',
    # Churn
    'Churn Orcado', 'Churn Realizado', 'Churn Diferenca',
    # [NOVO] Receita por Plano (Mensal)
    'Receita Essencial Mensal', 'Receita Vender Mensal', 'Receita Avancado Mensal'
]


def clean_brazilian_number(value):
    """
    Converte uma string de número formatada em BRL (ex: "R$ 1.234,56" ou "#N/A")
    para um float (ex: 1234.56) ou pd.NA.
    Também lida com números que já são float.
    """
    if pd.isna(value):
        return pd.NA
    
    # Se já for um número (float/int), apenas retorna
    if isinstance(value, (int, float)):
        return float(value)
        
    # Se for string, limpa
    try:
        # Garante que é uma string e remove espaços
        value_str = str(value).strip()
        
        # Se for um erro da planilha (PROCV), retorna NA
        if value_str.startswith('#'):
            return pd.NA
            
        # Remove caracteres não numéricos (R$, espaços, pontos de milhar)
        # re.sub(r'\s+', '', ...) remove TODOS os tipos de espaço
        cleaned_str = re.sub(r'[R$\.\s]', '', value_str)
        
        # Troca a vírgula do decimal por ponto
        cleaned_str = cleaned_str.replace(',', '.')
        
        # Se a string resultante for vazia (célula era ""), retorna NA
        if not cleaned_str:
            return pd.NA
            
        # Converte para float
        return float(cleaned_str)
        
    except (ValueError, TypeError):
        # Se falhar em qualquer ponto, loga e retorna NA
        # print(f"AVISO: Falha ao converter o valor '{value}' para número.")
        return pd.NA


@st.cache_data(ttl=600) # Cache de 10 minutos
def load_dashboard_data():
    """
    Carrega os dados da aba 'DADOS STREAMLIT'.
    1. Pede ao Google Sheets para EXECUTAR as fórmulas (evaluate_formulas=True).
    2. Pede o valor FORMATADO (ex: "R$ 1.234,56") - (value_render_option='FORMATTED_VALUE').
    3. Limpa e converte manualmente as colunas numéricas para float.
    """
    try:
        creds = st.secrets["connections"]["gsheets"]
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(creds["spreadsheet"])
        
        worksheet = spreadsheet.worksheet("DADOS STREAMLIT")
        
        df = get_as_dataframe(
            worksheet, 
            header=0, 
            value_render_option='FORMATTED_VALUE', # Pega o texto formatado (ex: "R$ 1.234,56")
            evaluate_formulas=True # <--- ESSENCIAL: Executa o PROCV
        )

        # Garante que os nomes das colunas não tenham espaços extras
        df.columns = df.columns.str.strip()

        # Remove linhas que possam estar completamente vazias
        df.dropna(how='all', inplace=True)

        # Aplica a limpeza APENAS nas colunas que definimos como numéricas
        for col in numeric_columns:
            if col in df.columns:
                # O apply garante que a função clean_brazilian_number
                # seja chamada para cada célula (valor) na coluna
                df[col] = df[col].apply(clean_brazilian_number)
            else:
                # Aviso caso uma coluna esperada não seja encontrada
                print(f"AVISO: Coluna numérica esperada '{col}' não encontrada na planilha.")

        return df
        
    except Exception as e:
        st.error(f"Erro fatal ao carregar dados do Google Sheets: {e}")
        # print(f"Erro fatal ao carregar dados: {e}")
        return pd.DataFrame()

