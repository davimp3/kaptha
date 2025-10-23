import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re # Para limpeza avançada

def clean_brazilian_number(value):
    """
    Limpa e converte uma string de número no padrão BRL para float.
    Trata "R$", ".", ",", espaços e erros de planilha como "#N/A".
    """
    if not isinstance(value, str):
        # Se já for um número (improvável, mas seguro), apenas retorna
        return pd.to_numeric(value, errors='coerce')

    # 1. Verifica se é um erro de VLOOKUP (PROCV)
    if value.strip().startswith('#'):
        # print(f"AVISO: Detectado erro de planilha ('{value}'). Convertendo para NA.")
        return pd.NA

    try:
        # 2. Limpeza agressiva:
        # Remove "R$", remove qualquer tipo de espaço (incluindo &nbsp;)
        cleaned_value = re.sub(r'\s+', '', value)
        cleaned_value = cleaned_value.replace('R$', '')
        
        # Remove "." de milhar
        cleaned_value = cleaned_value.replace('.', '')
        # Troca "," de decimal por "."
        cleaned_value = cleaned_value.replace(',', '.')
        
        # 3. Converte para float
        return float(cleaned_value)

    except (ValueError, TypeError) as e:
        # 4. Falha na conversão
        # Comentado para não poluir o log, mas útil para debug
        # print(f"AVISO: Falha ao converter o valor '{value}' para número. Erro: {e}")
        return pd.NA

@st.cache_data(ttl=600)
def load_dashboard_data():
    """
    Carrega os dados da aba 'DADOS STREAMLIT'.
    1. Pede ao Google Sheets para EXECUTAR as fórmulas (evaluate_formulas=True).
    2. Pede pelo valor FORMATADO (value_render_option='FORMATTED_VALUE').
    3. Limpa e converte manualmente as colunas numéricas.
    """
    try:
        creds = st.secrets["connections"]["gsheets"]
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(creds["spreadsheet"])
        
        worksheet = spreadsheet.worksheet("DADOS STREAMLIT")
        
        # evaluate_formulas=True é CRÍTICO para executar o VLOOKUP
        df = get_as_dataframe(
            worksheet, 
            header=0, 
            value_render_option='FORMATTED_VALUE',
            evaluate_formulas=True # <--- A CHAVE!
        )

        # Garante que os nomes das colunas não tenham espaços
        df.columns = df.columns.str.strip()
        df.dropna(how='all', inplace=True)

        # --- [ATUALIZAÇÃO AQUI] ---
        # Define quais colunas esperamos que sejam numéricas
        numeric_columns = [
            'Receita Orcada', 'Receita Realizada', 'Receita Diferenca',
            'Essencial Orcado', 'Essencial Realizado', 'Essencial Diferenca',
            'Vender Orcado', 'Vender Realizado', 'Vender Diferenca', # Assumindo "Vender" da planilha
            'Avancado Orcado', 'Avancado Realizado', 'Avancado Diferenca'
        ]
        
        # --- DEBUG: Imprime amostras (opcional) ---
        # print("\n--- DEBUG: Amostra de 'Mes' lido da planilha ---")
        # if 'Mes' in df.columns:
        #     print(df['Mes'].unique())
        # else:
        #     print("AVISO: Coluna 'Mes' não encontrada.")
        # print("-------------------------------------------------\n")
        
        # Aplica a limpeza APENAS nas colunas numéricas
        for col in numeric_columns:
            if col in df.columns:
                # print(f"--- DEBUG: Limpando coluna '{col}' ---")
                # Amostra antes
                # if not df[col].empty:
                #     print(f"Amostra ANTES: {df[col].iloc[0]} (tipo: {type(df[col].iloc[0])})")
                    
                df[col] = df[col].apply(clean_brazilian_number)
                
                # Amostra depois
                # if not df[col].dropna().empty:
                #     print(f"Amostra DEPOIS: {df[col].dropna().iloc[0]} (tipo: {type(df[col].dropna().iloc[0])})")
                # else:
                #     print(f"Amostra DEPOIS: (Coluna Vazia ou só NA)")
            # else:
            #     print(f"AVISO: Coluna numérica '{col}' não encontrada no DataFrame.")

        return df
        
    except Exception as e:
        print(f"Erro CRÍTICO ao carregar dados da aba 'DADOS STREAMLIT': {e}")
        return pd.DataFrame()

