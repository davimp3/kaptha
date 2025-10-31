import streamlit as st
import pandas as pd
from data_loader.loader import load_dashboard_data # Importa do loader correto (do Canvas)
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # Para o rodízio
from datetime import datetime # [NOVO] Para encontrar o mês atual
import locale # [NOVO] Para formatar o nome do mês em português

st.set_page_config(page_title="Dashboard MMR", layout="wide")

# --- AJUSTE DE CSS PARA REMOVER PADDING SUPERIOR ---
st.markdown("""
    <style>
        /* [NOVA ALTERAÇÃO] Define a fonte global para Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="st-"], [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* [ALTERAÇÃO] Remove TODO padding, margin e border do container principal para o topo */
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }
        [data-testid="stAppViewContainer"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }

        /* [REMOVIDO] O bloco 'header' que escondia a sidebar foi removido. */

        /* [ALTERAÇÃO] Ajusta padding geral da página para quase zero */
        .stApp {
            padding: 0.05rem !important;
        }
        /* [ALTERAÇÃO] Reduz o gap (espaço) entre as colunas */
        [data-testid="stHorizontalBlock"] {
            gap: 0.1rem !important;
        }
        /* [ALTERAÇÃO] Reduz o padding dos containers de borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.1rem !important;
        }
        /* Reduz o padding dos containers de métrica */
        [data-testid="stMetric"] {
            padding: 0px !important;
            margin: 0px !important;
        }
        /* [ALTERAÇÃO] Reduz o tamanho das fontes de título h6 e h5 */
        h6 { font-size: 0.8rem !important; margin: 0 !important; }
        h5 { font-size: 1.0rem !important; margin: 0 !important; }
        /* [ALTERAÇÃO] Reduz o tamanho das legendas */
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

# --- PRÉ-CÁLCULOS GERAIS (MOVECIDO PARA CIMA) ---
acumulado_total_geral = 0.0
total_orcado_geral = 0.0
all_months_list = []
default_month_selection = [] # [NOVO] Lista para o default do filtro

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
    
    # --- [NOVO] Lógica para Mês Atual e Acumulado ---
    try:
        # Define o local para português do Brasil para pegar o nome do mês
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252') # Windows
        except:
            pass # Usa o padrão do sistema se pt_BR falhar

    now = datetime.now()
    current_month_str = f"{now.strftime('%B').lower()}/{now.year}" # ex: "outubro/2025"
    
    # Encontra o índice do mês atual na lista ordenada
    current_month_index = -1
    if current_month_str in all_months_list:
        current_month_index = all_months_list.index(current_month_str)
        default_month_selection = [current_month_str] # Default é o mês atual
    else:
        # Se o mês atual exato não está nos dados, seleciona o último disponível
        if all_months_list:
            current_month_index = len(all_months_list) - 1
            default_month_selection = [all_months_list[-1]]
            
    # [ALTERAÇÃO] Filtra o DataFrame para calcular o Acumulado Total
    # Pega todos os meses do início até o índice do mês atual (inclusive)
    past_and_current_months = all_months_list[:current_month_index + 1]
    df_past_current = df[df['Mes'].isin(past_and_current_months)]
    
    # Calcula o Acumulado Total apenas com meses passados e atuais
    acumulado_total_geral = df_past_current['Receita Realizada'].sum()
    total_orcado_geral = df_past_current['Receita Orcada'].sum()


# --- SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros do Dashboard")

auto_rotate_views = st.sidebar.checkbox("Rodízio automático de telas (30s)", value=True)

if not df.empty:
    selected_months = st.sidebar.multiselect(
        "Selecione o(s) Mês(es)",
        options=all_months_list,
        default=default_month_selection # [ALTERAÇÃO] Usa o novo default (mês atual)
    )
else:
    selected_months = []
    st.sidebar.error("Não foi possível carregar os dados. Verifique a aba 'DADOS STREAMLIT'.")


# --- LÓGICA DE RODÍZIO DE TELA ---
view_to_show = 'MRR'
# [ALTERAÇÃO] Juntando os gráficos, voltando para 3 telas
page_options = ['MRR', 'COMERCIAL', 'GRAFICOS_EVOLUCAO'] 

if auto_rotate_views:
    count = st_autorefresh(interval=30000, key="view_switcher")
    page_index = count % 3 # [ALTERAÇÃO] Alterna entre 0, 1, e 2
    view_to_show = page_options[page_index]

else:
    # Se não estiver rotacionando, permite seleção manual
    view_to_show = st.sidebar.radio(
        "Selecionar visualização",
        page_options,
        label_visibility="collapsed"
    )


# --- CORPO PRINCIPAL DO DASHBOARD ---
if not selected_months:
    st.warning("Por favor, selecione um mês na barra lateral.")
elif df.empty:
    st.error("Falha ao carregar os dados.")
else:
    # --- 1. CÁLCULO DO PERÍODO ATUAL (SOMA) ---
    # [ALTERAÇÃO] Esta lógica agora funciona como esperado:
    # Por padrão, 'selected_months' contém apenas o mês atual.
    # Se o usuário selecionar mais, 'current_data' irá somar os meses selecionados.
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

    # Receita por Plano (GERAL - para o gráfico da direita)
    total_receita_essencial = current_data['Receita Essencial'].sum()
    total_receita_vender = current_data['Receita Vender'].sum()
    total_receita_avancado = current_data['Receita Avancado'].sum()

    # Receita por Plano (MENSAL - para o gráfico da esquerda)
    total_receita_essencial_mensal = current_data['Receita Essencial Mensal'].sum() if 'Receita Essencial Mensal' in current_data else 0.0
    total_receita_vender_mensal = current_data['Receita Vender Mensal'].sum() if 'Receita Vender Mensal' in current_data else 0.0
    total_receita_avancado_mensal = current_data['Receita Avancado Mensal'].sum() if 'Receita Avancado Mensal' in current_data else 0.0

    # Churn
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

    prev_orcado, prev_realizado, prev_diferenca = 0.0, 0.0, 0.0
    prev_essencial_orcado, prev_essencial_realizado, prev_essencial_diferenca = 0.0, 0.0, 0.0
    prev_vender_orcado, prev_vender_realizado, prev_vender_diferenca = 0.0, 0.0, 0.0
    prev_avancado_orcado, prev_avancado_realizado, prev_avancado_diferenca = 0.0, 0.0, 0.0

    if previous_months:
        previous_data = df[df['Mes'].isin(previous_months)]
        prev_orcado = previous_data['Receita Orcada'].sum()
        prev_realizado = previous_data['Receita Realizada'].sum()
        prev_diferenca = previous_data['Receita Diferenca'].sum()
        prev_essencial_orcado = previous_data['Essencial Orcado'].sum()
        prev_essencial_realizado = previous_data['Essencial Realizado'].sum()
        prev_essencial_diferenca = previous_data['Essencial Diferenca'].sum()
        prev_vender_orcado = previous_data['Vender Orcado'].sum()
        prev_vender_realizado = previous_data['Vender Realizado'].sum()
        prev_vender_diferenca = previous_data['Vender Diferenca'].sum()
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

    # Define labels e cores ANTES do loop
    labels = ['Essencial', 'Controle', 'Avançado']
    colors = ['#41D9FF', '#E8C147', '#69FF4E']

    # --- EXIBIÇÃO CONDICIONAL ---

    if view_to_show == 'MRR':
        # --- 4. EXIBIÇÃO - SEÇÃO 1: ACUMULADO TOTAL ---
        # [ALTERAÇÃO] O valor 'acumulado_total_geral' agora é pré-calculado
        st.caption(f"Acumulado até: {past_and_current_months[-1] if past_and_current_months else 'N/A'}")


        _col_ac_esq, col_ac_centro, _col_ac_dir = st.columns([0.3, 0.4, 0.3])
        with col_ac_centro:
            st.metric(
                "Receita Total (Geral)",
                format_currency(acumulado_total_geral),
                border=True
            )
        st.markdown("---")

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
                border=True,
                delta_color="normal" # [CORREÇÃO] Garantindo a cor padrão
            )
        st.markdown("---")

    elif view_to_show == 'COMERCIAL':
        # --- 6. EXIBIÇÃO - SEÇÃO 3: ANÁLISE COMERCIAL (PLANOS + CHURN + GRÁFICOS) ---
        st.caption(f"Período selecionado: {', '.join(sorted(selected_months, key=get_sort_key))}")

        main_col_left, main_col_right = st.columns([0.6, 0.4])

        with main_col_left:
            # Colunas aninhadas para os 3 cards de planos
            col1, col2, col3 = st.columns(3)
            with col1:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Essencial</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_essencial_orcado), delta=delta_essencial_orcado_str)
                    st.metric("Realizado", format_clients(total_essencial_realizado), delta=delta_essencial_realizado_str)
                    st.metric(
                        "Diferença",
                        format_clients(total_essencial_diferenca),
                        delta=delta_essencial_diferenca_str,
                        delta_color="normal" # [CORREÇÃO] Garantindo a cor padrão
                    )

            with col2:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Controle</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_vender_orcado), delta=delta_vender_orcado_str)
                    st.metric("Realizado", format_clients(total_vender_realizado), delta=delta_vender_realizado_str)
                    st.metric(
                        "Diferença",
                        format_clients(total_vender_diferenca),
                        delta=delta_vender_diferenca_str,
                        delta_color="normal" # [CORREÇÃO] Garantindo a cor padrão
                    )

            with col3:
                with st.container(border=True):
                    st.markdown("<h6 style='text-align: center;'>Avançado</h6>", unsafe_allow_html=True)
                    st.metric("Orçado", format_clients(total_avancado_orcado), delta=delta_avancado_orcado_str)
                    st.metric("Realizado", format_clients(total_avancado_realizado), delta=delta_avancado_realizado_str)
                    st.metric(
                        "Diferença",
                        format_clients(total_avancado_diferenca),
                        delta=delta_avancado_diferenca_str,
                        delta_color="normal" # [CORREÇÃO] Garantindo a cor padrão
                    )

            # --- Seção de Churn (agora na coluna da esquerda, abaixo dos planos) ---
            st.markdown("---")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em; opacity: 0.8;'>Churn Orçado</p>"
                            f"<h5 style='text-align: center;'>{format_clients(total_churn_orcado)}</h5>",
                            unsafe_allow_html=True)
            with col_c2:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em; opacity: 0.8;'>Churn Realizado</p>"
                            f"<h5 style='text-align: center;'>{format_clients(total_churn_realizado)}</h5>",
                            unsafe_allow_html=True)
            with col_c3:
                st.markdown(f"<p style='text-align: center; font-size: 0.7em; opacity: 0.8;'>Churn Diferença</p>"
                            f"<h5 style='text-align: center;'>{format_clients(total_churn_diferenca)}</h5>",
                            unsafe_allow_html=True)


        with main_col_right:
            # Gráfico de Pizza por Receita (MENSAL)
            st.markdown("<h6 style='text-align: center;'>Distribuição Mensal</h6>", unsafe_allow_html=True)
            values_mensal = [total_receita_essencial_mensal, total_receita_vender_mensal, total_receita_avancado_mensal]
            custom_data_mensal = [format_currency(v) for v in values_mensal]

            if sum(values_mensal) > 0:
                fig_mensal = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values_mensal,
                    hole=.4,
                    customdata=custom_data_mensal,
                    texttemplate='%{customdata}',
                    textfont_size=9,
                    hovertemplate='<b>%{label}</b><br>Receita: %{customdata} (%{percent:.0f})<extra></extra>',
                    marker=dict(colors=colors, line=dict(color='#FFFFFF', width=1)),
                    sort=False
                )])
                fig_mensal.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.01, font=dict(size=9)),
                    margin=dict(t=5, b=5, l=60, r=5),
                    height=180, # [CORREÇÃO] Altura diminuída
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white")
                )
                st.plotly_chart(fig_mensal, use_container_width=True)
            else:
                st.info("Sem dados mensais.")

            # Gráfico de Pizza por Receita (GERAL)
            st.markdown("<h6 style='text-align: center;'>Distribuição Geral</h6>", unsafe_allow_html=True)
            values_geral = [total_receita_essencial, total_receita_vender, total_receita_avancado]
            custom_data_geral = [format_currency(v) for v in values_geral]

            if sum(values_geral) > 0:
                fig_geral = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values_geral,
                    hole=.4,
                    customdata=custom_data_geral,
                    texttemplate='%{customdata}',
                    textfont_size=9,
                    hovertemplate='<b>%{label}</b><br>Receita: %{customdata} (%{percent:.0f})<extra></extra>',
                    marker=dict(colors=colors, line=dict(color='#FFFFFF', width=1)),
                    sort=False
                )])

                fig_geral.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.01, font=dict(size=9)),
                    margin=dict(t=5, b=5, l=60, r=5),
                    height=180, # [CORREÇÃO] Altura diminuída
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white")
                )
                st.plotly_chart(fig_geral, use_container_width=True)
            else:
                st.info("Sem dados gerais.")
    
    else: # [NOVO] view_to_show == 'GRAFICOS_EVOLUCAO'
        # --- TELA 3: GRÁFICOS DE EVOLUÇÃO ---
        
        # [ALTERAÇÃO] Os gráficos aqui usam o 'df' completo, ignorando o filtro 'selected_months'
        # Prepara os dados base (ordenados por Mês)
        chart_df = df.copy()
        chart_df['Mes'] = pd.Categorical(chart_df['Mes'], categories=all_months_list, ordered=True)
        chart_df = chart_df.sort_values('Mes')
        chart_df_final = chart_df.set_index('Mes')

        # Gráfico 1: Receita (Full Width)
        with st.container(border=True): # [ALTERAÇÃO] Borda adicionada
            # [ALTERAÇÃO] Título atualizado
            st.subheader("Meta MRR anual (agosto/25 a agosto/26)") 
            
            fig_receita = go.Figure()
            fig_receita.add_trace(go.Scatter(
                x=chart_df_final.index, y=chart_df_final['Receita Orcada'],
                mode='lines', name='Receita Orçada', line=dict(color='#0000FF') # Azul
            ))
            fig_receita.add_trace(go.Scatter(
                x=chart_df_final.index, y=chart_df_final['Receita Realizada'],
                mode='lines', name='Receita Realizada', line=dict(color='#00FF00') # Verde
            ))
            fig_receita.update_layout(
                height=300, # [ALTERAÇÃO] Altura diminuída
                xaxis=dict(tickangle=0), # [ALTERAÇÃO] Eixo X horizontal
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_receita, use_container_width=True)
        
        st.markdown("---") # Separador

        # Duas colunas para os gráficos de Clientes e Churn
        col_graf_1, col_graf_2 = st.columns(2)

        with col_graf_1:
            # Gráfico 2: Clientes
            with st.container(border=True): # [ALTERAÇÃO] Borda adicionada
                # [ALTERAÇÃO] Título atualizado
                st.subheader("Meta Clientes Anual (agosto/25 a agosto/26)") 
                
                chart_df_clientes_final = chart_df_final 
                
                cols_to_plot_clientes = ['Total de Clientes Orcados', 'Total de Clientes Realizados']
                if all(col in chart_df_clientes_final.columns for col in cols_to_plot_clientes):
                    fig_clientes = go.Figure()
                    fig_clientes.add_trace(go.Scatter(
                        x=chart_df_clientes_final.index, y=chart_df_clientes_final['Total de Clientes Orcados'],
                        mode='lines', name='Clientes Orçados', line=dict(color='#0000FF') # Azul
                    ))
                    fig_clientes.add_trace(go.Scatter(
                        x=chart_df_clientes_final.index, y=chart_df_clientes_final['Total de Clientes Realizados'],
                        mode='lines', name='Clientes Realizados', line=dict(color='#00FF00') # Verde
                    ))
                    fig_clientes.update_layout(
                        height=300, # [ALTERAÇÃO] Altura diminuída
                        xaxis=dict(tickangle=0), # [ALTERAÇÃO] Eixo X horizontal
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_clientes, use_container_width=True)
                else:
                    st.error("Colunas 'Total de Clientes Orcados' ou 'Total de Clientes Realizados' não encontradas.")

        with col_graf_2:
            # Gráfico 3: Churn Mensal
            with st.container(border=True): # [ALTERAÇÃO] Borda adicionada
                st.subheader("Churn") # [ALTERAÇÃO] Título atualizado
                
                chart_df_churn_final = chart_df_final 
                
                cols_to_plot_churn = ['Churn Orcado Mensal', 'Churn Realizado Mensal']
                if all(col in chart_df_churn_final.columns for col in cols_to_plot_churn):
                    fig_churn = go.Figure()
                    fig_churn.add_trace(go.Scatter(
                        x=chart_df_churn_final.index, y=chart_df_churn_final['Churn Orcado Mensal'],
                        mode='lines', name='Churn Orçado Mensal', line=dict(color='#FF0000') # Vermelho
                    ))
                    fig_churn.add_trace(go.Scatter(
                        x=chart_df_churn_final.index, y=chart_df_churn_final['Churn Realizado Mensal'],
                        mode='lines', name='Churn Realizado Mensal', line=dict(color='#800080') # Roxo
                    ))
                    fig_churn.update_layout(
                        height=300, # [ALTERAÇÃO] Altura diminuída
                        xaxis=dict(tickangle=0), # [ALTERAÇÃO] Eixo X horizontal
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_churn, use_container_width=True)
                else:
                    st.error("Colunas 'Churn Orcado Mensal' ou 'Churn Realizado Mensal' não encontradas.")

