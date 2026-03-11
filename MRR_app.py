import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Importação necessária para eixos duplos
from streamlit_autorefresh import st_autorefresh # Rodízio automático
from datetime import datetime
import os

# --- IMPORTAÇÃO SEGURA DOS LOADERS ---
try:
    from data_loader.loader import load_dashboard_data # Carregador GSheets (MRR/LTV)
    # [COMENTADO COM #]
    # from data_loader.loader_leads import load_leads_data # Carregador CSV (Leads)
except ImportError as e:
    st.error(f"Erro de Estrutura: Não foi possível encontrar os ficheiros na pasta 'data_loader'. Detalhe: {e}")
    st.stop()

# Configuração da página - Restaurado para estado expandido
st.set_page_config(page_title="Dashboard MRR", layout="wide", initial_sidebar_state="expanded")

# --- AJUSTE DE CSS PARA VISUAL PREMIUM E ACESSO À SIDEBAR ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Fonte Global e Fundo */
        html, body, [class*="st-"], [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* Mantemos apenas o footer escondido para um look mais clean */
        footer {
            visibility: hidden !important;
            height: 0 !important;
        }

        /* Redução de Padding do Container Principal */
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0rem !important;
            padding-bottom: 1rem !important;
        }

        /* Estilização dos Blocos de Métrica (Cards) */
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            border-color: #41D9FF;
            transform: translateY(-2px);
        }

        /* Títulos de Seção */
        h2, h3 {
            font-weight: 700 !important;
            color: #FFFFFF !important;
            letter-spacing: -0.02em !important;
        }
        
        h6 { 
            font-size: 0.9rem !important; 
            margin-bottom: 8px !important; 
            font-weight: 600 !important; 
            text-align: center;
            color: #41D9FF;
        }

        /* BADGE DE META (A FLAG VERDE) */
        .goal-badge-container {
            text-align: center;
            margin-top: 10px;
        }
        .goal-badge {
            background-color: #69FF4E;
            color: #000000;
            padding: 4px 16px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 1.1rem;
            display: inline-block;
            box-shadow: 0 0 15px rgba(105, 255, 78, 0.4);
            margin-bottom: 4px;
        }
        .goal-subtext {
            font-size: 0.7rem;
            color: rgba(255, 255, 255, 0.6);
            display: block;
        }

        /* Ajustes de Legendas e Captions padrão */
        [data-testid="stCaption"] {
            font-size: 0.75rem !important;
            color: rgba(255, 255, 255, 0.6) !important;
            text-align: center;
        }

        /* Estilização da Barra de Progresso */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #41D9FF, #69FF4E) !important;
        }

        /* HR Estilizado */
        hr {
            border: 0;
            height: 1px;
            background-image: linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0));
            margin-top: 1.5rem !important;
            margin-bottom: 1.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE FORMATAÇÃO ---
def format_currency(value):
    try:
        val = float(value)
        if pd.isna(val): return "R$ 0,00"
        return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return "R$ 0,00"

def format_percent(value):
    try:
        val = float(value)
        if pd.isna(val): return "0,0%"
        return f"{val:.1%}".replace('.', ',')
    except: return "0,0%"

def clean_sheets_numeric(val):
    if pd.isna(val) or val == "" or str(val).strip() == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        s = str(val).replace('R$', '').replace(' ', '').strip()
        if '.' in s and ',' in s: s = s.replace('.', '').replace(',', '.')
        elif ',' in s: s = s.replace(',', '.')
        return float(s)
    except: return 0.0

# --- CARREGA DADOS ---
df = load_dashboard_data()

# --- PRÉ-CÁLCULOS GERAIS ---
all_months_list = []
current_month_str = ""
if not df.empty:
    month_map = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}
    def get_sort_key(ms):
        try:
            m, y = ms.lower().split('/')
            m_val = int(m) if m.isdigit() else month_map.get(m, 0)
            return (int(y), m_val)
        except: return (0, 0)

    all_months_list = sorted(df['Mes'].unique(), key=get_sort_key)
    now = datetime.now()
    current_month_str = now.strftime('%m/%Y') 

    if current_month_str in all_months_list:
        idx_curr = all_months_list.index(current_month_str)
        default_month_selection = [current_month_str]
        past_and_current_months = all_months_list[:idx_curr + 1]
    else:
        default_month_selection = [all_months_list[-1]] if all_months_list else []
        past_and_current_months = all_months_list

