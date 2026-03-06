import streamlit as st
import pandas as pd
from data_loader.loader import load_dashboard_data # Carregador GSheets
from data_loader.loader_leads import load_leads_data # Carregador CSV Leads
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # Rodízio automático
from datetime import datetime

# Configuração da página - Obrigatório ser a primeira instrução Streamlit
st.set_page_config(page_title="Dashboard MRR", layout="wide")

# --- INICIALIZAÇÃO DE VARIÁVEIS GLOBAIS ---
selected_months_mrr = []
selected_months_acumulado = []
all_months_list = []
df = pd.DataFrame()

# --- AJUSTE DE CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="st-"], [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            font-family: 'Inter', sans-serif !important;
        }
        [data-testid="stAppViewContainer"] > .main { padding-top: 0px !important; }
        .stApp { padding: 0.05rem !important; }
        h6 { font-size: 0.85rem !important; margin: 0 !important; font-weight: 700 !important; text-align: center; }
        [data-testid="stCaption"] { font-size: 0.6rem !important; padding: 0 !important; margin: 0 !important; }
        hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
        
        /* Estilo para os títulos das linhas de leads */
        .lead-row-title {
            font-size: 0.9rem;
            font-weight: bold;
            color: #41D9FF;
            margin-top: 5px;
            margin-bottom: 2px;
            border-left: 3px solid #41D9FF;
            padding-left: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE FORMATAÇÃO ---
def format_currency(value):
    try:
        val = float(value)
        return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return "R$ 0,00"

def format_percent(value):
    try: return f"{float(value):.1%}".replace('.', ',')
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

# --- CARREGA DADOS GSHEETS ---
try:
    df = load_dashboard_data()
except Exception as e:
    st.sidebar.error(f"Erro GSheets: {e}")

# --- PRÉ-CÁLCULOS GERAIS ---
if not df.empty:
    month_map = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}
    def get_sort_key(ms):
        try:
            m, y = ms.lower().split('/')
            return (int(y), month_map.get(m, 0))
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

# --- NAVEGAÇÃO ---
st.sidebar.header("Controlos")
auto_rotate = st.sidebar.checkbox("Rodízio automático (30s)", value=True)
page_options = ['Receita', 'LTV', 'Leads'] 

if auto_rotate:
    count = st_autorefresh(interval=30000, key="view_switcher")
    view_to_show = page_options[count % len(page_options)]
else:
    view_to_show = st.sidebar.radio("Página", page_options)

# --- FILTROS LATERAIS ---
if not df.empty:
    selected_months_acumulado = st.sidebar.multiselect("Meses (Acumulado)", options=all_months_list, default=past_and_current_months)
    selected_months_mrr = st.sidebar.multiselect("Meses (Referência)", options=all_months_list, default=default_month_selection)
else:
    st.sidebar.warning("Aguardando carregamento da planilha...")

# --- LÓGICA DE EXIBIÇÃO ---
if df.empty:
    st.error("Falha crítica: O DataFrame está vazio. Verifique a planilha.")
elif not selected_months_mrr and view_to_show != 'Leads':
    st.warning("Selecione os meses na barra lateral para visualizar os dados.")
