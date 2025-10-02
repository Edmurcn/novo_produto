import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from io import BytesIO

import sys
st.write("Python version:", sys.version)

# ---------------- Configurações iniciais ----------------
st.set_page_config(page_title="MVP Agro", page_icon="🌱", layout="wide")
st.title("📊 MVP Agro - Gestão de Leads")

# Logo da empresa
st.image("logo.jpg", width=150)

# ---------------- Conexão com SQLite ----------------
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

# ---------------- Upload de CSV ----------------
uploaded_file = st.file_uploader("Carregar lista de leads (CSV)", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["etapa"] = "Leads"
    df.to_sql("leads", engine, if_exists="append", index=False)
    st.success("Leads importados com sucesso!")

# ---------------- Filtros ----------------
with engine.connect() as conn:
    estados_result = conn.execute(text("SELECT DISTINCT estado FROM leads")).all()
    cultivos_result = conn.execute(text("SELECT DISTINCT cultivo FROM leads")).all()

estado_filtro = st.selectbox("Filtrar por estado", ["Todos"] + [e[0] for e in estados_result])
cultivo_filtro = st.selectbox("Filtrar por cultivo", ["Todos"] + [c[0] for c in cultivos_result])

# ---------------- Montando query ----------------
query_base = "SELECT * FROM leads"
condicoes = []
params = {}
if estado_filtro != "Todos":
    condicoes.append("estado = :estado")
    params["estado"] = estado_filtro
if cultivo_filtro != "Todos":
    condicoes.append("cultivo = :cultivo")
    params["cultivo"] = cultivo_filtro
if condicoes:
    query_base += " WHERE " + " AND ".join(condicoes)

# ---------------- Etapas e cores ----------------
etapas = ["Leads", "Em andamento", "Contato Qualificado"]
cores = {
    "Leads": "#FFF7CC",
    "Em andamento": "#CCE5FF",
    "Contato Qualificado": "#CCFFCC"
}
borda = {
    "Leads": "#FFD700",
    "Em andamento": "#3399FF",
    "Contato Qualificado": "#33CC33"
}

# ---------------- Carregando leads em session_state ----------------
if 'leads_df' not in st.session_state:
    st.session_state['leads_df'] = pd.read_sql(text(query_base), engine, params=params)

# Função para atualizar etapa de um lead
def atualizar_etapa(lead_id):
    nova_etapa = st.session_state[f"etapa_{lead_id}"]
    # Atualiza no banco
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE leads SET etapa = :nova_etapa WHERE id = :id"),
            {"nova_etapa": nova_etapa, "id": lead_id}
        )
    # Atualiza no DataFrame em memória
    st.session_state['leads_df'].loc[
        st.session_state['leads_df']['id'] == lead_id, 'etapa'
    ] = nova_etapa

# Função para exportar contatos qualificados
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Contatos Qualificados')
    return output.getvalue()

# ---------------- Layout Kanban ----------------
cols = st.columns(len(etapas))


for idx, etapa in enumerate(etapas):
    with cols[idx]:
        st.subheader(etapa)
        etapa_df = st.session_state['leads_df'][st.session_state['leads_df']['etapa'] == etapa]

        # ---------- Botões ----------
        if etapa == "Contato Qualificado":
            btn_cols = st.columns([5,2])
            with btn_cols[1]:
                if not etapa_df.empty:
                    excel_data = to_excel(etapa_df)
                    st.download_button(
                        label="Exportar",
                        data=excel_data,
                        file_name="leads_contato_qualificado.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.button("Exportar (nenhum lead)", disabled=True)

        if etapa == "Leads" and not etapa_df.empty:
            if st.button("Limpar Leads", key="limpar_leads"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM leads WHERE etapa = 'Leads'"))
                # Remove do DataFrame em memória
                st.session_state['leads_df'] = st.session_state['leads_df'][st.session_state['leads_df']['etapa'] != 'Leads']
                st.success("Todos os leads na etapa 'Leads' foram removidos.")

        # ---------- Cards ----------
        for _, row in etapa_df.iterrows():
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

            # Selectbox para mover lead
            st.selectbox(
                "Mover para:",
                etapas,
                index=etapas.index(etapa),
                key=f"etapa_{row['id']}",
                on_change=atualizar_etapa,
                args=(row["id"],)
            )