# --- NAVEGAÇÃO E RODÍZIO ---
st.sidebar.header("Controlos de Visualização")
auto_rotate = st.sidebar.checkbox("Rodízio automático (30s)", value=True)
page_options = ['Receita', 'LTV', 'Ticket Médio', 'Clientes'] 

if auto_rotate:
    count = st_autorefresh(interval=30000, key="view_switcher")
    view_to_show = page_options[count % len(page_options)]
else:
    view_to_show = st.sidebar.radio("Navegar para:", page_options)

# --- FILTROS ---
st.sidebar.markdown("---")
if not df.empty:
    if auto_rotate:
        # Se estiver em rodízio, usa os valores padrão automaticamente
        selected_months_acumulado = past_and_current_months
        selected_months_mrr = default_month_selection
        st.sidebar.info("Modo Automático Ativado")
    else:
        # Se o rodízio estiver desligado, permite controlo manual
        selected_months_acumulado = st.sidebar.multiselect("Filtrar Acumulado (Cards)", options=all_months_list, default=past_and_current_months)
        selected_months_mrr = st.sidebar.multiselect("Filtrar Referência", options=all_months_list, default=default_month_selection)
else:
    st.sidebar.warning("Carregando base de dados...")

# --- LÓGICA DE EXIBIÇÃO POR PÁGINA ---
if df.empty:
    st.error("Não foi possível carregar os dados. Verifique a planilha 'DADOS STREAMLIT'.")
