import streamlit as st

st.set_page_config(
    page_title="World Cup 2026 Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚽ World Cup 2026 Analytics")
st.markdown(
    """
    Análise de dados da Copa do Mundo FIFA 2026 — histórico por nação, estatísticas
    de jogadores convocados e indicadores do Brasil.

    **Navegue pelas páginas na barra lateral.**
    """
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Nações participantes", "48")
col2.metric("Edições analisadas", "22")
col3.metric("Países sede", "3 (EUA, CAN, MEX)")
col4.metric("Jogos na fase de grupos", "104")
