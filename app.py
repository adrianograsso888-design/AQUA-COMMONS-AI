
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AQUA COMMONS AI",
    page_icon="💧",
    layout="wide"
)

# =====================================================
# CONFIGURAZIONE E STILE
# =====================================================

SECTORS = [
    "Agricoltura",
    "Usi civili",
    "Industria",
    "Ambiente"
]

DEFAULT_DEMAND = {
    "Agricoltura": 70.0,
    "Usi civili": 25.0,
    "Industria": 15.0,
    "Ambiente": 15.0
}

DEFAULT_MINIMUM = {
    "Agricoltura": 30.0,
    "Usi civili": 25.0,
    "Industria": 5.0,
    "Ambiente": 15.0
}

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
div[data-testid="stMetric"] {
    background-color: white;
    padding: 16px;
    border-radius: 10px;
    border: 1px solid #E0E8EF;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# FUNZIONI DI ALLOCAZIONE
# =====================================================

def proportional_allocation(availability, demands, minimums):

    allocations = minimums.copy()
    remaining = availability - sum(allocations.values())

    capacities = {
        sector: max(0, demands[sector] - minimums[sector])
        for sector in SECTORS
    }

    total_capacity = sum(capacities.values())

    if remaining > 0 and total_capacity > 0:
        for sector in SECTORS:
            extra = remaining * capacities[sector] / total_capacity
            allocations[sector] += min(extra, capacities[sector])

    return allocations


def priority_allocation(availability, demands, minimums, priority):

    allocations = minimums.copy()
    remaining = availability - sum(allocations.values())

    for sector in priority:
        capacity = max(0, demands[sector] - allocations[sector])
        extra = min(remaining, capacity)

        allocations[sector] += extra
        remaining -= extra

    return allocations


def calculate_results(demands, allocations):

    rows = []

    for sector in SECTORS:
        demand = demands[sector]
        allocated = allocations[sector]
        shortage = max(0, demand - allocated)

        satisfaction = (
            allocated / demand * 100
            if demand > 0 else 100
        )

        rows.append({
            "Settore": sector,
            "Domanda (hm³)": demand,
            "Acqua assegnata (hm³)": round(allocated, 2),
            "Deficit (hm³)": round(shortage, 2),
            "Fabbisogno soddisfatto (%)": round(satisfaction, 1)
        })

    return pd.DataFrame(rows)


# =====================================================
# NAVIGAZIONE
# =====================================================

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
st.sidebar.caption("TERRITORIO PILOTA")
st.sidebar.write("Bacino Brenta–Bacchiglione")
st.sidebar.write("Veneto, Italia")
st.sidebar.divider()
st.sidebar.caption("PROTOTIPO DIMOSTRATIVO")


# =====================================================
# 01 - WATER DASHBOARD
# =====================================================

if page == "Water Dashboard":

    st.title("Water Dashboard")

    st.write(
        "Panoramica della disponibilità idrica, "
        "della domanda e delle condizioni territoriali."
    )

    st.info(
        "PROTOTIPO — I valori visualizzati sono simulati "
        "e non rappresentano misurazioni ufficiali "
        "del bacino Brenta–Bacchiglione."
    )

    available = 100.0
    total_demand = sum(DEFAULT_DEMAND.values())
    deficit = max(0, total_demand - available)

    coverage = (
        available / total_demand * 100
        if total_demand > 0 else 0
    )

    st.subheader("Indicatori principali")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Disponibilità idrica", "100 hm³")
    c2.metric("Domanda complessiva", "125 hm³")
    c3.metric("Deficit teorico", "25 hm³")
    c4.metric("Copertura domanda", f"{coverage:.1f}%")

    st.divider()

    st.subheader("Fabbisogno per settore")

    demand_df = pd.DataFrame({
        "Settore": SECTORS,
        "Fabbisogno (hm³)": [
            DEFAULT_DEMAND[s] for s in SECTORS
        ]
    })

    left, right = st.columns([1.4, 1])

    with left:
        st.bar_chart(
            demand_df.set_index("Settore")
        )

    with right:
        st.dataframe(
            demand_df,
            hide_index=True,
            use_container_width=True
        )

    st.subheader("Copertura complessiva")

    st.progress(min(coverage / 100, 1.0))

    st.write(f"Copertura: {coverage:.1f}%")
    st.write(f"Domanda non coperta: {deficit:.1f} hm³")


# =====================================================
# 02 - ALLOCATION SIMULATOR
# =====================================================

elif page == "Allocation Simulator":

    st.title("Allocation Simulator")

    st.write(
        "Modifica la disponibilità idrica, i fabbisogni "
        "e i vincoli minimi per confrontare strategie "
        "alternative di allocazione."
    )

    st.info(
        "PROTOTIPO — Tutti i valori iniziali sono simulati. "
        "Le quote minime sono ipotesi dello scenario, "
        "non soglie normative ufficiali."
    )

    st.subheader("1. Parametri dello scenario")

    availability = st.number_input(
        "Disponibilità idrica totale (hm³)",
        min_value=0.0,
        max_value=1000.0,
        value=100.0,
        step=5.0
    )

    st.markdown("#### Fabbisogni e quote minime")

    demands = {}
    minimums = {}

    header = st.columns([2, 1, 1])

    header[0].markdown("**Settore**")
    header[1].markdown("**Domanda (hm³)**")
    header[2].markdown("**Quota minima (hm³)**")

    for sector in SECTORS:

        cols = st.columns([2, 1, 1])

        demands[sector] = cols[1].number_input(
            f"Domanda {sector}",
            min_value=0.0,
            max_value=1000.0,
            value=DEFAULT_DEMAND[sector],
            step=1.0,
            key=f"demand_{sector}",
            label_visibility="collapsed"
        )

        minimums[sector] = cols[2].number_input(
            f"Minimo {sector}",
            min_value=0.0,
            max_value=demands[sector],
            value=min(
                DEFAULT_MINIMUM[sector],
                demands[sector]
            ),
            step=1.0,
            key=f"minimum_{sector}",
            label_visibility="collapsed"
        )

        cols[0].write(sector)

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())

    st.divider()

    m1, m2, m3 = st.columns(3)

    m1.metric("Disponibilità", f"{availability:.1f} hm³")
    m2.metric("Domanda totale", f"{total_demand:.1f} hm³")
    m3.metric("Quote minime richieste", f"{total_minimum:.1f} hm³")

    # Verifica di fattibilità dei vincoli

    if total_minimum > availability:

        st.error(
            "SCENARIO NON FATTIBILE: le quote minime "
            "richieste superano la disponibilità idrica. "
            "Occorre rivedere le ipotesi o aumentare "
            "la disponibilità."
        )

    else:

        st.success(
            "Vincoli minimi compatibili con la disponibilità idrica."
        )

        st.subheader("2. Definizione delle priorità")

        st.write(
            "Scegli l'ordine con cui assegnare l'acqua "
            "nella strategia per priorità."
        )

        priority = []
        remaining_sectors = SECTORS.copy()

        for i in range(4):

            selected = st.selectbox(
                f"Priorità {i + 1}",
                options=remaining_sectors,
                index=0,
                key=f"priority_{i}"
            )

            priority.append(selected)
            remaining_sectors.remove(selected)

        st.divider()

        st.subheader("3. Risultati della simulazione")

        proportional = proportional_allocation(
            availability,
            demands,
            minimums
        )

        priority_result = priority_allocation(
            availability,
            demands,
            minimums,
            priority
        )

        prop_df = calculate_results(
            demands,
            proportional
        )

        priority_df = calculate_results(
            demands,
            priority_result
        )

        tab1, tab2 = st.tabs([
            "Allocazione proporzionale",
            "Allocazione per priorità"
        ])

        with tab1:

            st.markdown("#### Strategia proporzionale")

            st.write(
                "L'acqua residua dopo il rispetto delle quote "
                "minime viene distribuita in proporzione "
                "ai fabbisogni ancora insoddisfatti."
            )

            st.dataframe(
                prop_df,
                hide_index=True,
                use_container_width=True
            )

            st.bar_chart(
                prop_df.set_index("Settore")[
                    ["Domanda (hm³)", "Acqua assegnata (hm³)"]
                ]
            )

        with tab2:

            st.markdown("#### Strategia per priorità")

            st.write(
                "Dopo il rispetto delle quote minime, "
                "l'acqua residua viene assegnata seguendo "
                "l'ordine scelto dall'utente."
            )

            st.dataframe(
                priority_df,
                hide_index=True,
                use_container_width=True
            )

            st.bar_chart(
                priority_df.set_index("Settore")[
                    ["Domanda (hm³)", "Acqua assegnata (hm³)"]
                ]
            )

        st.divider()

        st.subheader("4. Confronto tra strategie")

        comparison = pd.DataFrame({
            "Settore": SECTORS,
            "Deficit proporzionale (hm³)": [
                round(
                    max(0, demands[s] - proportional[s]), 2
                )
                for s in SECTORS
            ],
            "Deficit per priorità (hm³)": [
                round(
                    max(0, demands[s] - priority_result[s]), 2
                )
                for s in SECTORS
            ]
        })

        st.dataframe(
            comparison,
            hide_index=True,
            use_container_width=True
        )

        total_prop_deficit = sum(
            max(0, demands[s] - proportional[s])
            for s in SECTORS
        )

        total_priority_deficit = sum(
            max(0, demands[s] - priority_result[s])
            for s in SECTORS
        )

        a, b = st.columns(2)

        a.metric(
            "Deficit totale - proporzionale",
            f"{total_prop_deficit:.2f} hm³"
        )

        b.metric(
            "Deficit totale - per priorità",
            f"{total_priority_deficit:.2f} hm³"
        )

        st.caption(
            "Le strategie sono strumenti di confronto, "
            "non raccomandazioni automatiche. "
            "La distribuzione effettiva deve rispettare "
            "la normativa e le competenze delle autorità."
        )


# =====================================================
# 03 - IMPACT ANALYSIS
# =====================================================

elif page == "Impact Analysis":

    st.title("Impact Analysis")

    st.write(
        "Analisi delle conseguenze economiche, sociali "
        "e ambientali degli scenari di allocazione."
    )

    st.info(
        "Modulo in fase di sviluppo. "
        "Sarà collegato ai risultati dell'Allocation Simulator."
    )


# =====================================================
# 04 - DECISION REPORT
# =====================================================

elif page == "Decision Report":

    st.title("Decision Report")

    st.write(
        "Organizzazione dei risultati e preparazione "
        "di un report a supporto delle decisioni pubbliche."
    )

    st.info(
        "Modulo in fase di sviluppo. "
        "Sarà collegato ai risultati delle simulazioni "
        "e dell'Impact Analysis."
    )
