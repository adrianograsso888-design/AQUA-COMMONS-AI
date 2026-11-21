
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

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


def build_analysis(availability, demands, minimums, priority, strategy):

    results_df, allocations = get_scenario(
        availability,
        demands,
        minimums,
        priority,
        strategy
    )

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())
    total_allocated = sum(allocations.values())

    total_shortage = sum(
        max(0, demands[s] - allocations[s])
        for s in SECTORS
    )

    coverage = (
        total_allocated / total_demand * 100
        if total_demand > 0 else 100
    )

    agricultural_shortage = max(
        0,
        demands["Agricoltura"] - allocations["Agricoltura"]
    )

    industrial_shortage = max(
        0,
        demands["Industria"] - allocations["Industria"]
    )

    civil_shortage = max(
        0,
        demands["Usi civili"] - allocations["Usi civili"]
    )

    civil_coverage = (
        allocations["Usi civili"] / demands["Usi civili"] * 100
        if demands["Usi civili"] > 0 else 100
    )

    environmental_minimum = minimums["Ambiente"]

    environmental_shortage = max(
        0,
        environmental_minimum - allocations["Ambiente"]
    )

    environmental_coverage = (
        allocations["Ambiente"] / environmental_minimum * 100
        if environmental_minimum > 0 else 100
    )

    results_df["Quota del deficit totale (%)"] = results_df[
        "Deficit (hm³)"
    ].apply(
        lambda value: round(
            value / total_shortage * 100, 1
        ) if total_shortage > 0 else 0
    )

    return {
        "results_df": results_df,
        "allocations": allocations,
        "total_demand": total_demand,
        "total_minimum": total_minimum,
        "total_allocated": total_allocated,
        "total_shortage": total_shortage,
        "coverage": coverage,
        "agricultural_shortage": agricultural_shortage,
        "industrial_shortage": industrial_shortage,
        "productive_shortage": (
            agricultural_shortage + industrial_shortage
        ),
        "civil_shortage": civil_shortage,
        "civil_coverage": civil_coverage,
        "environmental_minimum": environmental_minimum,
        "environmental_shortage": environmental_shortage,
        "environmental_coverage": environmental_coverage
    }


# =====================================================
# 4. GENERAZIONE DEL REPORT PDF
# =====================================================

