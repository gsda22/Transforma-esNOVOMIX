import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io

st.set_page_config(page_title="FAST", layout="wide")

# Banco SQLite
conn = sqlite3.connect("fast.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabelas
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

# Carregar produtos para sessão
def carregar_produtos():
    if 'produtos' not in st.session_state:
        df = pd.read_sql("SELECT * FROM produtos", conn)
        st.session_state.produtos = df

carregar_produtos()

def buscar_descricao(codigo: str) -> str:
    if not codigo:
        return ""
    df = st.session_state.produtos
    prod = df.loc[df['codigo'] == codigo]
    return prod['descricao'].values[0] if not prod.empty else ""

def validar_codigo(codigo: str) -> bool:
    if not codigo.strip():
        st.error("⚠️ Código não pode estar vazio.")
        return False
    return True

def validar_quantidade(qtd: float) -> bool:
    if qtd <= 0:
        st.error("⚠️ Quantidade deve ser maior que zero.")
        return False
    return True

st.title("🧾 FAST")

tabs = st.tabs(["📋 Lançamentos Padaria", "🥩 Transformações Carne"])

with tabs[0]:
    st.subheader("Registro de Lançamentos da Padaria")
    with st.form("form_padaria", clear_on_submit=True):
        col1, col2, col3 = st.columns([1.5,3,1])
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

        if st.form_submit_button("Salvar"):
            if validar_codigo(codigo) and validar_quantidade(quantidade):
                try:
                    cursor.execute("""
                    INSERT INTO padaria (data, codigo, descricao, quantidade, unidade, motivo, lote)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (str(date.today()), codigo, descricao, quantidade, unidade, motivo, lote))
                    conn.commit()
                    st.success("Registro salvo com sucesso!")
                    carregar_produtos()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Por favor corrija os erros acima antes de salvar.")

    st.markdown("### 📅 Registros de Hoje")
    df_padaria = pd.read_sql(f"SELECT * FROM padaria WHERE data = '{date.today()}'", conn)
    st.dataframe(df_padaria, use_container_width=True)

    def exportar_padaria_detalhado():
        df = pd.read_sql("SELECT * FROM padaria", conn)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output

    def exportar_padaria_total():
        df = pd.read_sql("SELECT * FROM padaria", conn)
        resumo = df.groupby("descricao")["quantidade"].sum().reset_index()
        output = io.BytesIO()
        resumo.to_excel(output, index=False)
        output.seek(0)
        return output

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Baixar Excel Detalhado", exportar_padaria_detalhado(),
                           file_name="padaria_detalhado.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button("📥 Baixar Excel Total por Produto", exportar_padaria_total(),
                           file_name="padaria_total.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tabs[1]:
    st.subheader("Registro de Transformações de Carne")
    with st.form("form_carnes", clear_on_submit=True):
        col1, col2, col3 = st.columns([1.5,3,1])
        with col1:
            codigo_origem = st.text_input("Código origem").strip()
        with col2:
            descricao_origem = buscar_descricao(codigo_origem)
            st.text_input("Descrição origem", value=descricao_origem, disabled=True)
        with col3:
            quantidade = st.number_input("Quantidade", min_value=0.01, step=0.01, key="qtd_carnes")

        col4, col5, col6 = st.columns([1.5,3,1])
        with col4:
            codigo_destino = st.text_input("Código destino").strip()
        with col5:
            descricao_destino = buscar_descricao(codigo_destino)
            st.text_input("Descrição destino", value=descricao_destino, disabled=True)
        with col6:
            unidade = st.selectbox("Unidade", ["kg", "un"], key="un_carnes")

        lote = st.text_input("Lote", key="lote_carnes")

        if st.form_submit_button("Salvar"):
            if (validar_codigo(codigo_origem) and validar_codigo(codigo_destino) and
                validar_quantidade(quantidade)):
                try:
                    cursor.execute("""
                    INSERT INTO carnes (data, codigo, descricao, codigo_destino, descricao_destino, quantidade, unidade, lote)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(date.today()), codigo_origem, descricao_origem, codigo_destino, descricao_destino, quantidade, unidade, lote))
                    conn.commit()
                    st.success("Transformação registrada com sucesso!")
                    carregar_produtos()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Por favor corrija os erros acima antes de salvar.")

    st.markdown("### 📅 Transformações de Hoje")
    df_carnes = pd.read_sql(f"SELECT * FROM carnes WHERE data = '{date.today()}'", conn)
    st.dataframe(df_carnes, use_container_width=True)

    def exportar_carnes_detalhado():
        df = pd.read_sql("SELECT * FROM carnes", conn)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output

    def exportar_carnes_total():
        df = pd.read_sql("SELECT * FROM carnes", conn)
        resumo = df.groupby("descricao_destino")["quantidade"].sum().reset_index()
        output = io.BytesIO()
        resumo.to_excel(output, index=False)
        output.seek(0)
        return output

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Baixar Excel Detalhado", exportar_carnes_detalhado(),
                           file_name="carnes_detalhado.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button("📥 Baixar Excel Total por Produto", exportar_carnes_total(),
                           file_name="carnes_total.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
