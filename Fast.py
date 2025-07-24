import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="FAST", layout="wide")

# ========== TÍTULO ==========
st.markdown("<h1 style='text-align: center; color: red;'>FAST - Controle Padaria e Transformações</h1>", unsafe_allow_html=True)

# ========== FUNÇÕES ==========
def init_db():
    with sqlite3.connect("produtos.db") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS produtos (codigo TEXT PRIMARY KEY, descricao TEXT)""")
    with sqlite3.connect("lancamentos.db") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS lancamentos_padaria (data TEXT, codigo TEXT, descricao TEXT, quantidade TEXT, motivo TEXT)""")
    with sqlite3.connect("transformacoes.db") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS transformacoes_carne (data TEXT, codigo_origem TEXT, descricao TEXT, quantidade TEXT, codigo_destino TEXT)""")

def cadastrar_produto(codigo, descricao):
    with sqlite3.connect("produtos.db") as conn:
        conn.execute("INSERT OR IGNORE INTO produtos (codigo, descricao) VALUES (?, ?)", (codigo, descricao))

def buscar_descricao(codigo):
    with sqlite3.connect("produtos.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT descricao FROM produtos WHERE codigo = ?", (codigo,))
        result = cur.fetchone()
        return result[0] if result else ""

def salvar_lancamento_padaria(data, codigo, descricao, quantidade, motivo):
    with sqlite3.connect("lancamentos.db") as conn:
        conn.execute("INSERT INTO lancamentos_padaria VALUES (?, ?, ?, ?, ?)", (data, codigo, descricao, quantidade, motivo))

def salvar_transformacao_carne(data, codigo_origem, descricao, quantidade, codigo_destino):
    with sqlite3.connect("transformacoes.db") as conn:
        conn.execute("INSERT INTO transformacoes_carne VALUES (?, ?, ?, ?, ?)", (data, codigo_origem, descricao, quantidade, codigo_destino))

def obter_lancamentos_padaria():
    with sqlite3.connect("lancamentos.db") as conn:
        df = pd.read_sql_query("SELECT * FROM lancamentos_padaria", conn)
    return df

def obter_transformacoes_carne():
    with sqlite3.connect("transformacoes.db") as conn:
        df = pd.read_sql_query("SELECT * FROM transformacoes_carne", conn)
    return df

# ========== INTERFACE ==========
init_db()
aba = st.sidebar.selectbox("Escolha uma aba", ["Lançamentos Padaria", "Transformações Carne"])

if aba == "Lançamentos Padaria":
    st.subheader("Lançamentos da Padaria")
    data = st.date_input("Data", value=datetime.today())
    codigo = st.text_input("Código do produto")
    descricao = buscar_descricao(codigo)
    st.text_input("Descrição", value=descricao, disabled=True)

    # CAMPO QUANTIDADE COM TRATAMENTO
    quantidade_raw = st.text_input("Quantidade (kg ou un)")
    quantidade = ''.join([c for c in quantidade_raw if c.isdigit() or c == '.' or c == ',']).replace(',', '.')

    motivo = st.selectbox("Motivo", ["Avaria", "Doação", "Refeitório", "Inventário"])

    if st.button("Salvar Lançamento"):
        if codigo and quantidade:
            cadastrar_produto(codigo, descricao)
            salvar_lancamento_padaria(str(data), codigo, descricao, quantidade, motivo)
            st.success("Lançamento salvo com sucesso.")
        else:
            st.warning("Preencha todos os campos obrigatórios.")

    st.markdown("---")
    st.subheader("Registros Salvos")
    df = obter_lancamentos_padaria()
    st.dataframe(df)

    # Exportar Excel com 3 abas
    if not df.empty:
        if st.button("📥 Exportar Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # TRATAR QUANTIDADE
                df["quantidade"] = df["quantidade"].astype(str).str.replace(',', '.')
                df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)

                # Aba 1: Detalhado
                df.to_excel(writer, sheet_name='Detalhado', index=False)

                # Aba 2: Total por Motivo
                df.groupby("motivo")["quantidade"].sum().reset_index(name="Total").to_excel(writer, sheet_name='Total por Motivo', index=False)

                # Aba 3: Total por Produto
                df.groupby(["codigo", "descricao"])["quantidade"].sum().reset_index(name="Total").to_excel(writer, sheet_name='Total por Produto', index=False)

            st.download_button(
                "Clique para baixar",
                data=output.getvalue(),
                file_name="lancamentos_padaria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

elif aba == "Transformações Carne":
    st.subheader("Transformações de Carne Bovina")
    data = st.date_input("Data", value=datetime.today(), key="carne")
    codigo_origem = st.text_input("Código do produto de origem")
    descricao = buscar_descricao(codigo_origem)
    st.text_input("Descrição", value=descricao, disabled=True, key="desc2")
    quantidade = st.text_input("Quantidade (kg)", key="qtd2")
    codigo_destino = st.text_input("Código do produto de destino")

    if st.button("Salvar Transformação"):
        if codigo_origem and quantidade and codigo_destino:
            cadastrar_produto(codigo_origem, descricao)
            salvar_transformacao_carne(str(data), codigo_origem, descricao, quantidade, codigo_destino)
            st.success("Transformação salva com sucesso.")
        else:
            st.warning("Preencha todos os campos obrigatórios.")

    st.markdown("---")
    st.subheader("Registros Salvos")
    df = obter_transformacoes_carne()
    st.dataframe(df)

    # Exportar Excel com 2 abas
    if not df.empty:
        if st.button("📥 Exportar Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Detalhado', index=False)
                df.groupby("codigo_destino")["quantidade"].count().reset_index(name="Total").to_excel(writer, sheet_name='Total por Código Destino', index=False)
            st.download_button("Clique para baixar", data=output.getvalue(), file_name="transformacoes_carne.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
