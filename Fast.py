import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO  # se você não usar BytesIO em outro ponto, pode remover esta linha

st.set_page_config(page_title="FAST", layout="wide")

# ========== CONEXÕES ==========
conn = sqlite3.connect("produtos.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY,
    descricao TEXT
)
""")
conn.commit()

conn_padaria = sqlite3.connect("padaria.db", check_same_thread=False)
cursor_padaria = conn_padaria.cursor()
cursor_padaria.execute("""
CREATE TABLE IF NOT EXISTS padaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    codigo TEXT,
    descricao TEXT,
    quantidade REAL,
    unidade TEXT,
    motivo TEXT
)
""")
conn_padaria.commit()

# ========== FUNÇÕES ==========
def buscar_descricao(codigo):
    cursor.execute("SELECT descricao FROM produtos WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else ""

def cadastrar_produto(codigo, descricao):
    try:
        cursor.execute("INSERT OR IGNORE INTO produtos (codigo, descricao) VALUES (?, ?)", (codigo, descricao))
        conn.commit()
    except sqlite3.OperationalError as e:
        st.error(f"Erro ao cadastrar produto: {e}")

def salvar_lancamento(data, codigo, descricao, quantidade, unidade, motivo):
    try:
        cursor_padaria.execute("""
            INSERT INTO padaria (data, codigo, descricao, quantidade, unidade, motivo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data, codigo, descricao, quantidade, unidade, motivo))
        conn_padaria.commit()
    except sqlite3.OperationalError as e:
        st.error(f"Erro ao salvar lançamento: {e}")

def excluir_lancamento_padaria(id_lanc):
    cursor_padaria.execute("DELETE FROM padaria WHERE id = ?", (id_lanc,))
    conn_padaria.commit()

# ========== LAYOUT ==========
st.image("logo.png", width=120)
st.title("📦 FAST - Lançamentos e Transformações")
aba = st.sidebar.radio("Escolha a área:", ["Lançamentos da padaria", "Transformações de carne bovina"])

# ========== ABA PADARIA ==========
if aba == "Lançamentos da padaria":
    st.header("🥖 Lançamentos da Padaria")
    with st.form("form_padaria"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data = st.date_input("Data", value=date.today())
        with col2:
            codigo = st.text_input("Código do produto")
        with col3:
            if codigo:
                descricao = buscar_descricao(codigo)
            else:
                descricao = ""
            descricao = st.text_input("Descrição", value=descricao)

        col4, col5, col6 = st.columns(3)
        with col4:
            quantidade = st.number_input("Quantidade", min_value=0.01, step=0.01)
        with col5:
            unidade = st.selectbox("Unidade", ["kg", "un"])
        with col6:
            motivo = st.selectbox("Motivo", ["Avaria", "Doação", "Refeitório", "Inventário"])

        submitted = st.form_submit_button("Salvar lançamento")
        if submitted and codigo and descricao:
            cadastrar_produto(codigo, descricao)
            salvar_lancamento(str(data), codigo, descricao, quantidade, unidade, motivo)
            st.success("Lançamento salvo com sucesso!")

    st.subheader("📄 Registros")
    df_padaria = pd.read_sql_query("SELECT * FROM padaria ORDER BY data DESC", conn_padaria)
    st.dataframe(df_padaria, use_container_width=True)

    # Botão para excluir
    if not df_padaria.empty:
        id_excluir = st.selectbox("Excluir lançamento (selecione o ID):", options=df_padaria["id"])
        if st.button("Excluir"):
            excluir_lancamento_padaria(id_excluir)
            st.success("Registro excluído com sucesso!")
            st.experimental_rerun()

    # ======= EXPORTAÇÃO ATUALIZADA: 3 abas no Excel =======
    if not df_padaria.empty:
        # 1) Total por motivo (soma da quantidade por motivo)
        total_por_motivo = (
            df_padaria.groupby("motivo", as_index=False)["quantidade"]
            .sum()
            .rename(columns={"quantidade": "total_quantidade"})
        )

        # 2) Total por produto (código + descrição), independente do motivo
        total_por_produto = (
            df_padaria.groupby(["codigo", "descricao"], as_index=False)["quantidade"]
            .sum()
            .rename(columns={"quantidade": "total_quantidade"})
        )

        # Gera o arquivo Excel em disco (mantendo seu padrão)
        with pd.ExcelWriter("lancamentos_padaria.xlsx", engine="xlsxwriter") as writer:
            df_padaria.to_excel(writer, index=False, sheet_name="Detalhado")
            total_por_motivo.to_excel(writer, index=False, sheet_name="Total por Motivo")
            total_por_produto.to_excel(writer, index=False, sheet_name="Total por Produto")

        with open("lancamentos_padaria.xlsx", "rb") as f:
            st.download_button(
                "📥 Baixar Excel (Detalhado + Totais)",
                f,
                file_name="lancamentos_padaria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ========== ABA TRANSFORMAÇÕES ==========
elif aba == "Transformações de carne bovina":
    st.header("🥩 Transformações de Carne Bovina")
    st.info("(Sem alterações aqui — você só pediu mudança na exportação da padaria.)")