def generate_pdf_report(analysis, availability, demands,
                        minimums, strategy_name, priority):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.7 * cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#123B56"),
        fontSize=22,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#123B56"),
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8
    )

    normal_style = styles["BodyText"]

    elements = []

    date_text = datetime.now().strftime("%d/%m/%Y %H:%M")

    elements.append(
        Paragraph("AQUA COMMONS AI", title_style)
    )

    elements.append(
        Paragraph("DECISION REPORT — ANALISI DELLO SCENARIO", styles["Heading2"])
    )

    elements.append(
        Paragraph(f"Data di generazione: {date_text}", normal_style)
    )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph("1. Sintesi dello scenario", heading_style)
    )

    summary_data = [
        ["Indicatore", "Valore"],
        ["Territorio di riferimento", "Bacino Brenta–Bacchiglione"],
        ["Disponibilità idrica", f"{availability:.2f} hm³"],
        ["Domanda complessiva", f"{analysis['total_demand']:.2f} hm³"],
        ["Quote minime richieste", f"{analysis['total_minimum']:.2f} hm³"],
        ["Strategia analizzata", strategy_name],
        ["Acqua assegnata", f"{analysis['total_allocated']:.2f} hm³"],
        ["Deficit complessivo", f"{analysis['total_shortage']:.2f} hm³"],
        ["Copertura della domanda", f"{analysis['coverage']:.1f}%"]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[8 * cm, 8 * cm]
    )

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B56")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE6")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    elements.append(summary_table)

    elements.append(
        Paragraph("2. Parametri e fabbisogni settoriali", heading_style)
    )

    demand_data = [
        ["Settore", "Domanda", "Quota minima"]
    ]

    for sector in SECTORS:
        demand_data.append([
            sector,
            f"{demands[sector]:.2f} hm³",
            f"{minimums[sector]:.2f} hm³"
        ])

    demand_table = Table(
        demand_data,
        colWidths=[6 * cm, 5 * cm, 5 * cm]
    )

    demand_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B56")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE6")),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    elements.append(demand_table)

    elements.append(
        Paragraph("3. Risultati dell'allocazione", heading_style)
    )

    allocation_data = [[
        "Settore",
        "Assegnata",
        "Deficit",
        "Soddisfatto"
    ]]

    for _, row in analysis["results_df"].iterrows():
        allocation_data.append([
            row["Settore"],
            f"{row['Acqua assegnata (hm³)']:.2f} hm³",
            f"{row['Deficit (hm³)']:.2f} hm³",
            f"{row['Fabbisogno soddisfatto (%)']:.1f}%"
        ])

    allocation_table = Table(
        allocation_data,
        colWidths=[4.5 * cm, 4 * cm, 4 * cm, 4 * cm]
    )

    allocation_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B56")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE6")),
        ("PADDING", (0, 0), (-1, -1), 6)
    ]))

    elements.append(allocation_table)

    elements.append(
        Paragraph("4. Analisi degli impatti", heading_style)
    )

    impact_data = [
        ["Dimensione", "Indicatore", "Risultato"],
        [
            "Economica",
            "Deficit produttivo",
            f"{analysis['productive_shortage']:.2f} hm³"
        ],
        [
            "Sociale",
            "Deficit usi civili",
            f"{analysis['civil_shortage']:.2f} hm³"
        ],
        [
            "Sociale",
            "Copertura usi civili",
            f"{analysis['civil_coverage']:.1f}%"
        ],
        [
            "Ambientale",
            "Quota minima ipotizzata",
            f"{analysis['environmental_minimum']:.2f} hm³"
        ],
        [
            "Ambientale",
            "Copertura quota minima",
            f"{analysis['environmental_coverage']:.1f}%"
        ]
    ]

    impact_table = Table(
        impact_data,
        colWidths=[4 * cm, 7 * cm, 5 * cm]
    )

    impact_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B56")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE6")),
        ("PADDING", (0, 0), (-1, -1), 6)
    ]))

    elements.append(impact_table)

    elements.append(
        Paragraph("5. Priorità impostate", heading_style)
    )

    elements.append(
        Paragraph(
            " → ".join(priority),
            normal_style
        )
    )

    elements.append(
        Paragraph("6. Considerazioni e limiti", heading_style)
    )

    elements.append(
        Paragraph(
            "Il presente documento è generato da un prototipo "
            "dimostrativo. I valori utilizzati sono simulati e "
            "non costituiscono misurazioni ufficiali del bacino "
            "Brenta–Bacchiglione.",
            normal_style
        )
    )

    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(
            "Il deficit produttivo rappresenta il volume di "
            "domanda non soddisfatto in agricoltura e industria. "
            "Non equivale a una perdita economica monetaria.",
            normal_style
        )
    )

    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(
            "La quota ambientale è un'ipotesi dello scenario e "
            "non sostituisce la verifica del deflusso ecologico "
            "e degli obblighi normativi applicabili.",
            normal_style
        )
    )

    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(
            "Il report supporta la valutazione delle alternative "
            "e non costituisce una decisione automatica. "
            "La decisione finale compete alle autorità responsabili.",
            normal_style
        )
    )

    document.build(elements)

    buffer.seek(0)

    return buffer.getvalue()


# =====================================================
# 5. NAVIGAZIONE
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
# 6. STATO CONDIVISO
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


# Recupero dei parametri correnti

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


# Recupero delle priorità

priority = []

for i in range(4):
    key = f"priority_{i}"

    if key in st.session_state:
        priority.append(st.session_state[key])

