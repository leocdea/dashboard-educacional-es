# ==============================================================================
# DASHBOARD EDUCACIONAL INTERATIVO - ESPÍRITO SANTO 2023
# ==============================================================================
# Autor: Leonardo Cruz de Andrade
# Disciplina: Cloud Computing para produtos de dados
# Professor: Maxwell Monteiro
#
# Descrição:
# Este dashboard interativo analisa a relação entre a infraestrutura escolar
# e o desempenho educacional (IDEB 2023) dos municípios do Espírito Santo.
# Os dados são carregados do Google BigQuery e visualizados de forma
# interativa usando Streamlit, Plotly e PyDeck.
#
# Versão Aprimorada:
# Esta versão mantém 100% da funcionalidade original, com foco em uma
# estilização visual refinada para uma aparência mais moderna e profissional.
# ==============================================================================


# --- 1. IMPORTAÇÃO DE BIBLIOTECAS ---
# Bibliotecas essenciais para o funcionamento do dashboard.
# ------------------------------------------------------------------------------
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import pydeck as pdk                      # Para a criação de mapas geoespaciais
from shapely import wkt                   # Para manipulação de dados geométricos (polígonos dos municípios)
import plotly.graph_objects as go
import plotly.express as px
import locale                             # Para ordenação correta de strings com acentos (ex: nomes de municípios)


# --- 2. CONFIGURAÇÕES INICIAIS DA APLICAÇÃO ---
# Define o layout da página, o locale para ordenação e os estilos visuais.
# ------------------------------------------------------------------------------

