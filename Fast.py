import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io

st.set_page_config(page_title="FAST", layout="wide")

# Conexão com banco
conn = sqlite3.connect("fast.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabelas se não existirem
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY,
    descricao TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS padaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    codigo TEXT,
    descricao TEXT,
    quantidade REAL,
    unidade TEXT,
    motivo TEXT,
    lote TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS carnes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    codigo TEXT,
    descricao TEXT,
    codigo_destino TEXT,
    descricao_destino TEXT,
    quantidade REAL,
    unidade TEXT,
    lote TEXT
)
""")
conn.commit()

# Carrega base produtos uma vez
def carregar_base():
    if 'produtos' not in st.session_state:
        df = pd.read_sql("SELECT * FROM produtos", conn)
        st.session_state.produtos = df

carregar_base()

# Função para buscar descrição
def buscar_descricao(codigo):
    df = st.session_state.produtos
    resultado = df[df['codigo'] == codigo]
    if not resultado.empty:
        return resultado.iloc[0]['descricao']
    return ""

# Layout
st.title("🧾 FAST")

abas = st.tabs(["📋 Lançamentos Padaria", "🥩 Transformações Carne"])

with abas[0]:
    st.subheader("📋 Registro de Lançamentos da Padaria")

    with st.form("form_padaria", clear_on_submit=True):
        col1, col2, col3 = st.columns([1.5, 3, 1])
        with col1:
            codigo = st.text_input("Código").strip()
        with col2:
            descricao = buscar_descricao(codigo)
            st.text_input("Descrição", value=descricao, disabled=True)
        with col3:
            quantidade = st.number_input("Quantidade", min_value=0.01, step=0.01)

        col4, col5, col6 = st.columns(3)
        with col4:
            unidade = st.selectbox("Unidade", ["kg", "un"])
        with col5:
            motivo = st.selectbox("Motivo", ["Avaria", "Doação", "Refeitório", "Inventário"])
        with col6:
            lote = st.text_input("Lote")

        submitted = st.form_submit_button("Salvar")
        if submitted:
            cursor.execute("""
                INSERT INTO padaria (data, codigo, descricao, quantidade, unidade, motivo, lote)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(date.today()), codigo, descricao, quantidade, unidade, motivo, lote))
            conn.commit()
            st.success("Registro salvo!")

    st.markdown("### 📅 Registros de Hoje:")
    df_padaria = pd.read_sql(f"SELECT * FROM padaria WHERE data = '{date.today()}'", conn)
    st.dataframe(df_padaria, use_container_width=True)

    # Exportações
    def exportar_padaria():
        df = pd.read_sql("SELECT * FROM padaria", conn)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Lançamentos", index=False)
            resumo = df.groupby("descricao")["quantidade"].sum().reset_index()
            resumo.to_excel(writer, sheet_name="Total por Produto", index=False)
        output.seek(0)
        return output

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Baixar Excel (detalhado)", data=exportar_padaria(),
                           file_name="padaria_detalhado.xlsx", mime="application/vnd.ms-excel")
    with col2:
        st.download_button("📥 Baixar Excel (total por produto)",
                           data=exportar_padaria(), file_name="padaria_total.xlsx", mime="application/vnd.ms-excel")

with abas[1]:
    st.subheader("🥩 Registro de Transformações de Carne")

    with st.form("form_carnes", clear_on_submit=True):
        col1, col2, col3 = st.columns([1.5, 3, 1])
        with col1:
            codigo = st.text_input("Código origem").strip()
        with col2:
            descricao = buscar_descricao(codigo)
            st.text_input("Descrição origem", value=descricao, disabled=True)
        with col3:
            quantidade = st.number_input("Quantidade", min_value=0.01, step=0.01, key="qtd_carnes")

        col4, col5, col6 = st.columns([1.5, 3, 1])
        with col4:
            codigo_destino = st.text_input("Código destino").strip()
        with col5:
            descricao_destino = buscar_descricao(codigo_destino)
            st.text_input("Descrição destino", value=descricao_destino, disabled=True)
        with col6:
            unidade = st.selectbox("Unidade", ["kg", "un"], key="un_carnes")

        lote = st.text_input("Lote", key="lote_carnes")

        submitted = st.form_submit_button("Salvar")
        if submitted:
            cursor.execute("""
                INSERT INTO carnes (data, codigo, descricao, codigo_destino, descricao_destino, quantidade, unidade, lote)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(date.today()), codigo, descricao, codigo_destino, descricao_destino, quantidade, unidade, lote))
            conn.commit()
            st.success("Transformação registrada!")

    st.markdown("### 📅 Transformações de Hoje:")
    df_carnes = pd.read_sql(f"SELECT * FROM carnes WHERE data = '{date.today()}'", conn)
    st.dataframe(df_carnes, use_container_width=True)

    # Exportações
    def exportar_carnes():
        df = pd.read_sql("SELECT * FROM carnes", conn)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Transformações", index=False)
            resumo = df.groupby("descricao_destino")["quantidade"].sum().reset_index()
            resumo.to_excel(writer, sheet_name="Total por Produto", index=False)
        output.seek(0)
        return output

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Baixar Excel (detalhado)", data=exportar_carnes(),
                           file_name="carnes_detalhado.xlsx", mime="application/vnd.ms-excel")
    with col2:
        st.download_button("📥 Baixar Excel (total por produto)",
                           data=exportar_carnes(), file_name="carnes_total.xlsx", mime="application/vnd.ms-excel")
