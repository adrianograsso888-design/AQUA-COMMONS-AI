import streamlit as st

st.set_page_config(
    page_title="AQUA COMMONS AI",
    page_icon="💧",
    layout="wide"
)

st.title("AQUA COMMONS AI")

st.subheader(
    "Water Resource Management & Decision Support Platform"
)

st.write(
    "Una piattaforma per supportare le amministrazioni "
    "nella gestione e nell'allocazione delle risorse idriche."
)

st.info(
    "Prototype in development — Brenta-Bacchiglione pilot area"
)

st.markdown("### Platform modules")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 01 · Water Dashboard")
    st.write("Disponibilità idrica, domanda e indicatori territoriali.")

    st.markdown("#### 02 · Allocation Simulator")
    st.write("Simulazione e confronto di strategie di allocazione.")

with col2:
    st.markdown("#### 03 · Impact Analysis")
    st.write("Valutazione degli impatti economici, sociali e ambientali.")

    st.markdown("#### 04 · Decision Report")
    st.write("Generazione di report a supporto delle decisioni.")
