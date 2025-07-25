import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

st.set_page_config(page_title="FAST", layout="wide")

# Estilo azul/vermelho simples
st.markdown(
    """
    <style>
    h1, h2, h3 { color: #0b5394; }
    .stButton>button { background-color: #c1121f; color: white; }
    .stButton>button:hover { background-color: #a10f19; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== Banco =====
conn = sqlite3.connect('produtos.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY,
    descricao TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    codigo TEXT,
    descricao TEXT,
    quantidade REAL,
    unidade TEXT,
    motivo TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS transformacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    codigo_origem TEXT,
    descricao_origem TEXT,
    quantidade REAL,
    unidade TEXT,
    codigo_destino TEXT,
    descricao_destino TEXT
)
""")
conn.commit()

# ===== Funções =====
def buscar_descricao(codigo):
    cursor.execute("SELECT descricao FROM produtos WHERE codigo = ?", (codigo,))
    result = cursor.fetchone()
    return result[0] if result else ""

def cadastrar_produto(codigo, descricao):
    cursor.execute("INSERT OR IGNORE INTO produtos (codigo, descricao) VALUES (?, ?)", (codigo, descricao))
    conn.commit()

def salvar_lancamento(data, codigo, descricao, qtd, unidade, motivo):
    cursor.execute("""
        INSERT INTO lancamentos (data, codigo, descricao, quantidade, unidade, motivo)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (data, codigo, descricao, qtd, unidade, motivo))
    conn.commit()

def salvar_transformacao(data, cod_ori, desc_ori, qtd, unidade, cod_dest, desc_dest):
    cursor.execute("""
        INSERT INTO transformacoes (data, codigo_origem, descricao_origem, quantidade, unidade, codigo_destino, descricao_destino)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data, cod_ori, desc_ori, qtd, unidade, cod_dest, desc_dest))
    conn.commit()

# Inicializa session_state para os campos se não existirem
for key in ["codigo_padaria", "descricao_padaria", "qtd_padaria", "unidade_padaria", "motivo_padaria",
            "codigo_transf_ori", "descricao_transf_ori", "qtd_transf", "unidade_transf",
            "codigo_transf_dest", "descricao_transf_dest"]:
    if key not in st.session_state:
        # Valores padrão
        if key in ["qtd_padaria", "qtd_transf"]:
            st.session_state[key] = 0.0
        elif key in ["unidade_padaria", "unidade_transf"]:
            st.session_state[key] = "kg"
        elif key == "motivo_padaria":
            st.session_state[key] = "Avaria"
        else:
            st.session_state[key] = ""

st.title("📦 FAST - Gestão de Lançamentos")

abas = st.tabs(["🥖 Lançamentos Padaria", "🥩 Transformações de Carne", "📁 Base de Produtos", "📊 Relatórios"])

# ------ Aba 1: Padaria ------
with abas[0]:
    st.subheader("🥖 Lançamentos da Padaria")
    with st.form("form_padaria", clear_on_submit=False):
        codigo = st.text_input("Código do produto", value=st.session_state["codigo_padaria"], key="codigo_padaria")
        buscar = st.form_submit_button("🔍 Buscar")
        if buscar and codigo:
            desc = buscar_descricao(codigo)
            if desc:
                st.session_state["descricao_padaria"] = desc
                st.success("Produto encontrado.")
            else:
                st.warning("Produto não encontrado. Preencha a descrição para cadastrar.")
                st.session_state["descricao_padaria"] = ""

        descricao = st.text_input("Descrição", value=st.session_state["descricao_padaria"], key="descricao_padaria")
        qtd = st.number_input("Quantidade", min_value=0.0, step=0.1, value=st.session_state["qtd_padaria"], key="qtd_padaria")
        unidade = st.selectbox("Unidade", ["kg", "un"], index=["kg", "un"].index(st.session_state["unidade_padaria"]), key="unidade_padaria")
        motivo = st.selectbox("Motivo", ["Avaria", "Doação", "Refeitório", "Inventário"], index=["Avaria", "Doação", "Refeitório", "Inventário"].index(st.session_state["motivo_padaria"]), key="motivo_padaria")

        salvar = st.form_submit_button("✅ Salvar Lançamento")
        if salvar:
            if not codigo or not descricao:
                st.error("Preencha código e descrição!")
            else:
                cadastrar_produto(codigo, descricao)
                salvar_lancamento(datetime.today().strftime("%Y-%m-%d"), codigo, descricao, qtd, unidade, motivo)
                st.success("Lançamento salvo com sucesso!")

                # Limpa campos no session_state para atualizar inputs na próxima interação
                st.session_state["codigo_padaria"] = ""
                st.session_state["descricao_padaria"] = ""
                st.session_state["qtd_padaria"] = 0.0
                st.session_state["unidade_padaria"] = "kg"
                st.session_state["motivo_padaria"] = "Avaria"