else:
    if view_to_show == 'Receita':
        # --- TELA 1: RECEITA ---
        st.subheader("Receita x Meta")
        df_ac_vigente = df[df['Mes'].isin(selected_months_acumulado)]
        acum_vigente = df_ac_vigente['Receita Realizada'].sum()
        
        META_VALOR = 1400000.0
        start_p, end_p = '08/2025', '08/2026'
        range_total_periodo = [m for m in all_months_list if get_sort_key(start_p) <= get_sort_key(m) <= get_sort_key(end_p)]
        total_periodo = df[df['Mes'].isin(range_total_periodo)]['Receita Realizada'].sum()
        progresso = total_periodo / META_VALOR if META_VALOR else 0

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Receita Acumulada", format_currency(acum_vigente))
        with c2: st.metric("Receita Total (Ago/25 - Ago/26)", format_currency(total_periodo))
        with c3:
            with st.container(border=True):
                st.markdown("<h6>Progresso da Meta</h6>", unsafe_allow_html=True)
                st.progress(min(progresso, 1.0))
                # Implementação da "Flag" Verde para o percentual
                st.markdown(f"""
                    <div class="goal-badge-container">
                        <span class="goal-badge">{progresso:.1%}</span>
                        <span class="goal-subtext">de R$ 1.400.000</span>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Resultado x Faturamento")
        res_col = next((c for c in ['Resultado Acumulado', 'Resultado AC', 'AC'] if c in df.columns), None)
        if res_col:
            df_safe = df.copy()
            df_safe[res_col] = df_safe[res_col].apply(clean_sheets_numeric)
            res_vigente = df_safe[df_safe['Mes'].isin(selected_months_acumulado)][res_col].sum()
            res_total = df_safe[df_safe['Mes'].isin(range_total_periodo)][res_col].sum()
            perc_res = res_vigente / acum_vigente if acum_vigente else 0
            
            r1, r2, r3 = st.columns(3)
            with r1: st.metric("Resultado Acumulado", format_currency(res_vigente))
            with r2: st.metric(label="Resultado / Receita %", value=format_percent(perc_res))
            with r3: st.metric(f"Resultado Total ({start_p}-{end_p})", format_currency(res_total))

    elif view_to_show == 'LTV':
        # --- TELA 2: LTV ---
        range_vigente_ltv = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key(current_month_str)]
        df_ltv_vig = df[df['Mes'].isin(range_vigente_ltv)].copy()
        range_total_ltv = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key('08/2026')]
        df_ltv_tot = df[df['Mes'].isin(range_total_ltv)].copy()

        st.subheader("LTV por Plano (Média Vigente)")
        l1, l2, l3 = st.columns(3)
        v_ess = df_ltv_vig['LTV Essencial'].apply(clean_sheets_numeric).mean() if 'LTV Essencial' in df_ltv_vig.columns else 0
        v_ven = df_ltv_vig['LTV Vender'].apply(clean_sheets_numeric).mean() if 'LTV Vender' in df_ltv_vig.columns else 0
        v_ava = df_ltv_vig['LTV Avancado'].apply(clean_sheets_numeric).mean() if 'LTV Avancado' in df_ltv_vig.columns else 0
        
        with l1: st.metric("LTV Essencial", format_currency(v_ess))
        with l2: st.metric("LTV Vender", format_currency(v_ven))
        with l3: st.metric("LTV Avançado", format_currency(v_ava))

        st.markdown("---")
        st.subheader("LTV por Plano (Média Anual)")
        lt1, lt2, lt3 = st.columns(3)
        v_ess_t = df_ltv_tot['LTV Essencial Total'].apply(clean_sheets_numeric).mean() if 'LTV Essencial Total' in df_ltv_tot.columns else 0
        v_ven_t = df_ltv_tot['LTV Vender Total'].apply(clean_sheets_numeric).mean() if 'LTV Vender Total' in df_ltv_tot.columns else 0
        v_ava_t = df_ltv_tot['LTV Avancado Total'].apply(clean_sheets_numeric).mean() if 'LTV Avancado Total' in df_ltv_tot.columns else 0

        with lt1: st.metric("Essencial Total", format_currency(v_ess_t))
        with lt2: st.metric("Vender Total", format_currency(v_ven_t))
        with lt3: st.metric("Avançado Total", format_currency(v_ava_t))

    elif view_to_show == 'Ticket Médio':
        # --- TELA 3: TICKET MÉDIO ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        range_tm = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key(current_month_str)]
        
        st.subheader("🎟️ Ticket Médio Geral")
        with st.container():
            if 'TM Geral' in chart_df.columns:
                df_tm_chart = chart_df[chart_df.index.isin(range_tm)]
                fig_tm = go.Figure(go.Bar(
                    x=df_tm_chart.index, 
                    y=df_tm_chart['TM Geral'], 
                    marker=dict(color='#41D9FF', line=dict(width=0)), 
                    text=[format_currency(v) for v in df_tm_chart['TM Geral']], 
                    textposition='auto'
                ))
                fig_tm.update_layout(
                    height=450, 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color="white", size=10),
                    margin=dict(t=30, b=10, l=10, r=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig_tm, use_container_width=True)

    elif view_to_show == 'Clientes':
        # --- TELA 4: CLIENTES (EVOLUÇÃO CRUZADA COM FATURAMENTO) ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        
        # Range solicitado: Ago/25 até data atual (vigente)
        range_cli = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key(current_month_str)]
        df_cli_chart = chart_df[chart_df.index.isin(range_cli)]
        
        st.subheader("Evolução: Clientes x Faturamento")
        with st.container():
            fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

            fig_combined.add_trace(
                go.Scatter(
                    x=df_cli_chart.index, 
                    y=df_cli_chart['Receita Realizada'], 
                    name="Faturamento (R$)",
                    mode='lines+markers+text', 
                    line=dict(color='#41D9FF', width=4, shape='spline'),
                    marker=dict(size=8),
                    text=[f"R${v/1000:,.0f}k" for v in df_cli_chart['Receita Realizada']],
                    textposition='top left'
                ),
                secondary_y=False,
            )

            fig_combined.add_trace(
                go.Scatter(
                    x=df_cli_chart.index, 
                    y=df_cli_chart['Total de Clientes Realizados'], 
                    name="Clientes (Un)",
                    mode='lines+markers+text', 
                    line=dict(color='#69FF4E', width=4, shape='spline'),
                    marker=dict(size=8),
                    text=df_cli_chart['Total de Clientes Realizados'], 
                    textposition='bottom right'
                ),
                secondary_y=True,
            )

            fig_combined.update_layout(
                height=500, 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font=dict(color="white", size=10),
                margin=dict(t=30, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            fig_combined.update_yaxes(title_text="Faturamento (R$)", secondary_y=False, gridcolor='rgba(255,255,255,0.05)')
            fig_combined.update_yaxes(title_text="Clientes (Un)", secondary_y=True, showgrid=False)

            st.plotly_chart(fig_combined, use_container_width=True)

    # --- PÁGINA DE LEADS (COMENTADA COM #) ---
    # elif view_to_show == 'Leads':
    #     ...