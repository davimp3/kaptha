import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # Rodízio automático
from datetime import datetime
import os

# --- IMPORTAÇÃO SEGURA DOS LOADERS ---
try:
    from data_loader.loader import load_dashboard_data # Carregador GSheets (MRR/LTV)
    from data_loader.loader_leads import load_leads_data # Carregador CSV (Leads)
except ImportError as e:
    st.error(f"Erro de Estrutura: Não foi possível encontrar os ficheiros na pasta 'data_loader'. Detalhe: {e}")
    st.stop()

# Configuração da página - Deve ser sempre a primeira instrução Streamlit
st.set_page_config(page_title="Dashboard MRR", layout="wide")

# --- AJUSTE DE CSS PARA ALTA DENSIDADE E LEITURA ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="st-"], [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            font-family: 'Inter', sans-serif !important;
        }
        [data-testid="stAppViewContainer"] > .main { padding-top: 0px !important; }
        .stApp { padding: 0.05rem !important; }
        
        /* Títulos e legendas reduzidos para economizar espaço */
        h6 { font-size: 0.85rem !important; margin: 0 !important; font-weight: 700 !important; text-align: center; }
        [data-testid="stCaption"] { font-size: 0.6rem !important; padding: 0 !important; margin: 0 !important; }
        hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
        
        /* Estilo destacado para os estágios do funil de leads */
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
    """Limpeza para garantir que PROCVs ou textos da planilha não quebrem o app."""
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
            # Tenta converter o mês para número, seja ele '01' ou 'janeiro'
            m_val = int(m) if m.isdigit() else month_map.get(m, 0)
            return (int(y), m_val)
        except: return (0, 0)

    all_months_list = sorted(df['Mes'].unique(), key=get_sort_key)
    now = datetime.now()
    # current_month_str representa o mês/ano vigente para limites de filtro
    current_month_str = now.strftime('%m/%Y') 

    # Sincronização de seleção padrão
    if current_month_str in all_months_list:
        idx_curr = all_months_list.index(current_month_str)
        default_month_selection = [current_month_str]
        past_and_current_months = all_months_list[:idx_curr + 1]
    else:
        default_month_selection = [all_months_list[-1]] if all_months_list else []
        past_and_current_months = all_months_list

# --- NAVEGAÇÃO E RODÍZIO ---
st.sidebar.header("Controlos")
auto_rotate = st.sidebar.checkbox("Rodízio automático (30s)", value=True)
page_options = ['Receita', 'LTV', 'Clientes', 'Leads'] 

if auto_rotate:
    count = st_autorefresh(interval=30000, key="view_switcher")
    view_to_show = page_options[count % len(page_options)]
else:
    view_to_show = st.sidebar.radio("Página", page_options)

# --- FILTROS ---
if not df.empty:
    selected_months_acumulado = st.sidebar.multiselect("Meses (Acumulado)", options=all_months_list, default=past_and_current_months)
    selected_months_mrr = st.sidebar.multiselect("Meses (Referência)", options=all_months_list, default=default_month_selection)
else:
    st.sidebar.warning("Aguardando dados da planilha...")

# --- LÓGICA DE EXIBIÇÃO POR PÁGINA ---
if df.empty:
    st.error("Falha ao carregar os dados. Verifique a ligação com a planilha.")
