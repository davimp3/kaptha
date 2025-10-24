import streamlit as st
import pandas as pd
from data_loader.loader import load_dashboard_data
import plotly.graph_objects as go # Para o gráfico de pizza

st.set_page_config(page_title="Dashboard MMR", layout="wide")

# --- FUNÇÕES DE FORMATAÇÃO ---

def format_currency(value):
    """Formata um valor numérico como moeda BRL."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "R$ 0,00"
        return f"R$ {numeric_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

def format_delta_string(current, previous):
    """Cria a string de delta para o st.metric (R$ e %)."""
    if pd.isna(current): current = 0.0
    if pd.isna(previous) or previous == 0:
        return f"{format_currency(current)} (Novo)" if current > 0 else "R$ 0,00 (0.0%)"
    
    delta_val = current - previous
    delta_pct = delta_val / previous
    delta_val_formatted = f"{delta_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    if delta_val > 0: delta_val_formatted = f"+{delta_val_formatted}"
    # Adicionado "vs Mês Anterior"
    return f"R$ {delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"

def format_clients(value):
    """Formata um valor numérico como 'XX clientes'."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "0 clientes"
        # Se for 1, mostra "cliente" no singular
        if int(numeric_value) == 1 or int(numeric_value) == -1:
             return f"{int(numeric_value)} cliente"
        return f"{int(numeric_value)} clientes"
    except (ValueError, TypeError):
        return "0 clientes"

def format_delta_clients(current, previous):
    """Cria a string de delta para o st.metric de clientes (valor e %)."""
    if pd.isna(current): current = 0.0
    if pd.isna(previous) or previous == 0:
        return f"+{int(current)} (Novo)" if current > 0 else "0 (0.0%)"
        
    delta_val = current - previous
    delta_pct = delta_val / previous
    delta_val_formatted = f"{int(delta_val):+}" # Ex: +3 ou -1
    # Adicionado "vs Mês Anterior"
    return f"{delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"


# --- CARREGA OS DADOS JÁ NUMÉRICOS ---
df = load_dashboard_data()

# --- PRÉ-CÁLCULOS GERAIS (MOVECIDO PARA CIMA) ---
acumulado_total_geral = 0.0
total_orcado_geral = 0.0 
all_months_list = []

if not df.empty:
    # Calcula o acumulado total
    acumulado_total_geral = df['Receita Realizada'].sum()
    total_orcado_geral = df['Receita Orcada'].sum() 
    
    # [MOVECIDO PARA CIMA] ORDENAÇÃO CRONOLÓGICA
    # Define a ordem correta dos meses
    month_order_pt = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]
    # Dicionário para mapear nome do mês para número (0-11)
    month_map = {name: i for i, name in enumerate(month_order_pt)}

    def get_sort_key(month_year_str):
        """
        Converte 'agosto/2025' em uma tupla (ano, num_mes)
        para ordenação correta, ex: (2025, 7).
        """
        try:
            # Garante que a string está em minúsculas para bater com o map
            month_name_str, year_str = month_year_str.lower().split('/')
            year = int(year_str)
            # Usa .get() para evitar erro se o mês não for encontrado
            month_num = month_map.get(month_name_str, -1) 
            return (year, month_num)
        except Exception:
            # Retorna algo que vai para o início em caso de formato inesperado
            return (0, 0)

    # Ordena a lista de meses usando a nova chave personalizada
    all_months_list = sorted(df['Mes'].unique(), key=get_sort_key)
    

# --- SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros do Dashboard")

if not df.empty:
    # Agora 'all_months_list' está disponível aqui
    selected_months = st.sidebar.multiselect(
        "Selecione o(s) Mês(es)",
        options=all_months_list,
        default=all_months_list[-1:] if all_months_list else []
    )
else:
    # all_months_list já é [] por padrão
    selected_months = []
    st.sidebar.error("Não foi possível carregar os dados. Verifique a aba 'DADOS STREAMLIT'.")

# --- CORPO PRINCIPAL DO DASHBOARD ---
if not selected_months:
    st.warning("Por favor, selecione um mês na barra lateral.")
elif df.empty:
    st.error("Falha ao carregar os dados.")