else:
    if view_to_show == 'Receita':
        # --- TELA 1: RECEITA ---
        st.subheader("Receita x Meta")
        df_ac_vigente = df[df['Mes'].isin(selected_months_acumulado)]
        acum_vigente = df_ac_vigente['Receita Realizada'].sum()
        
        META_VALOR = 1400000.0
        # Range fixo de Ago/25 a Ago/26
        start_p, end_p = '08/2025', '08/2026'
        range_total_periodo = [m for m in all_months_list if get_sort_key(start_p) <= get_sort_key(m) <= get_sort_key(end_p)]
        total_periodo = df[df['Mes'].isin(range_total_periodo)]['Receita Realizada'].sum()
        
        progresso = total_periodo / META_VALOR if META_VALOR else 0

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Receita Acumulada (Até Vigente)", format_currency(acum_vigente), border=True)
        with c2: st.metric("Receita Acumulada Total (Ago/25 - Ago/26)", format_currency(total_periodo), border=True)
        with c3:
            with st.container(border=True):
                # Título e legenda conforme solicitado
                st.markdown("<p style='text-align: center; font-size: 0.85rem; margin: 0;'>Progresso da Meta</p>", unsafe_allow_html=True)
                st.progress(min(progresso, 1.0))
                st.caption(f"{progresso:.1%} de R$ 1.400.000")

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
            with r1: st.metric("Resultado Acumulado (Vigente)", format_currency(res_vigente), border=True)
            with r2: st.metric(label="Resultado / Receita % (Acumulado)", value=format_percent(perc_res), border=True)
            with r3: st.metric(f"Resultado Acumulado ({start_p}-{end_p})", format_currency(res_total), border=True)

    elif view_to_show == 'LTV':
        # --- TELA 2: LTV ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        range_ltv = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key(current_month_str)]
        df_ltv = df[df['Mes'].isin(range_ltv)].copy()
        
        st.subheader("LTV por Plano (Média Ago/25 - Vigente)")
        l1, l2, l3 = st.columns(3)
        # Cálculo da média conforme solicitado
        val_ess = df_ltv['LTV Essencial'].apply(clean_sheets_numeric).mean() if 'LTV Essencial' in df_ltv.columns else 0
        val_ven = df_ltv['LTV Vender'].apply(clean_sheets_numeric).mean() if 'LTV Vender' in df_ltv.columns else 0
        val_ava = df_ltv['LTV Avancado'].apply(clean_sheets_numeric).mean() if 'LTV Avancado' in df_ltv.columns else 0
        
        with l1: st.metric("LTV Essencial", format_currency(val_ess), border=True)
        with l2: st.metric("LTV Vender", format_currency(val_ven), border=True)
        with l3: st.metric("LTV Avançado", format_currency(val_ava), border=True)

        st.markdown("---")
        with st.container(border=True):
            st.subheader("Ticket Médio")
            if 'TM Geral' in chart_df.columns:
                df_tm_chart = chart_df[chart_df.index.isin(range_ltv)]
                fig_tm = go.Figure(go.Bar(x=df_tm_chart.index, y=df_tm_chart['TM Geral'], marker_color='#41D9FF', text=[format_currency(v) for v in df_tm_chart['TM Geral']], textposition='auto'))
                fig_tm.update_layout(height=220, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(t=10,b=10))
                st.plotly_chart(fig_tm, use_container_width=True)
            
        with st.container(border=True):
            st.subheader("Clientes (Ago/2025 - Ago/2026)")
            fig_cli = go.Figure(go.Scatter(x=chart_df.index, y=chart_df['Total de Clientes Realizados'], mode='lines+markers+text', name='Realizado', line=dict(color='green', width=3), text=chart_df['Total de Clientes Realizados'], textposition='top center'))
            fig_cli.update_layout(height=220, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(t=10,b=10))
            st.plotly_chart(fig_cli, use_container_width=True)

    elif view_to_show == 'Leads':
        # --- TELA 3: LEADS ---
        st.markdown("<h6 style='text-align: left; margin-bottom: 10px;'>Performance de Funil (CRM)</h6>", unsafe_allow_html=True)
        d_leads = load_leads_data() # Lê o CSV local
        
        p_keys = [("dois_meses_atras", "2 Meses Atrás"), ("mes_passado", "Mês Passado"), ("este_mes", "Este Mês")]
        c_keys = [
            ("Leads Gerados", "gerados"),
            ("Leads Qualificados", "qualificados"),
            ("Reuniões de Diagnóstico", "diagnostico"),
            ("Reuniões de Proposta", "proposta"),
            ("Vendas", "vendas")
        ]
        
        # Estrutura de 5 linhas com 3 colunas cada, espaçamento reduzido
        for label_cat, key_cat in c_keys:
            st.markdown(f"<div class='lead-row-title'>{label_cat}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (p_key, p_label) in enumerate(p_keys):
                val = d_leads.get(p_key, {}).get(key_cat, 0)
                cols[i].metric(label=p_label, value=int(val), border=True)
            # Reduzido o espaçamento para melhorar a leitura
            st.markdown("<div style='margin-bottom: -15px;'></div>", unsafe_allow_html=True)
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.caption(f"Dados sincronizados via CSV em: {d_leads.get('ultima_atualizacao', '---')}")