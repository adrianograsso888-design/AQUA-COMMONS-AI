
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AQUA COMMONS AI",
    page_icon="💧",
    layout="wide"
)

# =====================================================
# 1. CONFIGURAZIONE
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

# =====================================================
# 2. STILE
# =====================================================

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
# 3. FUNZIONI DI CALCOLO
# =====================================================

def proportional_allocation(availability, demands, minimums):

    allocations = minimums.copy()
    remaining = availability - sum(allocations.values())

    capacities = {
        sector: max(0, demands[sector] - minimums[sector])
        for sector in SECTORS
    }

    active_sectors = [
        sector for sector in SECTORS
        if capacities[sector] > 0
    ]

    while remaining > 0.000001 and active_sectors:

        total_capacity = sum(
            capacities[sector] for sector in active_sectors
        )

        if total_capacity <= 0:
            break

        distributed = 0.0
        next_active = []

        for sector in active_sectors:

            share = remaining * capacities[sector] / total_capacity
            extra = min(share, capacities[sector])

            allocations[sector] += extra
            capacities[sector] -= extra
            distributed += extra

            if capacities[sector] > 0.000001:
                next_active.append(sector)

        remaining -= distributed
        active_sectors = next_active

        if distributed <= 0.000001:
            break

    return allocations


def priority_allocation(availability, demands, minimums, priority):

    allocations = minimums.copy()
    remaining = availability - sum(allocations.values())

    for sector in priority:

        capacity = max(
            0,
            demands[sector] - allocations[sector]
        )

        extra = min(remaining, capacity)

        allocations[sector] += extra
        remaining -= extra

        if remaining <= 0:
            break

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
            "Domanda (hm³)": round(demand, 2),
            "Acqua assegnata (hm³)": round(allocated, 2),
            "Deficit (hm³)": round(shortage, 2),
            "Fabbisogno soddisfatto (%)": round(satisfaction, 1)
        })

    return pd.DataFrame(rows)


def get_scenario(availability, demands, minimums, priority, strategy):

    if strategy == "proporzionale":
        allocations = proportional_allocation(
            availability, demands, minimums
        )
    else:
        allocations = priority_allocation(
            availability, demands, minimums, priority
        )

    return calculate_results(demands, allocations), allocations


# =====================================================
# 4. NAVIGAZIONE
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
# 5. STATO CONDIVISO DEI PARAMETRI
# =====================================================

if "availability" not in st.session_state:
    st.session_state.availability = 100.0

