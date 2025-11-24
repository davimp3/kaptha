import streamlit as st
import pandas as pd
from data_loader.loader import load_dashboard_data # Importa do loader correto (do Canvas)
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # Para o rodízio
from datetime import datetime # Para encontrar o mês atual
import locale # Para formatar o nome do mês em português

st.set_page_config(page_title="Dashboard MMR", layout="wide")

# --- AJUSTE DE CSS PARA REMOVER PADDING SUPERIOR ---
st.markdown("""
    <style>
        /* Define a fonte global para Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="st-"], [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* Remove TODO padding, margin e border do container principal para o topo */
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }
        [data-testid="stAppViewContainer"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }

        /* Ajusta padding geral da página para quase zero */
        .stApp {
            padding: 0.05rem !important;
        }
        /* Reduz o gap (espaço) entre as colunas */
        [data-testid="stHorizontalBlock"] {
            gap: 0.1rem !important;
        }
        /* Reduz o padding dos containers de borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.1rem !important;
        }
        /* Reduz o padding dos containers de métrica */
        [data-testid="stMetric"] {
            padding: 0px !important;
            margin: 0px !important;
        }
        /* Reduz o tamanho das fontes de título h6 e h5 */
        h6 { font-size: 0.8rem !important; margin: 0 !important; }
        h5 { font-size: 1.0rem !important; margin: 0 !important; }
        /* Reduz o tamanho das legendas */
        [data-testid="stCaption"] {
            font-size: 0.6rem !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        /* Reduz o espaço dos separadores (---) */
        hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
# --- FIM DO AJUSTE DE CSS ---


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
    delta_pct = (delta_val / previous) if previous != 0 else 0 # Evita divisão por zero
    delta_val_formatted = f"{delta_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    if delta_val > 0: delta_val_formatted = f"+{delta_val_formatted}"
    return f"R$ {delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"

def format_clients(value):
    """Formata um valor numérico como 'XX clientes'."""
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
    """Cria a string de delta para o st.metric de clientes (valor e %)."""
    if pd.isna(current): current = 0.0
    if pd.isna(previous) or previous == 0:
        return f"+{int(current)} (Novo)" if current > 0 else "0 (0.0%)"

    delta_val = current - previous
    delta_pct = (delta_val / previous) if previous != 0 else 0 # Evita divisão por zero
    delta_val_formatted = f"{int(delta_val):+}" # Ex: +3 ou -1
    return f"{delta_val_formatted} ({delta_pct:+.1%}) vs Mês Anterior"


# --- CARREGA OS DADOS JÁ NUMÉRICOS ---
df = load_dashboard_data() # Usa o loader do MRR (do Canvas)

# --- PRÉ-CÁLCULOS GERAIS ---
all_months_list = []
default_month_selection = [] 
past_and_current_months = [] 

if not df.empty:
    
    # --- Lógica de Ordenação e Datas ---
    month_order_pt = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]
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
    
    # --- Lógica para Mês Atual e Acumulado ---
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252') # Windows
        except:
            pass 

    now = datetime.now()
    current_month_str = f"{now.strftime('%B').lower()}/{now.year}" 
    
    current_month_index = -1
    if current_month_str in all_months_list:
        current_month_index = all_months_list.index(current_month_str)
        default_month_selection = [current_month_str]
    else:
        if all_months_list:
            current_month_index = len(all_months_list) - 1
            default_month_selection = [all_months_list[-1]]
            
    if current_month_index != -1:
        past_and_current_months = all_months_list[:current_month_index + 1]
    else:
        past_and_current_months = all_months_list


# --- SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros do Dashboard")

auto_rotate_views = st.sidebar.checkbox("Rodízio automático de telas (30s)", value=True)

if not df.empty:
    selected_months_acumulado = st.sidebar.multiselect(
        "Selecionar Meses (Acumulado Total)",
        options=all_months_list,
        default=past_and_current_months 
    )
    
    selected_months_mrr = st.sidebar.multiselect(
        "Selecionar Meses (MRR & Comercial)",
        options=all_months_list,
        default=default_month_selection
    )
else:
    selected_months_acumulado = []
    selected_months_mrr = []
    st.sidebar.error("Não foi possível carregar os dados. Verifique a aba 'DADOS STREAMLIT'.")


# --- LÓGICA DE RODÍZIO DE TELA ---
view_to_show = 'MRR'
page_options = ['MRR', 'COMERCIAL', 'GRAFICO_RECEITA', 'META_CLIENTES', 'GRAFICO_CHURN'] 

if auto_rotate_views:
    count = st_autorefresh(interval=30000, key="view_switcher")
    page_index = count % 5 
    view_to_show = page_options[page_index]

else:
    view_to_show = st.sidebar.radio(
        "Selecionar visualização",
        page_options,
        label_visibility="collapsed"
    )


# --- CORPO PRINCIPAL DO DASHBOARD ---
if not selected_months_mrr: 
    st.warning("Por favor, selecione um mês no filtro (MRR & Comercial).")
elif df.empty:
    st.error("Falha ao carregar os dados.")
else:
    # --- CÁLCULOS (SOMA) ---
    current_data = df[df['Mes'].isin(selected_months_mrr)]

    # Receita
    total_orcado = current_data['Receita Orcada'].sum()
    total_realizado = current_data['Receita Realizada'].sum()
    total_diferenca = current_data['Receita Diferenca'].sum()

    # Clientes
    total_essencial_orcado = current_data['Essencial Orcado'].sum()
    total_essencial_realizado = current_data['Essencial Realizado'].sum()
    total_essencial_diferenca = current_data['Essencial Diferenca'].sum()
    total_vender_orcado = current_data['Vender Orcado'].sum()
    total_vender_realizado = current_data['Vender Realizado'].sum()
    total_vender_diferenca = current_data['Vender Diferenca'].sum()
    total_avancado_orcado = current_data['Avancado Orcado'].sum()
    total_avancado_realizado = current_data['Avancado Realizado'].sum()
    total_avancado_diferenca = current_data['Avancado Diferenca'].sum()

    # [NOVO] Totais dos Planos (Soma dos 3 planos)
    total_planos_orcado = total_essencial_orcado + total_vender_orcado + total_avancado_orcado
    total_planos_realizado = total_essencial_realizado + total_vender_realizado + total_avancado_realizado
    total_planos_diferenca = total_essencial_diferenca + total_vender_diferenca + total_avancado_diferenca

    # Receitas Planos
    total_receita_essencial = current_data['Receita Essencial'].sum()
    total_receita_vender = current_data['Receita Vender'].sum()
    total_receita_avancado = current_data['Receita Avancado'].sum()
    total_receita_essencial_mensal = current_data['Receita Essencial Mensal'].sum() if 'Receita Essencial Mensal' in current_data else 0.0
    total_receita_vender_mensal = current_data['Receita Vender Mensal'].sum() if 'Receita Vender Mensal' in current_data else 0.0
    total_receita_avancado_mensal = current_data['Receita Avancado Mensal'].sum() if 'Receita Avancado Mensal' in current_data else 0.0

    # Churn
    total_churn_orcado = current_data['Churn Orcado'].sum() if 'Churn Orcado' in current_data else 0.0
    total_churn_realizado = current_data['Churn Realizado'].sum() if 'Churn Realizado' in current_data else 0.0
    total_churn_diferenca = current_data['Churn Diferenca'].sum() if 'Churn Diferenca' in current_data else 0.0

    # --- CÁLCULO DO PERÍODO ANTERIOR ---
    num_selected = len(selected_months_mrr)
    earliest_selected_month = min(selected_months_mrr, key=lambda m: all_months_list.index(m))
    min_index = all_months_list.index(earliest_selected_month)
    prev_start_index = max(0, min_index - num_selected)
    prev_end_index = min_index
    previous_months = all_months_list[prev_start_index:prev_end_index]
    
    # Inicializa variáveis prev com 0.0
    prev_orcado=0.0; prev_realizado=0.0; prev_diferenca=0.0
    prev_essencial_orcado=0.0; prev_essencial_realizado=0.0; prev_essencial_diferenca=0.0
    prev_vender_orcado=0.0; prev_vender_realizado=0.0; prev_vender_diferenca=0.0
    prev_avancado_orcado=0.0; prev_avancado_realizado=0.0; prev_avancado_diferenca=0.0
    prev_planos_orcado=0.0; prev_planos_realizado=0.0; prev_planos_diferenca=0.0 # [NOVO]

    if previous_months:
        prev_data = df[df['Mes'].isin(previous_months)]
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
        
        # [NOVO] Totais dos Planos (Anterior)
        prev_planos_orcado = prev_essencial_orcado + prev_vender_orcado + prev_avancado_orcado
        prev_planos_realizado = prev_essencial_realizado + prev_vender_realizado + prev_avancado_realizado
        prev_planos_diferenca = prev_essencial_diferenca + prev_vender_diferenca + prev_avancado_diferenca

    # --- DELTAS ---
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
    
    # [NOVO] Deltas para o Total dos Planos
    delta_planos_orcado_str = format_delta_clients(total_planos_orcado, prev_planos_orcado)
    delta_planos_realizado_str = format_delta_clients(total_planos_realizado, prev_planos_realizado)
    delta_planos_diferenca_str = format_delta_clients(total_planos_diferenca, prev_planos_diferenca)


    # Define labels e cores
    labels = ['Essencial', 'Controle', 'Avançado']
    colors = ['#41D9FF', '#E8C147', '#69FF4E']

    # --- EXIBIÇÃO CONDICIONAL ---

    if view_to_show == 'MRR':
        # --- TELA 1: MRR ---
        if selected_months_acumulado:
            df_acumulado = df[df['Mes'].isin(selected_months_acumulado)]
            acumulado_total_geral = df_acumulado['Receita Realizada'].sum()
            st.caption(f"Acumulado (Selecionado): {', '.join(sorted(selected_months_acumulado, key=get_sort_key))}")
        else:
            acumulado_total_geral = 0.0
            st.caption("Nenhum mês selecionado para o Acumulado Total.")

        _col_ac_esq, col_ac_centro, _col_ac_dir = st.columns([0.3, 0.4, 0.3])
        with col_ac_centro:
            st.metric("Receita Total (Geral)", format_currency(acumulado_total_geral), border=True)
        st.markdown("---")

        st.subheader("MRR")
        st.caption(f"Período selecionado: {', '.join(sorted(selected_months_mrr, key=get_sort_key))}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Orçado", format_currency(total_orcado), delta=delta_orcado_str, border=True)
        with col2:
            st.metric("Realizado", format_currency(total_realizado), delta=delta_realizado_str, border=True, delta_color="inverse")
        with col3:
            st.metric("Diferença", format_currency(total_diferenca), delta=delta_diferenca_str, border=True, delta_color="inverse")
        st.markdown("---")

    elif view_to_show == 'COMERCIAL':
        # --- TELA 2: COMERCIAL ---
        st.caption(f"Período selecionado: {', '.join(sorted(selected_months_mrr, key=get_sort_key))}")

        main_col_left, main_col_right = st.columns([0.6, 0.4])

        with main_col_left:
            # [ALTERAÇÃO] Mudado para 4 colunas para acomodar o "Total"
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Essencial</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_essencial_orcado), delta=delta_essencial_orcado_str)
                    st.metric("Realizado", format_clients(total_essencial_realizado), delta=delta_essencial_realizado_str)
                    st.metric("Diferença", format_clients(total_essencial_diferenca), delta=delta_essencial_diferenca_str, delta_color="normal")
            with col2:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Controle</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_vender_orcado), delta=delta_vender_orcado_str)
                    st.metric("Realizado", format_clients(total_vender_realizado), delta=delta_vender_realizado_str)
                    st.metric("Diferença", format_clients(total_vender_diferenca), delta=delta_vender_diferenca_str, delta_color="normal")
            with col3:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Avançado</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_avancado_orcado), delta=delta_avancado_orcado_str)
                    st.metric("Realizado", format_clients(total_avancado_realizado), delta=delta_avancado_realizado_str)
                    st.metric("Diferença", format_clients(total_avancado_diferenca), delta=delta_avancado_diferenca_str, delta_color="normal")
            
            # [NOVO] Cartão de Total
            with col4:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Total</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_planos_orcado), delta=delta_planos_orcado_str)
                    st.metric("Realizado", format_clients(total_planos_realizado), delta=delta_planos_realizado_str)
                    st.metric("Diferença", format_clients(total_planos_diferenca), delta=delta_planos_diferenca_str, delta_color="normal")

            st.markdown("---")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em; opacity: 0.8;'>Churn Orçado</p><h5 style='text-align: center;'>{format_clients(total_churn_orcado)}</h5>", unsafe_allow_html=True)
            with col_c2:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em; opacity: 0.8;'>Churn Realizado</p><h5 style='text-align: center;'>{format_clients(total_churn_realizado)}</h5>", unsafe_allow_html=True)
            with col_c3:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em; opacity: 0.8;'>Churn Diferença</p><h5 style='text-align: center;'>{format_clients(total_churn_diferenca)}</h5>", unsafe_allow_html=True)

        with main_col_right:
            # Gráficos de Pizza
            st.markdown("<h6 style='text-align: center;'>Distribuição Mensal</h6>", unsafe_allow_html=True)
            values_mensal = [total_receita_essencial_mensal, total_receita_vender_mensal, total_receita_avancado_mensal]
            custom_data_mensal = [format_currency(v) for v in values_mensal]

            if sum(values_mensal) > 0:
                fig_mensal = go.Figure(data=[go.Pie(
                    labels=labels, values=values_mensal, hole=.4, customdata=custom_data_mensal,
                    texttemplate='%{customdata}', textfont_size=9,
                    hovertemplate='<b>%{label}</b><br>Receita: %{customdata} (%{percent:.0f})<extra></extra>',
                    marker=dict(colors=colors, line=dict(color='#FFFFFF', width=1)), sort=False)])
                fig_mensal.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.01, font=dict(size=9)), margin=dict(t=5, b=5, l=60, r=5), height=180, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_mensal, use_container_width=True)
            else:
                st.info("Sem dados mensais.")

            st.markdown("<h6 style='text-align: center;'>Distribuição Geral</h6>", unsafe_allow_html=True)
            values_geral = [total_receita_essencial, total_receita_vender, total_receita_avancado]
            custom_data_geral = [format_currency(v) for v in values_geral]

            if sum(values_geral) > 0:
                fig_geral = go.Figure(data=[go.Pie(
                    labels=labels, values=values_geral, hole=.4, customdata=custom_data_geral,
                    texttemplate='%{customdata}', textfont_size=9,
                    hovertemplate='<b>%{label}</b><br>Receita: %{customdata} (%{percent:.0f})<extra></extra>',
                    marker=dict(colors=colors, line=dict(color='#FFFFFF', width=1)), sort=False)])
                fig_geral.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.01, font=dict(size=9)), margin=dict(t=5, b=5, l=60, r=5), height=180, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_geral, use_container_width=True)
            else:
                st.info("Sem dados gerais.")
    
    elif view_to_show == 'GRAFICO_RECEITA':
        # --- TELA 3: GRAFICO DE RECEITA (Separado) ---
        
        # Prepara dados
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes')
        chart_df_final = chart_df.set_index('Mes')

        with st.container(border=True):
            st.subheader("Meta MRR anual (agosto/25 a agosto/26)") 
            fig_receita = go.Figure()
            fig_receita.add_trace(go.Scatter(
                x=chart_df_final.index, y=chart_df_final['Receita Orcada'], mode='lines+markers+text', name='Receita Orçada', line=dict(color='#0000FF'),
                text=[format_currency(v) for v in chart_df_final['Receita Orcada']], textposition='top center', textfont=dict(color=st.get_option("theme.textColor"), size=10)
            ))
            fig_receita.add_trace(go.Scatter(
                x=chart_df_final.index, y=chart_df_final['Receita Realizada'], mode='lines+markers+text', name='Receita Realizada', line=dict(color='#00FF00'),
                text=[format_currency(v) for v in chart_df_final['Receita Realizada']], textposition='top center', textfont=dict(color=st.get_option("theme.textColor"), size=10)
            ))
            fig_receita.update_layout(height=320, xaxis=dict(tickangle=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig_receita, use_container_width=True)
    
    elif view_to_show == 'META_CLIENTES':
        # --- TELA 4: META CLIENTES (Separada) ---
        
        # Reutiliza preparação de dados
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes')
        chart_df_final = chart_df.set_index('Mes')

        with st.container(border=True):
            st.subheader("Meta Clientes Anual (agosto/25 a agosto/26)") 
            
            cols_to_plot_clientes = ['Total de Clientes Orcados', 'Total de Clientes Realizados']
            if all(col in chart_df_final.columns for col in cols_to_plot_clientes):
                fig_clientes = go.Figure()
                fig_clientes.add_trace(go.Scatter(
                    x=chart_df_final.index, y=chart_df_final['Total de Clientes Orcados'], mode='lines+markers+text', name='Clientes Orçados', line=dict(color='#0000FF'),
                    text=[format_clients(v) for v in chart_df_final['Total de Clientes Orcados']], textposition='top center', textfont=dict(color=st.get_option("theme.textColor"), size=10)
                ))
                fig_clientes.add_trace(go.Scatter(
                    x=chart_df_final.index, y=chart_df_final['Total de Clientes Realizados'], mode='lines+markers+text', name='Clientes Realizados', line=dict(color='#00FF00'),
                    text=[format_clients(v) for v in chart_df_final['Total de Clientes Realizados']], textposition='top center', textfont=dict(color=st.get_option("theme.textColor"), size=10)
                ))
                fig_clientes.update_layout(height=320, xaxis=dict(tickangle=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig_clientes, use_container_width=True)
            else:
                st.error("Colunas 'Total de Clientes Orcados' ou 'Total de Clientes Realizados' não encontradas.")

    elif view_to_show == 'GRAFICO_CHURN':
        # --- TELA 5: CHURN (Separada e Última) ---
        
        # Reutiliza preparação de dados
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes')
        chart_df_final = chart_df.set_index('Mes')

        with st.container(border=True):
            st.subheader("Churn")
            
            cols_to_plot_churn = ['Churn Orcado Mensal', 'Churn Realizado Mensal']
            if all(col in chart_df_final.columns for col in cols_to_plot_churn):
                fig_churn = go.Figure()
                fig_churn.add_trace(go.Scatter(
                    x=chart_df_final.index, y=chart_df_final['Churn Orcado Mensal'], mode='lines+markers+text', name='Churn Orçado Mensal', line=dict(color='#FF0000'),
                    text=[format_clients(v) for v in chart_df_final['Churn Orcado Mensal']], textposition='top center', textfont=dict(color=st.get_option("theme.textColor"), size=10)
                ))
                fig_churn.add_trace(go.Scatter(
                    x=chart_df_final.index, y=chart_df_final['Churn Realizado Mensal'], mode='lines+markers+text', name='Churn Realizado Mensal', line=dict(color='#800080'),
                    text=[format_clients(v) for v in chart_df_final['Churn Realizado Mensal']], textposition='top center', textfont=dict(color=st.get_option("theme.textColor"), size=10)
                ))
                fig_churn.update_layout(height=320, xaxis=dict(tickangle=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig_churn, use_container_width=True)
            else:
                st.error("Colunas 'Churn Orcado Mensal' ou 'Churn Realizado Mensal' não encontradas.")