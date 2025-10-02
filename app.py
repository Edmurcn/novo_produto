import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configurações do Streamlit
st.set_page_config(page_title="MVP Agro", page_icon="🌱", layout="wide")
st.title("📊 MVP Agro - Gestão de Leads")

# Inicializando flag de rerun no session_state
if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

# Logo da empresa (substitua 'logo.jpg' pelo arquivo do cliente)
st.image("logo.jpg", width=150)

# Conexão SQLite
engine = create_engine("sqlite:///leads.db", echo=True)

# Criação da tabela se não existir
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT,
            nome TEXT,
            estado TEXT,
            cidade TEXT,
            telefone TEXT,
            email TEXT,
            rede_social TEXT,
            cultivo TEXT,
            etapa TEXT DEFAULT 'Leads'
        )
    """))

# Upload de arquivo CSV
uploaded_file = st.file_uploader("Carregar lista de leads (CSV)", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["etapa"] = "Leads"
    df.to_sql("leads", engine, if_exists="append", index=False)
    st.success("Leads importados com sucesso!")
    st.session_state['rerun'] = True

# Filtros
with engine.connect() as conn:
    estados_result = conn.execute(text("SELECT DISTINCT estado FROM leads")).all()
    cultivos_result = conn.execute(text("SELECT DISTINCT cultivo FROM leads")).all()

estado_filtro = st.selectbox("Filtrar por estado", ["Todos"] + [e[0] for e in estados_result])
cultivo_filtro = st.selectbox("Filtrar por cultivo", ["Todos"] + [c[0] for c in cultivos_result])

# Montando query com parâmetros seguros
query = "SELECT * FROM leads"
condicoes = []
params = {}
if estado_filtro != "Todos":
    condicoes.append("estado = :estado")
    params["estado"] = estado_filtro
if cultivo_filtro != "Todos":
    condicoes.append("cultivo = :cultivo")
    params["cultivo"] = cultivo_filtro
if condicoes:
    query += " WHERE " + " AND ".join(condicoes)

leads_df = pd.read_sql(text(query), engine, params=params)

# Etapas e cores
etapas = ["Leads", "Em andamento", "Contato Qualificado"]
cores = {
    "Leads": "#FFF7CC",            # amarelo claro
    "Em andamento": "#CCE5FF",     # azul claro
    "Contato Qualificado": "#CCFFCC"  # verde claro
}
borda = {
    "Leads": "#FFD700",             # dourado
    "Em andamento": "#3399FF",      # azul
    "Contato Qualificado": "#33CC33" # verde
}

# Função para atualizar etapa
def atualizar_etapa(nova_etapa, lead_id, etapa_atual):
    if nova_etapa != etapa_atual:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE leads SET etapa = :nova_etapa WHERE id = :id"),
                {"nova_etapa": nova_etapa, "id": lead_id}
            )
        st.session_state['rerun'] = True

# Layout lado a lado
cols = st.columns(len(etapas))
for idx, etapa in enumerate(etapas):
    with cols[idx]:
        st.subheader(etapa)
        etapa_df = leads_df[leads_df["etapa"] == etapa]
        for _, row in etapa_df.iterrows():
            # Card com cor e borda indicando etapa
            st.markdown(
                f"""
                <div style='
                    background-color: {cores[etapa]};
                    color: #000000;
                    padding: 12px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    border-left: 5px solid {borda[etapa]};
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                '>
                    <b>{row['nome']}</b><br>
                    {row['cidade']} / {row['estado']}<br>
                    CNPJ: {row['cnpj']}<br>
                    Cultivo: {row['cultivo']}<br>
                    Contato: {row['telefone']} | {row['email']}
                </div>
                """, unsafe_allow_html=True
            )

            # Selectbox com on_change para atualizar automaticamente
            st.selectbox(
                "Mover para:", etapas, index=etapas.index(etapa),
                key=f"etapa_{row['id']}",
                on_change=atualizar_etapa,
                args=(st.session_state.get(f"etapa_{row['id']}", etapa), row["id"], etapa)
            )

# Reiniciar app se necessário
if st.session_state['rerun']:
    st.session_state['rerun'] = False
    st.experimental_rerun()