if len(priority) != 4 or len(set(priority)) != 4:
    priority = SECTORS.copy()


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
    dashboard_demand = sum(DEFAULT_DEMAND.values())
    deficit = max(0, dashboard_demand - available)

    coverage = (
        available / dashboard_demand * 100
        if dashboard_demand > 0 else 0
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

    if total_minimum > availability:

        st.error(
            "Non è possibile elaborare un'analisi valida: "
            "le quote minime superano la disponibilità idrica. "
            "Torna all'Allocation Simulator e modifica i parametri."
        )

    else:

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

        analysis = build_analysis(
            availability,
            demands,
            minimums,
            priority,
            strategy
        )

        st.divider()

        st.subheader("2. Quadro generale dell'impatto")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Disponibilità idrica", f"{availability:.1f} hm³")
        c2.metric("Acqua assegnata", f"{analysis['total_allocated']:.1f} hm³")
        c3.metric("Deficit complessivo", f"{analysis['total_shortage']:.1f} hm³")
        c4.metric("Domanda soddisfatta", f"{analysis['coverage']:.1f}%")

        st.caption(
            "L'acqua eventualmente non assegnata corrisponde "
            "a disponibilità eccedente i fabbisogni inseriti."
        )

        st.divider()

        st.subheader("3. Impatto economico")

        st.write(
            "L'analisi considera il deficit idrico dei due "
            "settori produttivi: agricoltura e industria."
        )

        e1, e2, e3 = st.columns(3)

        e1.metric(
            "Deficit agricoltura",
            f"{analysis['agricultural_shortage']:.2f} hm³"
        )

        e2.metric(
            "Deficit industria",
            f"{analysis['industrial_shortage']:.2f} hm³"
        )

        e3.metric(
            "Deficit produttivo",
            f"{analysis['productive_shortage']:.2f} hm³"
        )

        st.caption(
            "Il deficit produttivo misura il volume di domanda "
            "non soddisfatto. Non equivale direttamente a una "
            "perdita economica in euro."
        )

        st.divider()

        st.subheader("4. Impatto sociale")

        s1, s2, s3 = st.columns(3)

        s1.metric("Domanda civile", f"{demands['Usi civili']:.2f} hm³")
        s2.metric(
            "Acqua assegnata",
            f"{analysis['allocations']['Usi civili']:.2f} hm³"
        )
        s3.metric("Copertura civile", f"{analysis['civil_coverage']:.1f}%")

        st.write(
            f"Deficit degli usi civili: "
            f"**{analysis['civil_shortage']:.2f} hm³**"
        )

        if analysis["civil_shortage"] > 0:
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

        st.subheader("5. Impatto ambientale")

        a1, a2, a3 = st.columns(3)

        a1.metric(
            "Quota minima ipotizzata",
            f"{analysis['environmental_minimum']:.2f} hm³"
        )

        a2.metric(
            "Acqua assegnata",
            f"{analysis['allocations']['Ambiente']:.2f} hm³"
        )

        a3.metric(
            "Copertura quota minima",
            f"{analysis['environmental_coverage']:.1f}%"
        )

        if analysis["environmental_shortage"] > 0:
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
            "e non sostituisce il calcolo del deflusso ecologico "
            "o la verifica degli obblighi normativi."
        )

        st.divider()

        st.subheader("6. Distribuzione degli impatti")

        st.dataframe(
            analysis["results_df"],
            hide_index=True,
            use_container_width=True
        )

        st.markdown("#### Domanda e acqua assegnata")

        st.bar_chart(
            analysis["results_df"].set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

        st.markdown("#### Distribuzione del deficit")

        st.bar_chart(
            analysis["results_df"].set_index("Settore")[
                ["Deficit (hm³)"]
            ]
        )

        st.divider()

        st.subheader("7. Sintesi dell'analisi")

        st.write(
            f"La strategia selezionata è **{selected_strategy.lower()}**. "
            f"Su una disponibilità di **{availability:.1f} hm³**, "
            f"sono stati assegnati "
            f"**{analysis['total_allocated']:.1f} hm³**."
        )

        st.write(
            f"Il deficit complessivo è pari a "
            f"**{analysis['total_shortage']:.1f} hm³**. "
            f"Il settore agricolo presenta un deficit di "
            f"**{analysis['agricultural_shortage']:.2f} hm³**, "
            f"mentre quello industriale presenta un deficit di "
            f"**{analysis['industrial_shortage']:.2f} hm³**."
        )

        st.write(
            f"Gli usi civili presentano una copertura del "
            f"**{analysis['civil_coverage']:.1f}%**. "
            f"La quota minima ambientale impostata risulta "
            f"{'rispettata' if analysis['environmental_shortage'] == 0 else 'non rispettata'}."
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
        "Generazione di un documento strutturato che "
        "organizza i risultati della simulazione e "
        "dell'analisi d'impatto."
    )

    st.info(
        "Il report viene generato utilizzando i parametri "
        "e i risultati effettivi dello scenario selezionato. "
        "I dati del prototipo sono simulati."
    )

    if total_minimum > availability:

        st.error(
            "Impossibile generare il report: le quote minime "
            "superano la disponibilità idrica. "
            "Correggi lo scenario nell'Allocation Simulator."
        )

    else:

        st.subheader("1. Configurazione del report")

        report_strategy_name = st.selectbox(
            "Strategia da inserire nel report",
            [
                "Allocazione proporzionale",
                "Allocazione per priorità"
            ],
            key="report_strategy"
        )

        report_strategy = (
            "proporzionale"
            if report_strategy_name == "Allocazione proporzionale"
            else "priorità"
        )

        report_analysis = build_analysis(
            availability,
            demands,
            minimums,
            priority,
            report_strategy
        )

        st.caption(
            "Il report utilizza i parametri correnti "
            "dell'Allocation Simulator."
        )

        st.divider()

        st.subheader("2. Sintesi dello scenario")

        r1, r2, r3, r4 = st.columns(4)

        r1.metric(
            "Disponibilità",
            f"{availability:.1f} hm³"
        )

        r2.metric(
            "Domanda totale",
            f"{report_analysis['total_demand']:.1f} hm³"
        )

        r3.metric(
            "Acqua assegnata",
            f"{report_analysis['total_allocated']:.1f} hm³"
        )

        r4.metric(
            "Deficit complessivo",
            f"{report_analysis['total_shortage']:.1f} hm³"
        )

        st.write(f"**Territorio:** Bacino Brenta–Bacchiglione")
        st.write(f"**Strategia:** {report_strategy_name}")
        st.write(
            f"**Copertura complessiva:** "
            f"{report_analysis['coverage']:.1f}%"
        )

        st.divider()

        st.subheader("3. Risultati dell'allocazione")

        st.dataframe(
            report_analysis["results_df"],
            hide_index=True,
            use_container_width=True
        )

        st.bar_chart(
            report_analysis["results_df"].set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

        st.divider()

        st.subheader("4. Valutazione degli impatti")

        impact1, impact2, impact3 = st.columns(3)

        with impact1:
            st.markdown("**Economico**")
            st.metric(
                "Deficit produttivo",
                f"{report_analysis['productive_shortage']:.2f} hm³"
            )
            st.caption("Agricoltura e industria")

        with impact2:
            st.markdown("**Sociale**")
            st.metric(
                "Copertura civile",
                f"{report_analysis['civil_coverage']:.1f}%"
            )
            st.caption(
                f"Deficit: {report_analysis['civil_shortage']:.2f} hm³"
            )

        with impact3:
            st.markdown("**Ambientale**")
            st.metric(
                "Copertura quota minima",
                f"{report_analysis['environmental_coverage']:.1f}%"
            )
            st.caption(
                f"Quota ipotizzata: "
                f"{report_analysis['environmental_minimum']:.2f} hm³"
            )

        st.divider()

        st.subheader("5. Confronto tra strategie")

        proportional_analysis = build_analysis(
            availability,
            demands,
            minimums,
            priority,
            "proporzionale"
        )

        priority_analysis = build_analysis(
            availability,
            demands,
            minimums,
            priority,
            "priorità"
        )

        comparison_df = pd.DataFrame({
            "Indicatore": [
                "Acqua assegnata (hm³)",
                "Deficit complessivo (hm³)",
                "Deficit agricolo (hm³)",
                "Deficit usi civili (hm³)",
                "Deficit industria (hm³)",
                "Copertura domanda (%)"
            ],
            "Proporzionale": [
                round(proportional_analysis["total_allocated"], 2),
                round(proportional_analysis["total_shortage"], 2),
                round(proportional_analysis["agricultural_shortage"], 2),
                round(proportional_analysis["civil_shortage"], 2),
                round(proportional_analysis["industrial_shortage"], 2),
                round(proportional_analysis["coverage"], 1)
            ],
            "Per priorità": [
                round(priority_analysis["total_allocated"], 2),
                round(priority_analysis["total_shortage"], 2),
                round(priority_analysis["agricultural_shortage"], 2),
                round(priority_analysis["civil_shortage"], 2),
                round(priority_analysis["industrial_shortage"], 2),
                round(priority_analysis["coverage"], 1)
            ]
        })

        st.dataframe(
            comparison_df,
            hide_index=True,
            use_container_width=True
        )

        st.divider()

        st.subheader("6. Considerazioni per la decisione")

        st.write(
            f"La strategia selezionata è **{report_strategy_name.lower()}**. "
            f"Il deficit complessivo dello scenario è pari a "
            f"**{report_analysis['total_shortage']:.2f} hm³**."
        )

        if report_analysis["civil_shortage"] > 0:
            st.warning(
                "Attenzione: la domanda civile non è interamente "
                "soddisfatta. Occorre approfondire la tutela "
                "dei fabbisogni essenziali."
            )
        else:
            st.success(
                "La domanda civile inserita nello scenario "
                "risulta interamente soddisfatta."
            )

        if report_analysis["environmental_shortage"] > 0:
            st.error(
                "La quota minima ambientale ipotizzata "
                "non risulta rispettata."
            )
        else:
            st.success(
                "La quota minima ambientale ipotizzata "
                "risulta rispettata."
            )

        st.caption(
            "Le considerazioni sono indicatori di supporto, "
            "non raccomandazioni automatiche. La valutazione "
            "finale spetta alle autorità competenti."
        )

        st.divider()

        st.subheader("7. Generazione del documento")

        st.write(
            "Puoi esportare i risultati dello scenario "
            "in un documento PDF strutturato."
        )

        pdf_bytes = generate_pdf_report(
            report_analysis,
            availability,
            demands,
            minimums,
            report_strategy_name,
            priority
        )

        st.download_button(
            label="📄 Scarica Decision Report in PDF",
            data=pdf_bytes,
            file_name="AQUA_COMMONS_AI_Decision_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.caption(
            "Il documento contiene i parametri, i risultati, "
            "gli indicatori d'impatto e le principali "
            "limitazioni dello scenario."
        )
