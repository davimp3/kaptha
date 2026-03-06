import streamlit as st
import pandas as pd
import os
from datetime import datetime

@st.cache_data(ttl=3600)
def load_leads_data():
    """
    Carrega os dados de leads a partir do ficheiro CSV local.
    O ficheiro deve estar localizado em: data_loader/_DADOS_SPRINTHUB.csv
    """
    # Caminho para o ficheiro dentro da pasta data_loader
    file_path = os.path.join("data_loader", "_DADOS_SPRINTHUB.csv")
    
    # Estrutura inicial de retorno para garantir que o app não quebre se o ficheiro falhar
    relatorio = {
        "este_mes": {"gerados": 0, "qualificados": 0, "diagnostico": 0, "proposta": 0, "vendas": 0, "receita_vendas": 0.0},
        "mes_passado": {"gerados": 0, "qualificados": 0, "diagnostico": 0, "proposta": 0, "vendas": 0, "receita_vendas": 0.0},
        "dois_meses_atras": {"gerados": 0, "qualificados": 0, "diagnostico": 0, "proposta": 0, "vendas": 0, "receita_vendas": 0.0},
        "ultima_atualizacao": "Ficheiro não encontrado"
    }

    try:
        # Verifica se o ficheiro existe antes de tentar ler
        if os.path.exists(file_path):
            # Lê o CSV utilizando o separador ponto e vírgula (;) conforme identificado no ficheiro
            df_leads = pd.read_csv(file_path, sep=';')
            
            # Itera sobre as linhas para preencher o dicionário do relatório
            for _, row in df_leads.iterrows():
                periodo = str(row['Periodo']).strip()
                if periodo in relatorio:
                    relatorio[periodo] = {
                        "gerados": int(row['gerados']),
                        "qualificados": int(row['qualificados']),
                        "diagnostico": int(row['diagnostico']),
                        "proposta": int(row['proposta']),
                        "vendas": int(row['vendas']),
                        "receita_vendas": float(row['receita_vendas'])
                    }
            
            # Obtém a data e hora da última modificação do ficheiro CSV
            mod_time = os.path.getmtime(file_path)
            relatorio["ultima_atualizacao"] = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M")
            
        return relatorio
    except Exception as e:
        # Em caso de erro, exibe um aviso na barra lateral para depuração
        st.sidebar.warning(f"Aviso: Não foi possível ler o CSV de Leads ({e})")
        return relatorio