
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AQUA COMMONS AI",
    page_icon="💧",
    layout="wide"
)

# -------------------------
# DESIGN
# -------------------------

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FA;
}
section[data-testid="stSidebar"] {
    background-color: #102B40;
}
section[data-testid="stSidebar"] * {
    color: white;
}
h1, h2, h3 {
    color: #123B56;
}
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #E0E8EF;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# NAVIGATION
# -------------------------

st.sidebar.title("💧 AQUA COMMONS AI")
st.sidebar.caption("WATER MANAGEMENT PLATFORM")

page = st.sidebar.radio(
    "NAVIGAZIONE",
    [
        "Water Dashboard",
        "Allocation Simulator",
        "Impact Analysis",
        "Decision Report"
    ]
)

st.sidebar.divider()
st.sidebar.caption("PILOT TERRITORY")
st.sidebar.write("Brenta–Bacchiglione")
st.sidebar.caption("Veneto, Italia")

# -------------------------
# WATER DASHBOARD
# -------------------------

if page == "Water Dashboard":

    st.title("Water Dashboard")
    st.write(
        "Panoramica della disponibilità idrica, "
        "della domanda e delle condizioni territoriali."
    )

    st.info(
        "PROTOTIPO — I valori mostrati in questa prima "
        "versione sono dati simulati a scopo dimostrativo, "
        "non misurazioni ufficiali del bacino."
    )

    # Scenario dimostrativo
    available_water = 100
    total_demand = 125
    water_deficit = total_demand - available_water
    stress_level = water_deficit / total_demand * 100

    st.subheader("Indicatori principali")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Disponibilità idrica",
        f"{available_water} hm³"
    )

    col2.metric(
        "Domanda complessiva",
        f"{total_demand} hm³"
    )

    col3.metric(
        "Deficit idrico",
        f"{water_deficit} hm³"
    )

    col4.metric(
        "Domanda non coperta",
        f"{stress_level:.1f}%"
    )

    st.divider()

    st.subheader("Distribuzione della domanda")

    sector_data = pd.DataFrame({
        "Settore": [
            "Agricoltura",
            "Usi civili",
            "Industria",
            "Ambiente"
        ],
        "Fabbisogno (hm³)": [70, 25, 15, 15]
    })

    left, right = st.columns([1.4, 1])

    with left:
        st.bar_chart(
            sector_data.set_index("Settore"),
            y="Fabbisogno (hm³)"
        )

    with right:
        st.markdown("#### Fabbisogno per settore")
        st.dataframe(
            sector_data,
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    st.subheader("Stato della risorsa")

    st.write(
        "La disponibilità simulata non è sufficiente "
        "a coprire integralmente la domanda complessiva."
    )

    st.progress(available_water / total_demand)

    st.caption(
        "Copertura della domanda: "
        f"{available_water / total_demand * 100:.1f}%"
    )

# -------------------------
# OTHER MODULES
# -------------------------

elif page == "Allocation Simulator":
    st.title("Allocation Simulator")
    st.info("Modulo in fase di sviluppo.")

elif page == "Impact Analysis":
    st.title("Impact Analysis")
    st.info("Modulo in fase di sviluppo.")

elif page == "Decision Report":
    st.title("Decision Report")
    st.info("Modulo in fase di sviluppo.")