# Configuração da página do Streamlit (deve ser o primeiro comando st)
st.set_page_config(
    page_title="Dashboard Educacional ES",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define o locale para português do Brasil para garantir a ordenação alfabética correta
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252') # Fallback para sistemas Windows
    except locale.Error:
        st.sidebar.warning("Locale 'pt_BR' não encontrado. A ordenação pode não ser perfeita.")

# Definição da paleta de cores para consistência visual
COLOR_PRIMARY = "#004A8B" # Azul escuro para títulos principais
COLOR_SECONDARY = "#1F77B4" # Azul mais claro para subtítulos e elementos de UI
COLOR_ACCENT = "#FF6F61" # Um tom de coral para destaque (ex: linhas de tendência)
COLOR_BACKGROUND = "#F0F2F6" # Cinza claro para o fundo principal
COLOR_CARD_BACKGROUND = "#FFFFFF" # Branco para os cartões
COLOR_TEXT = "#333333" # Cinza escuro para texto
COLOR_SUCCESS = "#28A745" # Verde para indicadores positivos
COLOR_DANGER = "#DC3545" # Vermelho para indicadores negativos
COLOR_NEUTRAL = "#FFC107" # Amarelo para indicadores médios

# Estilos CSS customizados para uma aparência profissional e moderna.
st.markdown(f"""
<style>
    /* Importação da fonte e configurações globais */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="st-"], .stButton>button {{
        font-family: 'Roboto', sans-serif;
        color: {COLOR_TEXT};
    }}

    /* Fundo principal da aplicação */
    .main {{
        background-color: {COLOR_BACKGROUND};
    }}

    /* Container principal com espaçamento otimizado */
    .block-container {{
        padding: 2rem 3rem 3rem 3rem;
    }}

    /* Estilo dos cards para cada visualização */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {{
        background-color: {COLOR_CARD_BACKGROUND};
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 28px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.3s ease-in-out;
    }}
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"]:hover {{
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    }}

    /* Barra lateral */
    [data-testid="stSidebar"] {{
        background-color: #FAFBFC;
        border-right: 1px solid #E0E0E0;
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: {COLOR_PRIMARY};
    }}

    /* Tipografia e Hierarquia Visual */
    h1 {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
        padding-bottom: 0.5rem;
    }}
    h2 {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {COLOR_SECONDARY};
        border-bottom: 3px solid {COLOR_SECONDARY};
        padding-bottom: 10px;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
    }}
    h5 {{
        color: {COLOR_SECONDARY};
        font-weight: 500;
    }}

    /* Estilo das métricas (KPIs) */
    .stMetric {{
        background-color: #F8F9FA;
        border: 1px solid #DEE2E6;
        border-left: 5px solid {COLOR_SECONDARY};
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }}
    .stMetric label {{
        font-weight: 500;
    }}
    .stMetric p {{
        font-size: 1.5rem;
        font-weight: 700;
    }}

    /* Cabeçalho de informações */
    .header-info {{
        font-size: 0.85rem;
        color: #555;
        text-align: right;
        line-height: 1.5;
        padding-top: 1.5rem;
    }}
    
    /* Linha divisória customizada */
    hr {{
        border: none;
        border-top: 1px solid #E0E0E0;
        margin: 2rem 0;
    }}

    /* --- SOLUÇÃO PARA CORRIGIR OS ÍCONES DA BARRA LATERAL NO STREAMLIT --- */
    /* 1. Oculta o ícone de texto padrão que pode quebrar o layout */
    span[data-testid="stIconMaterial"] {{
        display: none !important;
    }}
    /* 2. Redesenha os ícones de seta usando SVG para controle total */
    button[data-testid="stSidebarCollapseButton"]::before, button[data-testid="stExpandSidebarButton"]::before {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: block;
        width: 24px;
        height: 24px;
    }}
    /* Ícone para RECOLHER (seta para a esquerda) */
    button[data-testid="stSidebarCollapseButton"]::before {{
        content: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3e%3cpath fill='%23555' d='M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z'/%3e%3c/svg%3e");
    }}
    /* Ícone para EXPANDIR (seta para a direita) */
    button[data-testid="stExpandSidebarButton"]::before {{
        content: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3e%3cpath fill='%23555' d='M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z'/%3e%3c/svg%3e");
    }}
    /* 3. Força o posicionamento correto do botão de expandir */
    button[data-testid="stExpandSidebarButton"] {{
        position: fixed;
        left: 10px;
        top: 10px;
        z-index: 100000;
        background-color: rgba(240, 242, 246, 0.8);
        border-radius: 50%;
        width: 48px;
        height: 48px;
        transition: background-color 0.2s;
    }}
    button[data-testid="stExpandSidebarButton"]:hover {{
        background-color: rgba(230, 230, 230, 1);
    }}

    /* --- Centralização da legenda do mapa --- */
    div[data-testid="stVerticalBlock"]:has(div.legend-container) {{
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .legend-container {{
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}

    /* Media queries para responsividade */
    @media (max-width: 992px) {{
        .block-container {{ padding: 1.5rem; }}
        .header-info {{ text-align: center; margin-top: 1rem; padding-top: 0; }}
    }}
</style>
""", unsafe_allow_html=True)


# --- 3. CONSTANTES E CONFIGURAÇÕES DO BIGQUERY ---
# Centraliza as configurações do projeto para facilitar a manutenção.
# ------------------------------------------------------------------------------
DATASET_ID = "dados_educacionais_es"
IDEB_TABLE = "ideb_2023"
CENSO_TABLE = "censo_2023"
MAP_TABLE = "limites_municipais_es"


# --- 4. FUNÇÕES DE ACESSO E PROCESSAMENTO DE DADOS ---
# Funções otimizadas com cache para conectar ao BigQuery e carregar os dados.
# ------------------------------------------------------------------------------

@st.cache_resource
def get_bq_client():
    """
    Cria e gerencia a conexão com o Google BigQuery usando as credenciais
    armazenadas no Streamlit Secrets.
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        project_id = credentials.project_id
        client = bigquery.Client(credentials=credentials, project=project_id)
        return client, project_id
    except Exception as e:
        st.error("Erro ao conectar com o BigQuery. Verifique suas credenciais no secrets.toml.")
        st.exception(e)
        st.stop()

@st.cache_data(ttl=3600)
def run_query(_client, query):
    """
    Executa uma consulta SQL no BigQuery e retorna o resultado como um DataFrame Pandas.
    """
    try:
        query_job = _client.query(query)
        return query_job.to_dataframe()
    except Exception as e:
        st.error(f"Erro ao executar a consulta no BigQuery.")
        st.exception(e)
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_and_prepare_data(_client, project_id, dataset_id, ideb_table, censo_table):
    """
    Carrega, une as tabelas do IDEB e do Censo, e prepara os dados para visualização.
    """
    query = f"""
        SELECT
            t1.*,
            t2.total_estimar_escolas, t2.escolas_com_internet, t2.escolas_com_lab_informatica,
            t2.escolas_com_biblioteca, t2.escolas_com_quadra_esportes, t2.escolas_com_banheiro_acessivel_pne,
            t2.pct_escolas_com_internet, t2.alunos_por_docente, t2.alunos_por_turma
        FROM `{project_id}.{dataset_id}.{ideb_table}` AS t1
        LEFT JOIN `{project_id}.{dataset_id}.{censo_table}` AS t2
        ON CAST(t1.cod_munic AS STRING) = CAST(t2.cod_munic AS STRING)
    """
    df = run_query(_client, query)

    numeric_cols = [
        'ideb_2023', 'nota_saeb_media_2023', 'tx_aprov_2023_1_ao_5_ano',
        'total_estimar_escolas', 'escolas_com_internet', 'escolas_com_lab_informatica',
        'escolas_com_biblioteca', 'escolas_com_quadra_esportes',
        'escolas_com_banheiro_acessivel_pne', 'pct_escolas_com_internet',
        'alunos_por_docente', 'alunos_por_turma'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    friendly_names = {
        'nome_munic': 'Município', 'ideb_2023': 'Nota IDEB 2023',
        'nota_saeb_media_2023': 'Nota Média SAEEB 2023', 'tx_aprov_2023_1_ao_5_ano': 'Taxa de Aprovação (1º-5º ano)',
        'total_estimar_escolas': 'Total de Escolas', 'escolas_com_internet': 'Nº Escolas c/ Internet',
        'escolas_com_lab_informatica': 'Nº Escolas c/ Lab. de Informática', 'escolas_com_biblioteca': 'Nº Escolas c/ Biblioteca',
        'escolas_com_quadra_esportes': 'Nº Escolas c/ Quadra', 'escolas_com_banheiro_acessivel_pne': 'Nº Escolas c/ Acessibilidade',
        'pct_escolas_com_internet': '% Escolas com Internet', 'alunos_por_docente': 'Média de Alunos por Docente',
        'alunos_por_turma': 'Média de Alunos por Turma'
    }
    df = df.rename(columns=friendly_names)
    return df, friendly_names


# --- 5. INICIALIZAÇÃO DA APLICAÇÃO ---
# ------------------------------------------------------------------------------
client, PROJECT_ID = get_bq_client()
df_completo, friendly_names = load_and_prepare_data(client, PROJECT_ID, DATASET_ID, IDEB_TABLE, CENSO_TABLE)


# --- 6. INTERFACE DO USUÁRIO (UI) - CABEÇALHO E BARRA LATERAL ---
# ------------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Dashboard Educacional Interativo")
        st.markdown("##### Análise da Relação entre Infraestrutura Escolar e Desempenho no IDEB 2023 no Espírito Santo")
    with col2:
        st.markdown(f"<div class='header-info'><b>Pós-Graduação em Mineração de Dados Educacionais</b><br>Disciplina: Cloud Computing para produtos de dados<br>Professor: Maxwell Monteiro<br>Aluno: Leonardo Cruz de Andrade</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

st.sidebar.title("🎓 Painel de Controle")
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Filtros e Navegação")

if not df_completo.empty:
    lista_municipios = sorted(df_completo['Município'].unique(), key=locale.strxfrm)
    municipios_selecionados = st.sidebar.multiselect(
        "Selecione um ou mais municípios:",
        options=lista_municipios,
        default=[],
        placeholder="Todos os municípios"
    )
else:
    municipios_selecionados = []
    st.sidebar.warning("Não foi possível carregar a lista de municípios.")

df_filtrado = df_completo[df_completo['Município'].isin(municipios_selecionados)] if municipios_selecionados else df_completo

secao = st.sidebar.radio(
    'Selecione a Análise:',
    ['Página Inicial', 'Visão Geral', 'Análise de Infraestrutura', 'Análise de Correlação', 'Análise Comparativa', 'Dados Detalhados'],
    horizontal=False
)


# --- 7. RENDERIZAÇÃO DAS SEÇÕES (PÁGINAS) ---
# ------------------------------------------------------------------------------

if secao == 'Página Inicial':
    st.header("📖 Visão Geral do Projeto e das Bases de Dados")
    st.markdown("O objetivo deste projeto é analisar a relação da infraestrutura escolar com o desempenho educacional no ano de 2023 das escolas públicas municipais do Estado do Espírito Santo, com foco nos anos iniciais (Ensino Fundamental I), para extrair insights sobre oportunidades de melhorias nas políticas públicas. Abaixo, apresentamos as estatísticas descritivas das duas principais bases de dados utilizadas.")

    st.subheader("Estatísticas Descritivas do Censo Escolar 2023")
    query_censo_describe = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{CENSO_TABLE}`"
    df_censo_full = run_query(client, query_censo_describe)
    if not df_censo_full.empty:
        df_numeric = df_censo_full.select_dtypes(include='number').drop(columns=['cod_munic'], errors='ignore')
        st.dataframe(df_numeric.rename(columns=friendly_names).describe().style.format("{:.2f}").set_properties(**{'background-color': '#f8f9fa', 'color': COLOR_TEXT}))
    else:
        st.warning("Não foi possível carregar os dados para a tabela descritiva do Censo.")

    st.markdown("---")

    st.subheader("Estatísticas Descritivas do IDEB 2023")
    query_ideb_describe = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{IDEB_TABLE}`"
    df_ideb_full = run_query(client, query_ideb_describe)
    if not df_ideb_full.empty:
        df_numeric_ideb = df_ideb_full.select_dtypes(include='number').drop(columns=['cod_munic'], errors='ignore')
        st.dataframe(df_numeric_ideb.rename(columns=friendly_names).describe().style.format("{:.2f}").set_properties(**{'background-color': '#f8f9fa', 'color': COLOR_TEXT}))
    else:
        st.warning("Não foi possível carregar os dados para a tabela descritiva do IDEB.")

elif secao == 'Visão Geral':
    st.header("🗺️ Desempenho Geral do IDEB 2023 no Estado")

    map_col, legend_col = st.columns([4, 1])

    with map_col:
        query_mapa = f"""
            SELECT t1.NM_MUN AS municipio, t1.geometry, t2.ideb_2023 AS nota_ideb
            FROM `{PROJECT_ID}.{DATASET_ID}.{MAP_TABLE}` AS t1
            JOIN `{PROJECT_ID}.{DATASET_ID}.{IDEB_TABLE}` AS t2
            ON CAST(t1.cod_munic AS STRING) = CAST(t2.cod_munic AS STRING)
        """
        df_mapa = run_query(client, query_mapa)

        if not df_mapa.empty:
            df_mapa.dropna(subset=['geometry', 'nota_ideb'], inplace=True)
            df_mapa['geometry_obj'] = df_mapa['geometry'].apply(wkt.loads)
            df_mapa['polygons'] = df_mapa['geometry_obj'].apply(lambda geom: [list(coord) for coord in geom.exterior.coords])
            view_state = pdk.ViewState(latitude=-19.5, longitude=-40.5, zoom=6.5, bearing=0, pitch=0)

            def get_color(nota):
                if pd.isnull(nota): return [200, 200, 200, 100]
                if nota < 5.8: return [220, 53, 69, 160] # Vermelho (Danger)
                if nota < 6.5: return [255, 193, 7, 160] # Amarelo (Neutral)
                return [40, 167, 69, 160] # Verde (Success)

            df_mapa['cor'] = df_mapa['nota_ideb'].apply(get_color)
            map_data = df_mapa[['municipio', 'nota_ideb', 'polygons', 'cor']].copy()
            # Pré-formata a nota do IDEB como string para a tooltip
            map_data['nota_ideb_str'] = map_data['nota_ideb'].apply(lambda x: f"{x:.2f}")
            polygon_layer = pdk.Layer('PolygonLayer', data=map_data, get_polygon='polygons', filled=True, get_fill_color='cor', pickable=True, auto_highlight=True, highlight_color=[255, 111, 97, 180])
            # Usa a coluna pré-formatada na tooltip
            tooltip = {"html": "<b>Município:</b> {municipio} <br/> <b>IDEB:</b> {nota_ideb_str}", "style": {"backgroundColor": "#333", "color": "white", "borderRadius": "5px", "padding": "8px"}}
            
            r = pdk.Deck(layers=[polygon_layer], initial_view_state=view_state, tooltip=tooltip, map_style='mapbox://styles/mapbox/light-v9')
            st.pydeck_chart(r)
        else:
            st.warning("Não foi possível carregar os dados do mapa.")

    with legend_col:
        st.html(f"""
        <div class="legend-container">
            <div style="text-align: center; background-color: {COLOR_CARD_BACKGROUND}; border-radius: 12px; padding: 20px; border: 1px solid #e0e0e0; width: 100%;">
                <h5 style="margin-bottom: 15px; color: {COLOR_TEXT};">Legenda - Nota IDEB</h5>
                <div style="text-align: left;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 20px; height: 20px; background-color: {COLOR_SUCCESS}; margin-right: 10px; border-radius: 3px; flex-shrink: 0;"></div>
                        <span><b>Alto:</b> &ge; 6.5</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 20px; height: 20px; background-color: {COLOR_NEUTRAL}; margin-right: 10px; border-radius: 3px; flex-shrink: 0;"></div>
                        <span><b>Médio:</b> 5.8-6.4</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background-color: {COLOR_DANGER}; margin-right: 10px; border-radius: 3px; flex-shrink: 0;"></div>
                        <span><b>Baixo:</b> &lt; 5.8</span>
                    </div>
                </div>
            </div>
        </div>
        """)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Ranking de Desempenho dos Municípios")
    rank_col1, rank_col2 = st.columns(2)
    
    chart_font = dict(family="Roboto, sans-serif", size=12, color=COLOR_TEXT)

    with rank_col1:
        st.markdown("##### 🚀 Top 5 Melhores Desempenhos")
        df_top5 = df_filtrado.nlargest(5, 'Nota IDEB 2023')
        fig_top5 = px.bar(df_top5.sort_values('Nota IDEB 2023', ascending=True), y='Município', x='Nota IDEB 2023', text_auto=True, orientation='h')
        fig_top5.update_traces(marker_color=COLOR_SUCCESS, texttemplate='%{x:.2f}', textposition="outside")
        fig_top5.update_layout(yaxis_title=None, xaxis_title="Nota IDEB", plot_bgcolor='rgba(0,0,0,0)', font=chart_font, uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_top5, use_container_width=True)

    with rank_col2:
        st.markdown("##### 🔻 Top 5 Piores Desempenhos")
        df_bottom5 = df_filtrado.nsmallest(5, 'Nota IDEB 2023')
        fig_bottom5 = px.bar(df_bottom5.sort_values('Nota IDEB 2023', ascending=False), y='Município', x='Nota IDEB 2023', text_auto=True, orientation='h')
        fig_bottom5.update_traces(marker_color=COLOR_DANGER, texttemplate='%{x:.2f}', textposition="outside")
        fig_bottom5.update_layout(yaxis_title=None, xaxis_title="Nota IDEB", plot_bgcolor='rgba(0,0,0,0)', font=chart_font, uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_bottom5, use_container_width=True)

elif secao == 'Análise de Infraestrutura':
    st.header("📊 Análise de Infraestrutura (Censo 2023)")
    st.markdown("Média e distribuição dos indicadores para os municípios selecionados.")

    if not df_filtrado.empty:
        total_escolas = df_filtrado['Total de Escolas'].sum()
        avg_internet = df_filtrado['% Escolas com Internet'].mean()
        avg_lab = (df_filtrado['Nº Escolas c/ Lab. de Informática'].sum() / total_escolas) * 100 if total_escolas > 0 else 0
        avg_quadra = (df_filtrado['Nº Escolas c/ Quadra'].sum() / total_escolas) * 100 if total_escolas > 0 else 0
        avg_acessibilidade = (df_filtrado['Nº Escolas c/ Acessibilidade'].sum() / total_escolas) * 100 if total_escolas > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="% Escolas com Internet", value=f"{avg_internet:.1f}%")
        col2.metric(label="% com Lab. Informática", value=f"{avg_lab:.1f}%")
        col3.metric(label="% com Quadra Esportiva", value=f"{avg_quadra:.1f}%")
        col4.metric(label="% com Acessibilidade", value=f"{avg_acessibilidade:.1f}%")
        st.markdown("<hr>", unsafe_allow_html=True)

        st.subheader("Distribuição de Indicadores")
        col1, col2 = st.columns(2)
        chart_font = dict(family="Roboto, sans-serif", size=12, color=COLOR_TEXT)

        with col1:
            fig = px.histogram(df_filtrado, x="Média de Alunos por Turma", nbins=20, title="Distribuição de Alunos por Turma", color_discrete_sequence=[COLOR_SECONDARY])
            fig.update_yaxes(title_text='Número de Municípios')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', bargap=0.1, font=chart_font)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.histogram(df_filtrado, x="% Escolas com Internet", nbins=20, title="Distribuição de % de Escolas com Internet", color_discrete_sequence=[COLOR_SECONDARY])
            fig.update_yaxes(title_text='Número de Municípios')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', bargap=0.1, font=chart_font)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para os municípios selecionados.")

elif secao == 'Análise de Correlação':
    st.header("🔍 Análise de Correlação entre IDEB e Infraestrutura")
    chart_font = dict(family="Roboto, sans-serif", size=12, color=COLOR_TEXT)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Correlação Interativa")
        st.write("Explore a relação entre o IDEB e um indicador de infraestrutura escolar.")
        opcoes_correlacao = {v: k for k, v in friendly_names.items() if k in ['pct_escolas_com_internet', 'alunos_por_turma', 'alunos_por_docente', 'tx_aprov_2023_1_ao_5_ano']}
        indicador_selecionado_friendly = st.selectbox("Selecione um indicador:", options=list(opcoes_correlacao.keys()))

    with col2:
        if not df_filtrado.empty and indicador_selecionado_friendly:
            df_chart = df_filtrado[[friendly_names['ideb_2023'], indicador_selecionado_friendly]].dropna()
            fig = px.scatter(df_chart, x=indicador_selecionado_friendly, y=friendly_names['ideb_2023'],
                             title=f"Relação entre {friendly_names['ideb_2023']} e {indicador_selecionado_friendly}",
                             trendline="ols", trendline_color_override=COLOR_ACCENT)
            fig.update_traces(marker=dict(color=COLOR_SECONDARY, size=8, opacity=0.7))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=chart_font)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Selecione um município para visualizar a correlação.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Mapa de Calor de Correlações")
    if not df_filtrado.empty:
        df_corr = df_filtrado.select_dtypes(include='number').drop(columns=['cod_munic'], errors='ignore')
        corr = df_corr.rename(columns=friendly_names).corr()
        fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns, colorscale='RdBu_r', zmin=-1, zmax=1, colorbar=dict(thickness=15)))
        fig.update_layout(title_text="Matriz de Correlação de Todas as Variáveis Numéricas", height=600, font=chart_font)
        st.plotly_chart(fig, use_container_width=True)

elif secao == 'Análise Comparativa':
    st.header("🆚 Análise Comparativa entre Municípios")
    st.write("Selecione dois ou mais municípios na barra lateral para compará-los lado a lado.")

    if len(municipios_selecionados) < 2:
        st.info("ℹ️ Por favor, selecione pelo menos dois municípios no filtro da barra lateral para ativar a comparação.", icon="💡")
    else:
        indicadores_comparacao_friendly = {
            'Nota IDEB 2023': 'Nota IDEB 2023',
            '% Escolas com Internet': '% Escolas com Internet',
            'Média de Alunos por Turma': 'Média de Alunos por Turma',
            'Média de Alunos por Docente': 'Média de Alunos por Docente'
        }
        indicador_comp_selecionado = st.selectbox("Selecione um indicador para comparar:", options=list(indicadores_comparacao_friendly.keys()))

        df_comp = df_filtrado[['Município', indicador_comp_selecionado]].dropna().sort_values(by=indicador_comp_selecionado, ascending=False)
        fig = px.bar(df_comp, x='Município', y=indicador_comp_selecionado,
                     title=f"Comparativo de '{indicador_comp_selecionado}'",
                     color='Município',
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     text_auto=True)
        fig.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False, texttemplate='%{y:.2f}')
        chart_font = dict(family="Roboto, sans-serif", size=12, color=COLOR_TEXT)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', uniformtext_minsize=8, uniformtext_mode='hide', showlegend=False, font=chart_font)
        st.plotly_chart(fig, use_container_width=True)

elif secao == 'Dados Detalhados':
    st.header("📚 Dados Detalhados por Município")
    st.write("Tabela com todos os indicadores para os municípios selecionados. Clique no cabeçalho de uma coluna para ordenar.")

    if not df_filtrado.empty:
        df_to_display = df_filtrado.drop(columns=['cod_munic'], errors='ignore').set_index('Município')
        numeric_cols_to_format = df_to_display.select_dtypes(include='number').columns
        st.dataframe(df_to_display.style.format("{:.2f}", subset=numeric_cols_to_format), use_container_width=True)
    else:
        st.info("ℹ️ Selecione um ou mais municípios no filtro da barra lateral para ver os dados detalhados.", icon="💡")