else:
    if view_to_show == 'Receita':
        # --- TELA 1: RECEITA ---
        st.subheader("Receita x Meta")
        df_ac_vigente = df[df['Mes'].isin(selected_months_acumulado)]
        acum_vigente = df_ac_vigente['Receita Realizada'].sum()
        
        META_VALOR = 1400000.0
        # Range fixo: Agosto/2025 a Agosto/2026
        start_p, end_p = '08/2025', '08/2026'
        range_total_periodo = [m for m in all_months_list if get_sort_key(start_p) <= get_sort_key(m) <= get_sort_key(end_p)]
        total_periodo = df[df['Mes'].isin(range_total_periodo)]['Receita Realizada'].sum()
        progresso = total_periodo / META_VALOR if META_VALOR else 0

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Receita Acumulada (Até Vigente)", format_currency(acum_vigente), border=True)
        with c2: st.metric("Receita Acumulada Total (Ago/25 - Ago/26)", format_currency(total_periodo), border=True)
        with c3:
            with st.container(border=True):
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
        
        # Range Vigente: Ago/25 até Hoje
        range_vigente = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key(current_month_str)]
        df_ltv_vig = df[df['Mes'].isin(range_vigente)].copy()
        
        # Range Total: Ago/25 a Ago/26
        range_total = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key('08/2026')]
        df_ltv_tot = df[df['Mes'].isin(range_total)].copy()

        st.subheader("LTV por Plano (Média Ago/25 - Vigente)")
        l1, l2, l3 = st.columns(3)
        v_ess = df_ltv_vig['LTV Essencial'].apply(clean_sheets_numeric).mean() if 'LTV Essencial' in df_ltv_vig.columns else 0
        v_ven = df_ltv_vig['LTV Vender'].apply(clean_sheets_numeric).mean() if 'LTV Vender' in df_ltv_vig.columns else 0
        v_ava = df_ltv_vig['LTV Avancado'].apply(clean_sheets_numeric).mean() if 'LTV Avancado' in df_ltv_vig.columns else 0
        
        with l1: st.metric("LTV Essencial", format_currency(v_ess), border=True)
        with l2: st.metric("LTV Vender", format_currency(v_ven), border=True)
        with l3: st.metric("LTV Avançado", format_currency(v_ava), border=True)

        st.markdown("---")
        st.subheader("LTV por Plano (Média Total Ago/25 - Ago/26)")
        lt1, lt2, lt3 = st.columns(3)
        v_ess_t = df_ltv_tot['LTV Essencial Total'].apply(clean_sheets_numeric).mean() if 'LTV Essencial Total' in df_ltv_tot.columns else 0
        v_ven_t = df_ltv_tot['LTV Vender Total'].apply(clean_sheets_numeric).mean() if 'LTV Vender Total' in df_ltv_tot.columns else 0
        v_ava_t = df_ltv_tot['LTV Avancado Total'].apply(clean_sheets_numeric).mean() if 'LTV Avancado Total' in df_ltv_tot.columns else 0

        with lt1: st.metric("LTV Essencial Total", format_currency(v_ess_t), border=True)
        with lt2: st.metric("LTV Vender Total", format_currency(v_ven_t), border=True)
        with lt3: st.metric("LTV Avançado Total", format_currency(v_ava_t), border=True)

        st.markdown("---")
        with st.container(border=True):
            st.subheader("Ticket Médio Geral")
            if 'TM Geral' in chart_df.columns:
                df_tm_chart = chart_df[chart_df.index.isin(range_vigente)]
                fig_tm = go.Figure(go.Bar(x=df_tm_chart.index, y=df_tm_chart['TM Geral'], marker_color='#41D9FF', text=[format_currency(v) for v in df_tm_chart['TM Geral']], textposition='auto'))
                fig_tm.update_layout(height=220, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(t=10,b=10))
                st.plotly_chart(fig_tm, use_container_width=True)

    elif view_to_show == 'Clientes':
        # --- TELA 3: CLIENTES ---
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes').set_index('Mes')
        
        # Range solicitado: Agosto/25 até o mês vigente (período atual)
        range_cli = [m for m in all_months_list if get_sort_key('08/2025') <= get_sort_key(m) <= get_sort_key(current_month_str)]
        df_cli_chart = chart_df[chart_df.index.isin(range_cli)]
        
        st.subheader("Evolução de Clientes")
        with st.container(border=True):
            st.markdown(f"<h6>Base de Clientes (Ago/2025 - {current_month_str})</h6>", unsafe_allow_html=True)
            fig_cli = go.Figure(go.Scatter(
                x=df_cli_chart.index, 
                y=df_cli_chart['Total de Clientes Realizados'], 
                mode='lines+markers+text', 
                name='Realizado', 
                line=dict(color='green', width=3), 
                text=df_cli_chart['Total de Clientes Realizados'], 
                textposition='top center'
            ))
            fig_cli.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(t=20,b=10))
            st.plotly_chart(fig_cli, use_container_width=True)

    elif view_to_show == 'Leads':
        # --- TELA 4: LEADS (VOLTANDO AO FORMATO ANTERIOR DE METRICS) ---
        st.markdown("<h6 style='text-align: left; margin-bottom: 10px;'>Performance de Funil (CRM)</h6>", unsafe_allow_html=True)
        d_leads = load_leads_data() 
        
        p_keys = [("dois_meses_atras", "2 Meses Atrás"), ("mes_passado", "Mês Passado"), ("este_mes", "Este Mês")]
        c_keys = [
            ("Leads Gerados", "gerados"),
            ("Leads Qualificados", "qualificados"),
            ("Reuniões de Diagnóstico", "diagnostico"),
            ("Reuniões de Proposta", "proposta"),
            ("Vendas", "vendas")
        ]
        
        # Estrutura de 5 linhas com 3 colunas cada, conforme solicitado anteriormente
        for label_cat, key_cat in c_keys:
            st.markdown(f"<div class='lead-row-title'>{label_cat}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (p_key, p_label) in enumerate(p_keys):
                val = d_leads.get(p_key, {}).get(key_cat, 0)
                cols[i].metric(label=p_label, value=int(val), border=True)
            # Margem negativa para compactar a visualização e melhorar leitura
            st.markdown("<div style='margin-bottom: -15px;'></div>", unsafe_allow_html=True)
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.caption(f"Dados sincronizados via CSV em: {d_leads.get('ultima_atualizacao', '---')}")