# ------ Aba 2: Transformações ------
with abas[1]:
    st.subheader("🥩 Transformações de Carne Bovina")
    with st.form("form_transformacoes", clear_on_submit=False):
        codigo_ori = st.text_input("Código origem", value=st.session_state["codigo_transf_ori"], key="codigo_transf_ori")
        buscar_ori = st.form_submit_button("🔍 Buscar Origem")
        if buscar_ori and codigo_ori:
            desc_ori = buscar_descricao(codigo_ori)
            if desc_ori:
                st.session_state["descricao_transf_ori"] = desc_ori
                st.success("Produto origem encontrado.")
            else:
                st.warning("Produto origem não encontrado. Preencha a descrição para cadastrar.")
                st.session_state["descricao_transf_ori"] = ""

        descricao_ori = st.text_input("Descrição origem", value=st.session_state["descricao_transf_ori"], key="descricao_transf_ori")
        qtd = st.number_input("Quantidade", min_value=0.0, step=0.1, value=st.session_state["qtd_transf"], key="qtd_transf")
        unidade = st.selectbox("Unidade", ["kg", "un"], index=["kg", "un"].index(st.session_state["unidade_transf"]), key="unidade_transf")

        codigo_dest = st.text_input("Código destino", value=st.session_state["codigo_transf_dest"], key="codigo_transf_dest")
        buscar_dest = st.form_submit_button("🔍 Buscar Destino")
        if buscar_dest and codigo_dest:
            desc_dest = buscar_descricao(codigo_dest)
            if desc_dest:
                st.session_state["descricao_transf_dest"] = desc_dest
                st.success("Produto destino encontrado.")
            else:
                st.warning("Produto destino não encontrado. Preencha a descrição para cadastrar.")
                st.session_state["descricao_transf_dest"] = ""

        descricao_dest = st.text_input("Descrição destino", value=st.session_state["descricao_transf_dest"], key="descricao_transf_dest")

        salvar = st.form_submit_button("✅ Salvar Transformação")
        if salvar:
            if not codigo_ori or not descricao_ori or not codigo_dest or not descricao_dest:
                st.error("Preencha todos os campos!")
            else:
                cadastrar_produto(codigo_ori, descricao_ori)
                cadastrar_produto(codigo_dest, descricao_dest)
                salvar_transformacao(datetime.today().strftime("%Y-%m-%d"), codigo_ori, descricao_ori, qtd, unidade, codigo_dest, descricao_dest)
                st.success("Transformação salva com sucesso!")

                # Limpa campos
                st.session_state["codigo_transf_ori"] = ""
                st.session_state["descricao_transf_ori"] = ""
                st.session_state["qtd_transf"] = 0.0
                st.session_state["unidade_transf"] = "kg"
                st.session_state["codigo_transf_dest"] = ""
                st.session_state["descricao_transf_dest"] = ""

# ------ Aba 3: Base de Produtos ------
with abas[2]:
    st.subheader("📁 Upload da Base de Produtos")
    uploaded_file = st.file_uploader("Faça upload do Excel com colunas 'codigo' e 'descricao'", type=['xlsx', 'xls'])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            if 'codigo' in df.columns and 'descricao' in df.columns:
                df.to_sql('produtos', conn, if_exists='replace', index=False)
                st.success("Base de produtos carregada e salva no banco com sucesso!")
            else:
                st.error("O arquivo deve conter as colunas 'codigo' e 'descricao'.")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

    st.write("Base atual de produtos:")
    df_produtos = pd.read_sql_query("SELECT * FROM produtos ORDER BY codigo", conn)
    st.dataframe(df_produtos)

# ------ Aba 4: Relatórios ------
with abas[3]:
    st.subheader("📊 Relatórios de Lançamentos")
    df_lanc = pd.read_sql_query("SELECT * FROM lancamentos ORDER BY data DESC", conn)
    st.dataframe(df_lanc)

    if not df_lanc.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_lanc.to_excel(writer, sheet_name='Detalhado', index=False)
            total_motivo = df_lanc.groupby('motivo')['quantidade'].sum().reset_index()
            total_motivo.rename(columns={'quantidade': 'Quantidade Total'}, inplace=True)
            total_motivo.to_excel(writer, sheet_name='Total por Motivo', index=False)
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Baixar Excel dos lançamentos",
            data=processed_data,
            file_name="lancamentos_fast.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.subheader("📊 Relatórios de Transformações")
    df_transf = pd.read_sql_query("SELECT * FROM transformacoes ORDER BY data DESC", conn)
    st.dataframe(df_transf)

    if not df_transf.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_transf.to_excel(writer, sheet_name='Detalhado', index=False)
            total_dest = df_transf.groupby('codigo_destino')['quantidade'].sum().reset_index()
            total_dest.rename(columns={'quantidade': 'Quantidade Total'}, inplace=True)
            total_dest.to_excel(writer, sheet_name='Total por Código Destino', index=False)
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Baixar Excel das transformações",
            data=processed_data,
            file_name="transformacoes_fast.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