else:
    # --- 1. CÁLCULO DO PERÍODO ATUAL (SOMA) ---
    current_data = df[df['Mes'].isin(selected_months)]
    
    # Receita
    total_orcado = current_data['Receita Orcada'].sum()
    total_realizado = current_data['Receita Realizada'].sum()
    total_diferenca = current_data['Receita Diferenca'].sum()

    # Clientes Essencial
    total_essencial_orcado = current_data['Essencial Orcado'].sum()
    total_essencial_realizado = current_data['Essencial Realizado'].sum()
    total_essencial_diferenca = current_data['Essencial Diferenca'].sum()
    
    # Clientes Controle (Vender)
    total_vender_orcado = current_data['Vender Orcado'].sum()
    total_vender_realizado = current_data['Vender Realizado'].sum()
    total_vender_diferenca = current_data['Vender Diferenca'].sum()

    # Clientes Avançado
    total_avancado_orcado = current_data['Avancado Orcado'].sum()
    total_avancado_realizado = current_data['Avancado Realizado'].sum()
    total_avancado_diferenca = current_data['Avancado Diferenca'].sum()

    # Receita por Plano (para o gráfico de pizza)
    total_receita_essencial = current_data['Receita Essencial'].sum()
    total_receita_vender = current_data['Receita Vender'].sum()
    total_receita_avancado = current_data['Receita Avancado'].sum()

    # [NOVO] Churn
    # Garante que as colunas existem antes de somar
    total_churn_orcado = current_data['Churn Orcado'].sum() if 'Churn Orcado' in current_data else 0.0
    total_churn_realizado = current_data['Churn Realizado'].sum() if 'Churn Realizado' in current_data else 0.0
    total_churn_diferenca = current_data['Churn Diferenca'].sum() if 'Churn Diferenca' in current_data else 0.0


    # --- 2. CÁLCULO DO PERÍODO ANTERIOR ---
    num_selected = len(selected_months)
    earliest_selected_month = min(selected_months, key=lambda m: all_months_list.index(m))
    min_index = all_months_list.index(earliest_selected_month)
    
    prev_start_index = max(0, min_index - num_selected)
    prev_end_index = min_index
    previous_months = all_months_list[prev_start_index:prev_end_index]
    
    # Inicializa totais anteriores
    prev_orcado, prev_realizado, prev_diferenca = 0.0, 0.0, 0.0
    prev_essencial_orcado, prev_essencial_realizado, prev_essencial_diferenca = 0.0, 0.0, 0.0
    prev_vender_orcado, prev_vender_realizado, prev_vender_diferenca = 0.0, 0.0, 0.0
    prev_avancado_orcado, prev_avancado_realizado, prev_avancado_diferenca = 0.0, 0.0, 0.0
    
    if previous_months:
        previous_data = df[df['Mes'].isin(previous_months)]
        # Receita
        prev_orcado = previous_data['Receita Orcada'].sum()
        prev_realizado = previous_data['Receita Realizada'].sum()
        prev_diferenca = previous_data['Receita Diferenca'].sum()
        # Essencial
        prev_essencial_orcado = previous_data['Essencial Orcado'].sum()
        prev_essencial_realizado = previous_data['Essencial Realizado'].sum()
        prev_essencial_diferenca = previous_data['Essencial Diferenca'].sum()
        # Vender
        prev_vender_orcado = previous_data['Vender Orcado'].sum()
        prev_vender_realizado = previous_data['Vender Realizado'].sum()
        prev_vender_diferenca = previous_data['Vender Diferenca'].sum()
        # Avançado
        prev_avancado_orcado = previous_data['Avancado Orcado'].sum()
        prev_avancado_realizado = previous_data['Avancado Realizado'].sum()
        prev_avancado_diferenca = previous_data['Avancado Diferenca'].sum()

    # --- 3. CÁLCULO DAS STRINGS DE DELTA ---
    delta_orcado_str = format_delta_string(total_orcado, prev_orcado)
    delta_realizado_str = format_delta_string(total_realizado, prev_realizado)
    delta_diferenca_str = format_delta_string(total_diferenca, prev_diferenca)
    
    delta_essencial_orcado_str = format_delta_clients(total_essencial_orcado, prev_essencial_orcado)
    delta_essencial_realizado_str = format_delta_clients(total_essencial_realizado, prev_essencial_realizado)
    delta_essencial_diferenca_str = format_delta_clients(total_essencial_diferenca, prev_essencial_diferenca)
    
    delta_vender_orcado_str = format_delta_clients(total_vender_orcado, prev_vender_orcado)
    delta_vender_realizado_str = format_delta_clients(total_vender_realizado, prev_vender_realizado)
    delta_vender_diferenca_str = format_delta_clients(total_vender_diferenca, prev_vender_diferenca)

    delta_avancado_orcado_str = format_delta_clients(total_avancado_orcado, prev_avancado_orcado)
    delta_avancado_realizado_str = format_delta_clients(total_avancado_realizado, prev_avancado_realizado)
    delta_avancado_diferenca_str = format_delta_clients(total_avancado_diferenca, prev_avancado_diferenca)
    
    # --- 4. EXIBIÇÃO - SEÇÃO 1: ACUMULADO TOTAL ---
    st.subheader("Acumulado Total")
    st.caption("Soma de toda a receita realizada em todos os períodos.")
    
    _col_ac_esq, col_ac_centro, _col_ac_dir = st.columns([0.3, 0.4, 0.3]) 

    with col_ac_centro: # Coloca no centro
        st.metric(
            "Receita Total (Geral)", 
            format_currency(acumulado_total_geral),
            border=True
        )
    
    st.markdown("---") # Separador


    # --- 5. EXIBIÇÃO - SEÇÃO 2: MRR ---
    st.subheader("MRR")
    st.caption(f"Período selecionado: {', '.join(sorted(selected_months, key=get_sort_key))}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Orçado", format_currency(total_orcado), delta=delta_orcado_str, border=True)
    with col2:
        st.metric("Realizado", format_currency(total_realizado), delta=delta_realizado_str, border=True)
    with col3:
        st.metric(
            "Diferença", 
            format_currency(total_diferenca), 
            delta=delta_diferenca_str, 
            delta_color="inverse",
            border=True 
        )
    st.markdown("---")

    # --- 6. EXIBIÇÃO - SEÇÃO 3: ANÁLISE COMERCIAL (CLIENTES) ---
    st.subheader("Análise Comercial")
    st.caption(f"Período selecionado: {', '.join(sorted(selected_months, key=get_sort_key))}")
    
    col1, col2, col3, col4 = st.columns([0.23, 0.23, 0.23, 0.31]) # Dando mais espaço ao gráfico

    with col1:
        # Cards de Clientes (Contagem)
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center;'>Essencial</h6>", unsafe_allow_html=True)
            st.metric("Orçado", format_clients(total_essencial_orcado), delta=delta_essencial_orcado_str)
            st.metric("Realizado", format_clients(total_essencial_realizado), delta=delta_essencial_realizado_str)
            st.metric("Diferença", format_clients(total_essencial_diferenca), delta=delta_essencial_diferenca_str, delta_color="inverse")
    
    with col2:
        # Cards de Clientes (Contagem)
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center;'>Controle</h6>", unsafe_allow_html=True)
            st.metric("Orçado", format_clients(total_vender_orcado), delta=delta_vender_orcado_str)
            st.metric("Realizado", format_clients(total_vender_realizado), delta=delta_vender_realizado_str)
            st.metric("Diferença", format_clients(total_vender_diferenca), delta=delta_vender_diferenca_str, delta_color="inverse")

    with col3:
        # Cards de Clientes (Contagem)
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center;'>Avançado</h6>", unsafe_allow_html=True)
            st.metric("Orçado", format_clients(total_avancado_orcado), delta=delta_avancado_orcado_str)
            st.metric("Realizado", format_clients(total_avancado_realizado), delta=delta_avancado_realizado_str)
            st.metric("Diferença", format_clients(total_avancado_diferenca), delta=delta_avancado_diferenca_str, delta_color="inverse")

    with col4:
        # Gráfico de Pizza por Receita (Valor)
        st.markdown("<h6 style='text-align: center;'>Distribuição da Receita (Realizado)</h6>", unsafe_allow_html=True)
        labels = ['Essencial', 'Controle', 'Avançado']
        values = [total_receita_essencial, total_receita_vender, total_receita_avancado]
        
        # Criação de dados customizados para o hover/texto
        custom_data = [format_currency(v) for v in values]
        
        # Define as cores com base na sua imagem (tons de azul)
        colors = ['#06B6D4', '#3B82F6', '#1E40AF'] # Claro, Médio, Escuro

        if sum(values) > 0:
            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.4, 
                
                customdata=custom_data,
                # [ALTERAÇÃO] Mostra SOMENTE o valor formatado
                texttemplate='%{customdata}', 
                textfont_size=12,
                # [ALTERAÇÃO] Hover mostra percentual também
                hovertemplate='<b>%{label}</b><br>Receita: %{customdata} (%{percent:.0f})<extra></extra>', 
                
                marker=dict(colors=colors, line=dict(color='#FFFFFF', width=1)),
                sort=False # Mantém a ordem Essencial, Controle, Avançado
            )])
            
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                paper_bgcolor='rgba(0,0,0,0)', # Fundo transparente
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white") # Cor da legenda
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de receita por plano para exibir o gráfico.")

    st.markdown("---")

    # --- 7. EXIBIÇÃO - SEÇÃO 4: CHURN (NOVO) ---
    # Adicionado no lugar do expander removido
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    # Usando st.markdown para centralizar e formatar o texto pequeno
    with col_c1:
        st.markdown(f"<p style='text-align: center; font-size: 0.9em; opacity: 0.8;'>Churn Orçado(Todos os Períodos)</p>"
                    f"<h5 style='text-align: center;'>{format_clients(total_churn_orcado)}</h5>", 
                    unsafe_allow_html=True)
    with col_c2:
        st.markdown(f"<p style='text-align: center; font-size: 0.9em; opacity: 0.8;'>Churn Realizado(Todos os Períodos)</p>"
                    f"<h5 style='text-align: center;'>{format_clients(total_churn_realizado)}</h5>", 
                    unsafe_allow_html=True)
    with col_c3:
        st.markdown(f"<p style='text-align: center; font-size: 0.9em; opacity: 0.8;'>Churn Diferença(Todos os Períodos)</p>"
                    f"<h5 style='text-align: center;'>{format_clients(total_churn_diferenca)}</h5>", 
                    unsafe_allow_html=True)