for sector in SECTORS:

    demand_key = f"demand_{sector}"
    minimum_key = f"minimum_{sector}"

    if demand_key not in st.session_state:
        st.session_state[demand_key] = DEFAULT_DEMAND[sector]

    if minimum_key not in st.session_state:
        st.session_state[minimum_key] = DEFAULT_MINIMUM[sector]


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
        st.bar_chart(demand_df.set_index("Settore"))

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
        step=5.0,
        key="availability"
    )

    st.markdown("#### Fabbisogni e quote minime")

    demands = {}
    minimums = {}

    header = st.columns([2, 1, 1])
    header[0].markdown("**Settore**")
    header[1].markdown("**Domanda (hm³)**")
    header[2].markdown("**Quota minima (hm³)**")

    for sector in SECTORS:

        demand_key = f"demand_{sector}"
        minimum_key = f"minimum_{sector}"

        if st.session_state[minimum_key] > st.session_state[demand_key]:
            st.session_state[minimum_key] = st.session_state[demand_key]

        cols = st.columns([2, 1, 1])
        cols[0].write(sector)

        demands[sector] = cols[1].number_input(
            f"Domanda {sector}",
            min_value=0.0,
            max_value=1000.0,
            step=1.0,
            key=demand_key,
            label_visibility="collapsed"
        )

        minimums[sector] = cols[2].number_input(
            f"Minimo {sector}",
            min_value=0.0,
            max_value=demands[sector],
            step=1.0,
            key=minimum_key,
            label_visibility="collapsed"
        )

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())

    st.divider()

    m1, m2, m3 = st.columns(3)

    m1.metric("Disponibilità", f"{availability:.1f} hm³")
    m2.metric("Domanda totale", f"{total_demand:.1f} hm³")
    m3.metric("Quote minime richieste", f"{total_minimum:.1f} hm³")

    if total_minimum > availability:

        st.error(
            "SCENARIO NON FATTIBILE: le quote minime "
            "richieste superano la disponibilità idrica."
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

        prop_df, proportional = get_scenario(
            availability, demands, minimums,
            priority, "proporzionale"
        )

        priority_df, priority_result = get_scenario(
            availability, demands, minimums,
            priority, "priorità"
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
                round(max(0, demands[s] - proportional[s]), 2)
                for s in SECTORS
            ],
            "Deficit per priorità (hm³)": [
                round(max(0, demands[s] - priority_result[s]), 2)
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
        "Valutazione delle conseguenze economiche, sociali "
        "e ambientali delle strategie di allocazione."
    )

    st.info(
        "PROTOTIPO — Gli indicatori sono calcolati "
        "sui parametri simulati inseriti nell'Allocation Simulator."
    )

    # Recupero dei parametri condivisi

    availability = st.session_state.availability

    demands = {
        sector: st.session_state[f"demand_{sector}"]
        for sector in SECTORS
    }

    minimums = {
        sector: st.session_state[f"minimum_{sector}"]
        for sector in SECTORS
    }

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())

    if total_minimum > availability:

        st.error(
            "Non è possibile elaborare un'analisi valida: "
            "le quote minime superano la disponibilità idrica. "
            "Torna all'Allocation Simulator e modifica i parametri."
        )

    else:

        # Recupero delle priorità

        priority = []

        for i in range(4):
            key = f"priority_{i}"

            if key in st.session_state:
                priority.append(st.session_state[key])

        if len(priority) != 4 or len(set(priority)) != 4:
            priority = SECTORS.copy()

        st.subheader("1. Selezione dello scenario")

        selected_strategy = st.selectbox(
            "Scegli la strategia da analizzare",
            [
                "Allocazione proporzionale",
                "Allocazione per priorità"
            ],
            key="impact_strategy"
        )

        strategy = (
            "proporzionale"
            if selected_strategy == "Allocazione proporzionale"
            else "priorità"
        )

        impact_df, allocations = get_scenario(
            availability,
            demands,
            minimums,
            priority,
            strategy
        )

        # Indicatori generali

        total_allocated = sum(allocations.values())

        total_shortage = sum(
            max(0, demands[s] - allocations[s])
            for s in SECTORS
        )

        coverage = (
            total_allocated / total_demand * 100
            if total_demand > 0 else 100
        )

        st.divider()

        st.subheader("2. Quadro generale dell'impatto")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Disponibilità idrica",
            f"{availability:.1f} hm³"
        )

        c2.metric(
            "Acqua assegnata",
            f"{total_allocated:.1f} hm³"
        )

        c3.metric(
            "Deficit complessivo",
            f"{total_shortage:.1f} hm³"
        )

        c4.metric(
            "Domanda soddisfatta",
            f"{coverage:.1f}%"
        )

        st.caption(
            "L'acqua eventualmente non assegnata corrisponde "
            "a disponibilità eccedente i fabbisogni inseriti."
        )

        st.divider()

        # IMPATTO ECONOMICO

        st.subheader("3. Impatto economico")

        st.write(
            "L'analisi considera il deficit idrico dei due "
            "settori produttivi: agricoltura e industria."
        )

        agricultural_shortage = max(
            0,
            demands["Agricoltura"] - allocations["Agricoltura"]
        )

        industrial_shortage = max(
            0,
            demands["Industria"] - allocations["Industria"]
        )

        productive_shortage = (
            agricultural_shortage + industrial_shortage
        )

        e1, e2, e3 = st.columns(3)

        e1.metric(
            "Deficit agricoltura",
            f"{agricultural_shortage:.2f} hm³"
        )

        e2.metric(
            "Deficit industria",
            f"{industrial_shortage:.2f} hm³"
        )

        e3.metric(
            "Deficit produttivo",
            f"{productive_shortage:.2f} hm³"
        )

        st.caption(
            "Il deficit produttivo misura il volume di domanda "
            "non soddisfatto nei due settori. Non equivale "
            "direttamente a una perdita economica in euro."
        )

        st.divider()

        # IMPATTO SOCIALE

        st.subheader("4. Impatto sociale")

        civil_demand = demands["Usi civili"]
        civil_allocated = allocations["Usi civili"]

        civil_shortage = max(
            0,
            civil_demand - civil_allocated
        )

        civil_coverage = (
            civil_allocated / civil_demand * 100
            if civil_demand > 0 else 100
        )

        s1, s2, s3 = st.columns(3)

        s1.metric(
            "Domanda civile",
            f"{civil_demand:.2f} hm³"
        )

        s2.metric(
            "Acqua assegnata",
            f"{civil_allocated:.2f} hm³"
        )

        s3.metric(
            "Copertura civile",
            f"{civil_coverage:.1f}%"
        )

        st.write(
            f"Deficit degli usi civili: **{civil_shortage:.2f} hm³**"
        )

        if civil_shortage > 0:
            st.warning(
                "La domanda civile non è interamente soddisfatta. "
                "È necessario verificare la tutela dei fabbisogni "
                "essenziali e delle utenze vulnerabili."
            )
        else:
            st.success(
                "La domanda civile inserita nello scenario "
                "risulta interamente soddisfatta."
            )

        st.divider()

        # IMPATTO AMBIENTALE

        st.subheader("5. Impatto ambientale")

        environmental_minimum = minimums["Ambiente"]
        environmental_allocated = allocations["Ambiente"]

        environmental_shortage = max(
            0,
            environmental_minimum - environmental_allocated
        )

        environmental_coverage = (
            environmental_allocated / environmental_minimum * 100
            if environmental_minimum > 0 else 100
        )

        a1, a2, a3 = st.columns(3)

        a1.metric(
            "Quota minima ipotizzata",
            f"{environmental_minimum:.2f} hm³"
        )

        a2.metric(
            "Acqua assegnata",
            f"{environmental_allocated:.2f} hm³"
        )

        a3.metric(
            "Copertura quota minima",
            f"{environmental_coverage:.1f}%"
        )

        if environmental_shortage > 0:
            st.error(
                "La quota minima ambientale impostata "
                "non risulta rispettata."
            )
        else:
            st.success(
                "La quota minima ambientale impostata "
                "risulta rispettata nello scenario."
            )

        st.caption(
            "La quota ambientale è un'ipotesi dimostrativa "
            "del modello e non sostituisce il calcolo del "
            "deflusso ecologico o la verifica degli obblighi normativi."
        )

        st.divider()

        # CONFRONTO TRA SETTORI

        st.subheader("6. Distribuzione degli impatti")

        impact_df["Quota del deficit totale (%)"] = impact_df[
            "Deficit (hm³)"
        ].apply(
            lambda value: round(
                value / total_shortage * 100, 1
            ) if total_shortage > 0 else 0
        )

        st.dataframe(
            impact_df,
            hide_index=True,
            use_container_width=True
        )

        st.markdown("#### Domanda e acqua assegnata")

        chart_df = impact_df.set_index("Settore")[
            ["Domanda (hm³)", "Acqua assegnata (hm³)"]
        ]

        st.bar_chart(chart_df)

        st.markdown("#### Distribuzione del deficit")

        shortage_df = impact_df.set_index("Settore")[
            ["Deficit (hm³)"]
        ]

        st.bar_chart(shortage_df)

        st.divider()

        # SINTESI

        st.subheader("7. Sintesi dell'analisi")

        st.write(
            f"La strategia selezionata è **{selected_strategy.lower()}**. "
            f"Su una disponibilità di **{availability:.1f} hm³**, "
            f"sono stati assegnati **{total_allocated:.1f} hm³**."
        )

        st.write(
            f"Il deficit complessivo è pari a **{total_shortage:.1f} hm³**. "
            f"Il settore agricolo presenta un deficit di "
            f"**{agricultural_shortage:.2f} hm³**, mentre quello "
            f"industriale presenta un deficit di "
            f"**{industrial_shortage:.2f} hm³**."
        )

        st.write(
            f"Gli usi civili presentano una copertura del "
            f"**{civil_coverage:.1f}%**. La quota minima ambientale "
            f"impostata risulta "
            f"{'rispettata' if environmental_shortage == 0 else 'non rispettata'}."
        )

        st.caption(
            "L'analisi è uno strumento di supporto alla valutazione. "
            "Non formula decisioni automatiche né sostituisce "
            "le autorità competenti."
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
