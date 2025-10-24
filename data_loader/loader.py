import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import re # Para limpeza avançada

# [INÍCIO DA FUNÇÃO AUXILIAR DE LIMPEZA]
def clean_brazilian_number(value):
    """
    Converte uma string de número formatada em BRL (ex: "R$ 1.234,56" ou "#N/A")
    para um float (ex: 1234.56) ou pd.NA.
    """
    if not isinstance(value, str):
        # Se já for um número (float, int), apenas retorna
        return pd.to_numeric(value, errors='coerce')

    # Se for um erro da planilha (ex: #N/A, #REF!), retorna NA
    if value.strip().startswith('#'):
        return pd.NA

    try:
        # Limpeza agressiva:
        # 1. Remove "R$"
        # 2. Remove todos os tipos de espaços (incluindo &nbsp;)
        # 3. Remove o separador de milhar "."
        # 4. Troca a vírgula decimal "," por "."
        cleaned_value = re.sub(r'\s+', '', value.replace("R$", "")).replace(".", "").replace(",", ".")
        
        # Converte para float, se não for vazio
        if cleaned_value:
            return float(cleaned_value)
        else:
            return pd.NA
            
    except Exception as e:
        # Adiciona um print de aviso no console do Streamlit
        print(f"AVISO: Falha ao converter o valor '{value}' para número. Erro: {e}")
        return pd.NA
# [FIM DA FUNÇÃO AUXILIAR DE LIMPEZA]


@st.cache_data(ttl=600)
def load_dashboard_data():
    """
    Carrega os dados da aba 'DADOS STREAMLIT', pedindo ao Google Sheets
    pelos valores formatados e executando as fórmulas.
    """
    try:
        creds = st.secrets["connections"]["gsheets"]
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(creds["spreadsheet"])
        
        worksheet = spreadsheet.worksheet("DADOS STREAMLIT")
        
        # Pede ao Google para EXECUTAR as fórmulas (PROCV) e nos dar o valor formatado.
        df = get_as_dataframe(worksheet, header=0, value_render_option='FORMATTED_VALUE', evaluate_formulas=True)

        # Garante que os nomes das colunas não tenham espaços
        df.columns = df.columns.str.strip()

        # Remove linhas que possam estar completamente vazias
        df.dropna(how='all', inplace=True)

        # --- Limpeza e Conversão Manual ---
        # Lista de todas as colunas que devem ser numéricas
        numeric_columns = [
            # Receita
            'Receita Orcada', 'Receita Realizada', 'Receita Diferenca',
            # Clientes (Contagem)
            'Essencial Orcado', 'Essencial Realizado', 'Essencial Diferenca',
            'Vender Orcado', 'Vender Realizado', 'Vender Diferenca',
            'Avancado Orcado', 'Avancado Realizado', 'Avancado Diferenca',
            # Receita por Plano (Valor)
            'Receita Essencial', 'Receita Vender', 'Receita Avancado',
            # [NOVO] Churn
            'Churn Orcado', 'Churn Realizado', 'Churn Diferenca'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                # Aplica a função de limpeza em toda a coluna
                df[col] = df[col].apply(clean_brazilian_number)
            else:
                # Não mostra aviso para colunas que podem não existir ainda
                # print(f"AVISO: A coluna numérica esperada '{col}' não foi encontrada na planilha.")
                pass

        return df
        
    except Exception as e:
        st.error(f"Erro fatal ao carregar dados: {e}")
        return pd.DataFrame()

