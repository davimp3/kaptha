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
    # [ALTERAÇÃO] Adicionado "vs Mês Anterior"
    return f"R$ {delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"

def format_clients(value):
    """Formata um valor numérico como 'XX clientes'."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "0 clientes"
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
    # [ALTERAÇÃO] Adicionado "vs Mês Anterior"
    return f"{delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"


# --- CARREGA OS DADOS JÁ NUMÉRICOS ---
df = load_dashboard_data()

# --- SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros do Dashboard")

if not df.empty:
    # ORDENAÇÃO CRONOLÓGICA (Corrigido)
    month_order_pt = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                      'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    month_map = {name: i for i, name in enumerate(month_order_pt)}

    def get_sort_key(month_year_str):
        try:
            month_name_str, year_str = month_year_str.lower().split('/')
            year = int(year_str)
            month_num = month_map.get(month_name_str, -1) 
            return (year, month_num)
        except Exception:
            return (0, 0)

    all_months_list = sorted(df['Mes'].unique(), key=get_sort_key)
    
    selected_months = st.sidebar.multiselect(
        "Selecione o(s) Mês(es)",
        options=all_months_list,
        default=all_months_list[-1:] if all_months_list else []
    )
else:
    all_months_list = []
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

    # --- 4. EXIBIÇÃO - SEÇÃO 1: MRR ---
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

    # --- 5. EXIBIÇÃO - SEÇÃO 2: ANÁLISE COMERCIAL (CLIENTES) ---
    st.subheader("Análise Comercial")
    st.caption(f"Período selecionado: {', '.join(sorted(selected_months, key=get_sort_key))}")
    
    col1, col2, col3, col4 = st.columns([0.23, 0.23, 0.23, 0.31]) # Dando mais espaço ao gráfico

    with col1:
        # [ALTERAÇÃO] Adicionado container com borda
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center;'>Essencial</h6>", unsafe_allow_html=True)
            # [ALTERAÇÃO] Removido border=True das métricas internas
            st.metric("Orçado", format_clients(total_essencial_orcado), delta=delta_essencial_orcado_str)
            st.metric("Realizado", format_clients(total_essencial_realizado), delta=delta_essencial_realizado_str)
            st.metric("Diferença", format_clients(total_essencial_diferenca), delta=delta_essencial_diferenca_str, delta_color="inverse")
    
    with col2:
        # [ALTERAÇÃO] Adicionado container com borda
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center;'>Controle</h6>", unsafe_allow_html=True)
            # [ALTERAÇÃO] Removido border=True das métricas internas
            st.metric("Orçado", format_clients(total_vender_orcado), delta=delta_vender_orcado_str)
            st.metric("Realizado", format_clients(total_vender_realizado), delta=delta_vender_realizado_str)
            st.metric("Diferença", format_clients(total_vender_diferenca), delta=delta_vender_diferenca_str, delta_color="inverse")

    with col3:
        # [ALTERAÇÃO] Adicionado container com borda
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center;'>Avançado</h6>", unsafe_allow_html=True)
            # [ALTERAÇÃO] Removido border=True das métricas internas
            st.metric("Orçado", format_clients(total_avancado_orcado), delta=delta_avancado_orcado_str)
            st.metric("Realizado", format_clients(total_avancado_realizado), delta=delta_avancado_realizado_str)
            st.metric("Diferença", format_clients(total_avancado_diferenca), delta=delta_avancado_diferenca_str, delta_color="inverse")

    with col4:
        st.markdown("<h6 style='text-align: center;'>Distribuição dos Planos (Realizado)</h6>", unsafe_allow_html=True)
        labels = ['Essencial', 'Controle', 'Avançado']
        values = [total_essencial_realizado, total_vender_realizado, total_avancado_realizado]
        
        # Define as cores com base na sua imagem (tons de azul)
        colors = ['#06B6D4', '#3B82F6', '#1E40AF'] # Claro, Médio, Escuro

        if sum(values) > 0:
            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.4, 
                # [ALTERAÇÃO] Mostra percentual e valor (contagem)
                texttemplate='%{percent} (%{value})', 
                textfont_size=12,
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
            st.info("Sem dados de clientes realizados para exibir o gráfico.")

    st.markdown("---")

    # --- 6. EXPANDER COM DETALHES DA COMPARAÇÃO ---
    with st.expander("Detalhes da Comparação (Período Anterior)"):
        if not previous_months:
            st.info("Não há dados de período anterior para comparação (a seleção inclui o primeiro mês dos dados).")
        else:
            st.caption(f"Período anterior comparado: {', '.join(previous_months)}")
            
            st.markdown("<h6>Receita (Anterior)</h6>", unsafe_allow_html=True)
            prev_col1, prev_col2, prev_col3 = st.columns(3)
            with prev_col1:
                st.metric("Orçado (Anterior)", format_currency(prev_orcado), border=True)
            with prev_col2:
                st.metric("Realizado (Anterior)", format_currency(prev_realizado), border=True)
            with prev_col3:
                st.metric("Diferença (Anterior)", format_currency(prev_diferenca), border=True)

            st.markdown("<h6>Clientes (Anterior)</h6>", unsafe_allow_html=True)
            prev_c1, prev_c2, prev_c3 = st.columns(3)
            with prev_c1:
                st.markdown("<p style='text-align: center;'>Essencial</p>", unsafe_allow_html=True)
                st.metric("Orçado", format_clients(prev_essencial_orcado), border=True)
                st.metric("Realizado", format_clients(prev_essencial_realizado), border=True)
                st.metric("Diferença", format_clients(prev_essencial_diferenca), border=True)
            with prev_c2:
                st.markdown("<p style='text-align: center;'>Controle</p>", unsafe_allow_html=True)
                st.metric("Orçado", format_clients(prev_vender_orcado), border=True)
                st.metric("Realizado", format_clients(prev_vender_realizado), border=True)
                st.metric("Diferença", format_clients(prev_vender_diferenca), border=True)
            with prev_c3:
                st.markdown("<p style='text-align: center;'>Avançado</p>", unsafe_allow_html=True)
                st.metric("Orçado", format_clients(prev_avancado_orcado), border=True)
                st.metric("Realizado", format_clients(prev_avancado_realizado), border=True)
                st.metric("Diferença", format_clients(prev_avancado_diferenca), border=True)

