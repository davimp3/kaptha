import streamlit as st
import pandas as pd
from data_loader.loader import load_dashboard_data # Importa do loader correto
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # Para o rodízio automático
from datetime import datetime # Para encontrar o mês atual
import locale # Para formatar o nome do mês em português

# Configuração da página
st.set_page_config(page_title="Dashboard MMR", layout="wide")

# --- AJUSTE DE CSS PARA REMOVER PADDING E AJUSTAR FONTES ESPECÍFICAS ---
st.markdown("""
    <style>
        /* Define a fonte global para Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="st-"], [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* Remove padding superior do container principal */
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }
        [data-testid="stAppViewContainer"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }

        /* Ajusta padding geral da página */
        .stApp {
            padding: 0.05rem !important;
        }
        /* Reduz o espaço entre as colunas */
        [data-testid="stHorizontalBlock"] {
            gap: 0.1rem !important;
        }
        /* Reduz o padding dos containers de borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.1rem !important;
        }

        /* Fonte dos títulos (h6) - Mantida no tamanho original solicitado */
        h6 { 
            font-size: 0.85rem !important; 
            margin: 0 !important; 
            font-weight: 700 !important; 
            text-align: center;
        }
        
        /* h5 usado para labels de Churn no rodapé */
        h5 { font-size: 0.85rem !important; margin: 0 !important; }
        
        /* Reduz o tamanho das legendas */
        [data-testid="stCaption"] {
            font-size: 0.6rem !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        /* Reduz o espaço dos separadores */
        hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

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
    delta_pct = (delta_val / previous) if previous != 0 else 0
    delta_val_formatted = f"{delta_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    if delta_val > 0: delta_val_formatted = f"+{delta_val_formatted}"
    return f"R$ {delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"

def format_clients(value):
    """Formata um valor numérico como clientes."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "0 clientes"
        if int(numeric_value) == 1 or int(numeric_value) == -1:
             return f"{int(numeric_value)} cliente"
        return f"{int(numeric_value)} clientes"
    except (ValueError, TypeError):
        return "0 clientes"

def format_delta_clients(current, previous):
    """Cria a string de delta para métricas de clientes."""
    if pd.isna(current): current = 0.0
    if pd.isna(previous) or previous == 0:
        return f"+{int(current)} (Novo)" if current > 0 else "0 (0.0%)"
    delta_val = current - previous
    delta_pct = (delta_val / previous) if previous != 0 else 0
    delta_val_formatted = f"{int(delta_val):+}"
    return f"{delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"

def format_percent(value):
    """Formata um valor decimal como percentagem."""
    try:
        numeric_value = float(value)
        if pd.isna(numeric_value):
            return "0,0%"
        return f"{numeric_value:.1%}".replace('.', ',')
    except (ValueError, TypeError):
        return "0,0%"

# --- CARREGA OS DADOS ---
df = load_dashboard_data()

# --- PRÉ-CÁLCULOS GERAIS ---
all_months_list = []
default_month_selection = [] 
past_and_current_months = [] 

if not df.empty:
    month_order_pt = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    month_map = {name: i for i, name in enumerate(month_order_pt)}

    def get_sort_key(month_year_str):
        try:
            month_name_str, year_str = month_year_str.lower().split('/')
            return (int(year_str), month_map.get(month_name_str, -1))
        except Exception:
            return (0, 0)

    all_months_list = sorted(df['Mes'].unique(), key=get_sort_key)
    
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        pass 

    now = datetime.now()
    current_month_str = f"{now.strftime('%B').lower()}/{now.year}" 
    
    current_month_index = -1
    if current_month_str in all_months_list:
        current_month_index = all_months_list.index(current_month_str)
        default_month_selection = [current_month_str]
        past_and_current_months = all_months_list[:current_month_index + 1]
    else:
        if all_months_list:
            default_month_selection = [all_months_list[-1]]
            past_and_current_months = all_months_list

# --- SIDEBAR E RODÍZIO ---
st.sidebar.header("Controlos")
auto_rotate_views = st.sidebar.checkbox("Rodízio automático (30s)", value=True)

if not df.empty:
    selected_months_acumulado = st.sidebar.multiselect("Meses (Acumulado)", options=all_months_list, default=past_and_current_months)
    selected_months_mrr = st.sidebar.multiselect("Meses (MRR & Comercial)", options=all_months_list, default=default_month_selection)

# Mantendo as 5 telas solicitadas
page_options = ['MRR', 'COMERCIAL', 'GRAFICO_RECEITA', 'META_CLIENTES', 'GRAFICO_CHURN'] 

if auto_rotate_views:
    count = st_autorefresh(interval=30000, key="view_switcher")
    page_index = count % 5 
    view_to_show = page_options[page_index]
else:
    view_to_show = st.sidebar.radio("Navegação", page_options, label_visibility="collapsed")

# --- LÓGICA DE EXIBIÇÃO ---
if not selected_months_mrr: 
    st.warning("Selecione um mês no filtro.")
elif df.empty:
    st.error("Erro ao carregar dados.")
else:
    current_data = df[df['Mes'].isin(selected_months_mrr)]

    # Cálculo dos valores atuais para métricas
    total_orcado = current_data['Receita Orcada'].sum()
    total_realizado = current_data['Receita Realizada'].sum()
    total_diferenca = current_data['Receita Diferenca'].sum()

    total_essencial_orcado = current_data['Essencial Orcado'].sum()
    total_essencial_realizado = current_data['Essencial Realizado'].sum()
    total_essencial_diferenca = current_data['Essencial Diferenca'].sum()
    total_vender_orcado = current_data['Vender Orcado'].sum()
    total_vender_realizado = current_data['Vender Realizado'].sum()
    total_vender_diferenca = current_data['Vender Diferenca'].sum()
    total_avancado_orcado = current_data['Avancado Orcado'].sum()
    total_avancado_realizado = current_data['Avancado Realizado'].sum()
    total_avancado_diferenca = current_data['Avancado Diferenca'].sum()

    total_planos_orcado = total_essencial_orcado + total_vender_orcado + total_avancado_orcado
    total_planos_realizado = total_essencial_realizado + total_vender_realizado + total_avancado_realizado
    total_planos_diferenca = total_essencial_diferenca + total_vender_diferenca + total_avancado_diferenca

    total_receita_essencial = current_data['Receita Essencial'].sum()
    total_receita_vender = current_data['Receita Vender'].sum()
    total_receita_avancado = current_data['Receita Avancado'].sum()
    total_receita_essencial_mensal = current_data['Receita Essencial Mensal'].sum() if 'Receita Essencial Mensal' in current_data else 0.0
    total_receita_vender_mensal = current_data['Receita Vender Mensal'].sum() if 'Receita Vender Mensal' in current_data else 0.0
    total_receita_avancado_mensal = current_data['Receita Avancado Mensal'].sum() if 'Receita Avancado Mensal' in current_data else 0.0

    total_churn_orcado = current_data['Churn Orcado'].sum() if 'Churn Orcado' in current_data else 0.0
    total_churn_realizado = current_data['Churn Realizado'].sum() if 'Churn Realizado' in current_data else 0.0
    total_churn_diferenca = current_data['Churn Diferenca'].sum() if 'Churn Diferenca' in current_data else 0.0

    # Cálculo do Período Anterior
    num_sel = len(selected_months_mrr)
    earliest = min(selected_months_mrr, key=lambda m: all_months_list.index(m))
    idx = all_months_list.index(earliest)
    prev_months = all_months_list[max(0, idx - num_sel):idx]
    
    prev_orcado=0.0; prev_realizado=0.0; prev_diferenca=0.0
    prev_essencial_orcado=0.0; prev_essencial_realizado=0.0; prev_essencial_diferenca=0.0
    prev_vender_orcado=0.0; prev_vender_realizado=0.0; prev_vender_diferenca=0.0
    prev_avancado_orcado=0.0; prev_avancado_realizado=0.0; prev_avancado_diferenca=0.0
    prev_planos_orcado=0.0; prev_planos_realizado=0.0; prev_planos_diferenca=0.0 

    if prev_months:
        prev_data = df[df['Mes'].isin(prev_months)]
        prev_orcado = prev_data['Receita Orcada'].sum()
        prev_realizado = prev_data['Receita Realizada'].sum()
        prev_diferenca = prev_data['Receita Diferenca'].sum()
        prev_essencial_orcado = prev_data['Essencial Orcado'].sum()
        prev_essencial_realizado = prev_data['Essencial Realizado'].sum()
        prev_essencial_diferenca = prev_data['Essencial Diferenca'].sum()
        prev_vender_orcado = prev_data['Vender Orcado'].sum()
        prev_vender_realizado = prev_data['Vender Realizado'].sum()
        prev_vender_diferenca = prev_data['Vender Diferenca'].sum()
        prev_avancado_orcado = prev_data['Avancado Orcado'].sum()
        prev_avancado_realizado = prev_data['Avancado Realizado'].sum()
        prev_avancado_diferenca = prev_data['Avancado Diferenca'].sum()
        prev_planos_orcado = prev_essencial_orcado + prev_vender_orcado + prev_avancado_orcado
        prev_planos_realizado = prev_essencial_realizado + prev_vender_realizado + prev_avancado_realizado
        prev_planos_diferenca = prev_essencial_diferenca + prev_vender_diferenca + prev_avancado_diferenca

    # Deltas
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
    delta_planos_orcado_str = format_delta_clients(total_planos_orcado, prev_planos_orcado)
    delta_planos_realizado_str = format_delta_clients(total_planos_realizado, prev_planos_realizado)
    delta_planos_diferenca_str = format_delta_clients(total_planos_diferenca, prev_planos_diferenca)

    # Taxa de Churn
    base_cli_total = current_data['Total de Clientes Realizados'].sum()
    rate_orc = (total_churn_orcado / base_cli_total) if base_cli_total > 0 else 0
    rate_real = (total_churn_realizado / base_cli_total) if base_cli_total > 0 else 0

    # Apoio Visual
    labels = ['Essencial', 'Controle', 'Avançado']
    colors = ['#41D9FF', '#E8C147', '#69FF4E']

    if view_to_show == 'MRR':
        # --- TELA 1: MRR ---
        df_ac = df[df['Mes'].isin(selected_months_acumulado)]
        acum_total = df_ac['Receita Realizada'].sum()
        st.caption(f"Acumulado: {', '.join(sorted(selected_months_acumulado, key=get_sort_key))}")
        
        _, col_ac, _ = st.columns([0.3, 0.4, 0.3])
        with col_ac:
            st.metric("Receita Total (Geral)", format_currency(acum_total), border=True)
        st.markdown("---")
        st.subheader("MRR")
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçado", format_currency(total_orcado), delta=delta_orcado_str, border=True)
        c2.metric("Realizado", format_currency(total_realizado), delta=delta_realizado_str, border=True, delta_color="inverse")
        # [RESTAURADO] Adicionado o delta para Diferença
        c3.metric("Diferença", format_currency(total_diferenca), delta=delta_diferenca_str, border=True, delta_color="inverse")

    elif view_to_show == 'COMERCIAL':
        # --- TELA 2: COMERCIAL ---
        
        # [AJUSTE SOLICITADO] CSS Scoped: Fonte reduzida e BOLD para o valor da métrica nesta sessão
        st.markdown("""
            <style>
                [data-testid="stMetricValue"] {
                    font-size: 0.95rem !important;
                    font-weight: bold !important;
                }
                [data-testid="stMetricDelta"] {
                    font-size: 0.75rem !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
        st.caption(f"Período: {', '.join(selected_months_mrr)}")
        m_l, m_r = st.columns([0.65, 0.35])
        
        with m_l:
            c1, c2, c3, c4 = st.columns(4)
            # Cards Essencial
            with c1:
                with st.container(border=True):
                    st.markdown("<h6>Essencial</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_essencial_orcado), delta=delta_essencial_orcado_str)
                    st.metric("Realizado", format_clients(total_essencial_realizado), delta=delta_essencial_realizado_str)
                    st.metric("Diferença", format_clients(total_essencial_diferenca), delta=delta_essencial_diferenca_str, delta_color="normal")
            # Cards Controle
            with c2:
                with st.container(border=True):
                    st.markdown("<h6>Controle</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_vender_orcado), delta=delta_vender_orcado_str)
                    st.metric("Realizado", format_clients(total_vender_realizado), delta=delta_vender_realizado_str)
                    st.metric("Diferença", format_clients(total_vender_diferenca), delta=delta_vender_diferenca_str, delta_color="normal")
            # Cards Avançado
            with c3:
                with st.container(border=True):
                    st.markdown("<h6>Avançado</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_avancado_orcado), delta=delta_avancado_orcado_str)
                    st.metric("Realizado", format_clients(total_avancado_realizado), delta=delta_avancado_realizado_str)
                    st.metric("Diferença", format_clients(total_avancado_diferenca), delta=delta_avancado_diferenca_str, delta_color="normal")
            # Cards Total
            with c4:
                with st.container(border=True):
                    st.markdown("<h6>Total</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_planos_orcado), delta=delta_planos_orcado_str)
                    st.metric("Realizado", format_clients(total_planos_realizado), delta=delta_planos_realizado_str)
                    st.metric("Diferença", format_clients(total_planos_diferenca), delta=delta_planos_diferenca_str, delta_color="normal")

            st.markdown("---")
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em;'>Churn Orçado</p><h5 style='text-align: center;'>{format_clients(total_churn_orcado)}</h5>", unsafe_allow_html=True)
            with cc2:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em;'>Churn Realizado</p><h5 style='text-align: center;'>{format_clients(total_churn_realizado)}</h5>", unsafe_allow_html=True)
            with cc3:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em;'>Diferença</p><h5 style='text-align: center;'>{format_clients(total_churn_diferenca)}</h5>", unsafe_allow_html=True)

        with m_r:
            st.markdown("<h6>Distribuição Mensal</h6>", unsafe_allow_html=True)
            vals_m = [total_receita_essencial_mensal, total_receita_vender_mensal, total_receita_avancado_mensal]
            if sum(vals_m) > 0:
                fig_m = go.Figure(data=[go.Pie(labels=labels, values=vals_m, hole=.4, marker=dict(colors=colors))])
                fig_m.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=5), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_m, use_container_width=True)
            
            st.markdown("<h6>Distribuição Geral</h6>", unsafe_allow_html=True)
            vals_g = [total_receita_essencial, total_receita_vender, total_receita_avancado]
            if sum(vals_g) > 0:
                fig_g = go.Figure(data=[go.Pie(labels=labels, values=vals_g, hole=.4, marker=dict(colors=colors))])
                fig_g.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=5), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_g, use_container_width=True)

    elif view_to_show == 'GRAFICO_RECEITA':
        # --- TELA 3: RECEITA ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        with st.container(border=True):
            st.subheader("Meta MRR Anual")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Receita Orcada'], mode='lines+markers+text', name='Orçado', line=dict(color='blue'), text=[format_currency(v) for v in chart_df['Receita Orcada']], textposition='top center'))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Receita Realizada'], mode='lines+markers+text', name='Realizado', line=dict(color='green'), text=[format_currency(v) for v in chart_df['Receita Realizada']], textposition='top center'))
            fig.update_layout(height=320, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)

    elif view_to_show == 'META_CLIENTES':
        # --- TELA 4: CLIENTES ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        with st.container(border=True):
            st.subheader("Meta Clientes Anual")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Total de Clientes Orcados'], mode='lines+markers+text', name='Orçado', line=dict(color='blue'), text=[format_clients(v) for v in chart_df['Total de Clientes Orcados']], textposition='top center'))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Total de Clientes Realizados'], mode='lines+markers+text', name='Realizado', line=dict(color='green'), text=[format_clients(v) for v in chart_df['Total de Clientes Realizados']], textposition='top center'))
            fig.update_layout(height=320, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)

    elif view_to_show == 'GRAFICO_CHURN':
        # --- TELA 5: CHURN VALORES ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        with st.container(border=True):
            st.subheader("Evolução de Churn (Unidades)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Churn Orcado Mensal'], mode='lines+markers+text', name='Orçado', line=dict(color='red'), text=[format_clients(v) for v in chart_df['Churn Orcado Mensal']], textposition='top center'))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Churn Realizado Mensal'], mode='lines+markers+text', name='Realizado', line=dict(color='#800080'), text=[format_clients(v) for v in chart_df['Churn Realizado Mensal']], textposition='top center'))
            fig.update_layout(height=320, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)