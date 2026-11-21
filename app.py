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
    TableStyle,
)

# ============================================================
# AQUA COMMONS AI - PROTOTIPO DIMOSTRATIVO
# ============================================================

st.set_page_config(
    page_title="AQUA COMMONS AI",
    page_icon="💧",
    layout="wide",
)

SECTORS = ["Agricoltura", "Usi civili", "Industria", "Ambiente"]

DEFAULT_DEMAND = {
    "Agricoltura": 70.0,
    "Usi civili": 25.0,
    "Industria": 15.0,
    "Ambiente": 15.0,
}

DEFAULT_MINIMUM = {
    "Agricoltura": 30.0,
    "Usi civili": 25.0,
    "Industria": 5.0,
    "Ambiente": 15.0,
}

TERRITORY = "Bacino Brenta–Bacchiglione"
REGION = "Veneto, Italia"

# ============================================================
# STILE
# ============================================================

st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)

# ============================================================
# FUNZIONI DI CALCOLO
# ============================================================

def proportional_allocation(availability, demands, minimums):
    """
    Rispetta prima tutte le quote minime.
    Distribuisce poi la risorsa residua in proporzione
    alla domanda ancora insoddisfatta di ciascun settore.
    """
    allocations = {s: float(minimums[s]) for s in SECTORS}
    remaining = max(0.0, float(availability) - sum(allocations.values()))

    capacities = {
        s: max(0.0, float(demands[s]) - allocations[s])
        for s in SECTORS
    }

    tolerance = 1e-9

    while remaining > tolerance:
        active = [s for s in SECTORS if capacities[s] > tolerance]
        if not active:
            break

        total_capacity = sum(capacities[s] for s in active)
        if total_capacity <= tolerance:
            break

        amount_to_distribute = remaining
        distributed = 0.0

        for sector in active:
            share = amount_to_distribute * capacities[sector] / total_capacity
            extra = min(share, capacities[sector])
            allocations[sector] += extra
            capacities[sector] -= extra
            distributed += extra

        remaining -= distributed
        if distributed <= tolerance:
            break

    return allocations


def priority_allocation(availability, demands, minimums, priority):
    """
    Rispetta prima tutte le quote minime.
    Distribuisce poi la risorsa residua seguendo l'ordine
    di priorità scelto dall'utente.
    """
    allocations = {s: float(minimums[s]) for s in SECTORS}
    remaining = max(0.0, float(availability) - sum(allocations.values()))

    for sector in priority:
        capacity = max(0.0, float(demands[sector]) - allocations[sector])
        extra = min(remaining, capacity)
        allocations[sector] += extra
        remaining -= extra

        if remaining <= 1e-9:
            break

    return allocations


def calculate_results(demands, allocations):
    rows = []

    for sector in SECTORS:
        demand = float(demands[sector])
        allocated = float(allocations[sector])
        deficit = max(0.0, demand - allocated)
        satisfaction = allocated / demand * 100 if demand > 0 else 100.0

        rows.append(
            {
                "Settore": sector,
                "Domanda (hm³)": round(demand, 2),
                "Acqua assegnata (hm³)": round(allocated, 2),
                "Deficit (hm³)": round(deficit, 2),
                "Fabbisogno soddisfatto (%)": round(satisfaction, 1),
            }
        )

    return pd.DataFrame(rows)


def get_scenario(availability, demands, minimums, priority, strategy):
    if strategy == "proporzionale":
        allocations = proportional_allocation(
            availability, demands, minimums
        )
    elif strategy == "priorità":
        allocations = priority_allocation(
            availability, demands, minimums, priority
        )
    else:
        raise ValueError("Strategia di allocazione non riconosciuta.")

    return calculate_results(demands, allocations), allocations


def build_analysis(availability, demands, minimums, priority, strategy):
    results_df, allocations = get_scenario(
        availability, demands, minimums, priority, strategy
    )

    total_demand = sum(float(demands[s]) for s in SECTORS)
    total_minimum = sum(float(minimums[s]) for s in SECTORS)
    total_allocated = sum(allocations.values())
    total_shortage = sum(
        max(0.0, float(demands[s]) - allocations[s]) for s in SECTORS
    )

    demand_coverage = (
        total_allocated / total_demand * 100
        if total_demand > 0
        else 100.0
    )

    agricultural_shortage = max(
        0.0, demands["Agricoltura"] - allocations["Agricoltura"]
    )
    industrial_shortage = max(
        0.0, demands["Industria"] - allocations["Industria"]
    )
    civil_shortage = max(
        0.0, demands["Usi civili"] - allocations["Usi civili"]
    )

    civil_coverage = (
        allocations["Usi civili"] / demands["Usi civili"] * 100
        if demands["Usi civili"] > 0
        else 100.0
    )

    # Questa è una quota minima ipotizzata nel modello.
    # Non è una misurazione del deflusso ecologico reale.
    environmental_minimum = float(minimums["Ambiente"])
    environmental_allocated = float(allocations["Ambiente"])
    environmental_constraint_gap = max(
        0.0, environmental_minimum - environmental_allocated
    )
    environmental_constraint_coverage = (
        environmental_allocated / environmental_minimum * 100
        if environmental_minimum > 0
        else 100.0
    )

    results_df["Quota del deficit totale (%)"] = results_df[
        "Deficit (hm³)"
    ].apply(
        lambda value: round(value / total_shortage * 100, 1)
        if total_shortage > 0
        else 0.0
    )

    return {
        "results_df": results_df,
        "allocations": allocations,
        "total_demand": total_demand,
        "total_minimum": total_minimum,
        "total_allocated": total_allocated,
        "total_shortage": total_shortage,
        "coverage": demand_coverage,
        "agricultural_shortage": agricultural_shortage,
        "industrial_shortage": industrial_shortage,
        "productive_shortage": agricultural_shortage + industrial_shortage,
        "civil_shortage": civil_shortage,
        "civil_coverage": civil_coverage,
        "environmental_minimum": environmental_minimum,
        "environmental_allocated": environmental_allocated,
        "environmental_constraint_gap": environmental_constraint_gap,
        "environmental_constraint_coverage": environmental_constraint_coverage,
    }


def build_comparison(availability, demands, minimums, priority):
    proportional = build_analysis(
        availability, demands, minimums, priority, "proporzionale"
    )
    priority_result = build_analysis(
        availability, demands, minimums, priority, "priorità"
    )

    comparison = pd.DataFrame(
        {
            "Indicatore": [
                "Acqua assegnata (hm³)",
                "Deficit complessivo (hm³)",
                "Deficit agricolo (hm³)",
                "Deficit usi civili (hm³)",
                "Deficit industria (hm³)",
                "Copertura domanda (%)",
            ],
            "Proporzionale": [
                round(proportional["total_allocated"], 2),
                round(proportional["total_shortage"], 2),
                round(proportional["agricultural_shortage"], 2),
                round(proportional["civil_shortage"], 2),
                round(proportional["industrial_shortage"], 2),
                round(proportional["coverage"], 1),
            ],
            "Per priorità": [
                round(priority_result["total_allocated"], 2),
                round(priority_result["total_shortage"], 2),
                round(priority_result["agricultural_shortage"], 2),
                round(priority_result["civil_shortage"], 2),
                round(priority_result["industrial_shortage"], 2),
                round(priority_result["coverage"], 1),
            ],
        }
    )

    return proportional, priority_result, comparison


# ============================================================
# GENERAZIONE DEL PDF
# ============================================================

def generate_pdf_report(
    analysis,
    availability,
    demands,
    minimums,
    strategy_name,
    priority,
    comparison_df,
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AquaTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#123B56"),
        fontSize=21,
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "AquaHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#123B56"),
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = styles["BodyText"]

    elements = []
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    elements.append(Paragraph("AQUA COMMONS AI", title_style))
    elements.append(
        Paragraph("DECISION REPORT — ANALISI DELLO SCENARIO", styles["Heading2"])
    )
    elements.append(
        Paragraph(f"Data e ora di generazione: {generated_at}", body_style)
    )
    elements.append(Spacer(1, 10))

    def add_table(data, widths):
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B56")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE6")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(table)

    elements.append(Paragraph("1. Sintesi dello scenario", heading_style))
    summary_data = [
        ["Indicatore", "Valore"],
        ["Territorio di riferimento", TERRITORY],
        ["Regione", REGION],
        ["Disponibilità idrica", f"{availability:.2f} hm³"],
        ["Domanda complessiva", f"{analysis['total_demand']:.2f} hm³"],
        ["Somma delle quote minime", f"{analysis['total_minimum']:.2f} hm³"],
        ["Strategia analizzata", strategy_name],
        ["Acqua assegnata", f"{analysis['total_allocated']:.2f} hm³"],
        ["Deficit complessivo", f"{analysis['total_shortage']:.2f} hm³"],
        ["Copertura della domanda", f"{analysis['coverage']:.1f}%"],
    ]
    add_table(summary_data, [8 * cm, 8 * cm])

    elements.append(
        Paragraph("2. Domande e quote minime impostate", heading_style)
    )
    demand_data = [["Settore", "Domanda", "Quota minima"]]
    for sector in SECTORS:
        demand_data.append(
            [
                sector,
                f"{demands[sector]:.2f} hm³",
                f"{minimums[sector]:.2f} hm³",
            ]
        )
    add_table(demand_data, [6 * cm, 5 * cm, 5 * cm])

    elements.append(
        Paragraph("3. Risultati dell'allocazione", heading_style)
    )
    allocation_data = [
        ["Settore", "Assegnata", "Deficit", "Soddisfatto"]
    ]
    for _, row in analysis["results_df"].iterrows():
        allocation_data.append(
            [
                row["Settore"],
                f"{row['Acqua assegnata (hm³)']:.2f} hm³",
                f"{row['Deficit (hm³)']:.2f} hm³",
                f"{row['Fabbisogno soddisfatto (%)']:.1f}%",
            ]
        )
    add_table(allocation_data, [4.2 * cm, 4.1 * cm, 4.1 * cm, 4.5 * cm])

    elements.append(
        Paragraph("4. Indicatori di impatto e di scenario", heading_style)
    )
    impact_data = [
        ["Dimensione", "Indicatore", "Risultato"],
        [
            "Settori produttivi",
            "Deficit agricolo + industriale",
            f"{analysis['productive_shortage']:.2f} hm³",
        ],
        [
            "Sociale",
            "Deficit degli usi civili",
            f"{analysis['civil_shortage']:.2f} hm³",
        ],
        [
            "Sociale",
            "Copertura degli usi civili",
            f"{analysis['civil_coverage']:.1f}%",
        ],
        [
            "Vincolo ambientale simulato",
            "Quota minima inserita",
            f"{analysis['environmental_minimum']:.2f} hm³",
        ],
        [
            "Vincolo ambientale simulato",
            "Acqua assegnata all'ambiente",
            f"{analysis['environmental_allocated']:.2f} hm³",
        ],
    ]
    add_table(impact_data, [4.4 * cm, 7.0 * cm, 5.5 * cm])

    elements.append(
        Paragraph("5. Confronto tra strategie", heading_style)
    )
    comparison_data = [
        [
            "Indicatore",
            "Proporzionale",
            "Per priorità",
        ]
    ]
    for _, row in comparison_df.iterrows():
        comparison_data.append(
            [
                str(row["Indicatore"]),
                str(row["Proporzionale"]),
                str(row["Per priorità"]),
            ]
        )
    add_table(comparison_data, [8 * cm, 4.5 * cm, 4.5 * cm])

    elements.append(
        Paragraph("6. Ordine di priorità configurato", heading_style)
    )
    if strategy_name == "Allocazione per priorità":
        elements.append(Paragraph(" > ".join(priority), body_style))
    else:
        elements.append(
            Paragraph(
                "Non applicabile: nella strategia proporzionale "
                "l'ordine di priorità non determina l'allocazione.",
                body_style,
            )
        )

    elements.append(
        Paragraph("7. Assunzioni, limiti e responsabilità", heading_style)
    )
    notes = [
        (
            "Il presente documento è generato da un prototipo dimostrativo. "
            "I valori utilizzati sono simulati e non costituiscono "
            "misurazioni ufficiali del bacino Brenta–Bacchiglione."
        ),
        (
            "Il deficit dei settori produttivi è espresso in volume d'acqua "
            "non assegnato (hm³). Non rappresenta una perdita economica "
            "monetaria e non viene convertito in euro."
        ),
        (
            "La quota ambientale è un parametro ipotizzato nello scenario. "
            "Il suo rispetto matematico nel modello non dimostra il rispetto "
            "del deflusso ecologico, delle portate sito-specifiche o di tutti "
            "gli obblighi normativi."
        ),
        (
            "Le quote minime sono vincoli del modello dimostrativo e non "
            "devono essere interpretate come soglie normative ufficiali."
        ),
        (
            "Il report confronta scenari e organizza indicatori a supporto "
            "della valutazione. Non formula decisioni automatiche: la "
            "decisione finale compete alle autorità responsabili."
        ),
    ]
    for note in notes:
        elements.append(Paragraph(f"• {note}", body_style))
        elements.append(Spacer(1, 4))

    document.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# STATO CONDIVISO
# ============================================================

if "availability" not in st.session_state:
    st.session_state["availability"] = 100.0

for sector in SECTORS:
    demand_key = f"demand_{sector}"
    minimum_key = f"minimum_{sector}"

    if demand_key not in st.session_state:
        st.session_state[demand_key] = DEFAULT_DEMAND[sector]
    if minimum_key not in st.session_state:
        st.session_state[minimum_key] = DEFAULT_MINIMUM[sector]

# Priorità iniziali distinte: una per ciascun settore.
for index, sector in enumerate(SECTORS):
    priority_key = f"priority_{index}"
    if priority_key not in st.session_state:
        st.session_state[priority_key] = sector

# Recupero dello scenario persistente.
availability = float(st.session_state["availability"])
demands = {
    sector: float(st.session_state[f"demand_{sector}"])
    for sector in SECTORS
}
minimums = {
    sector: float(st.session_state[f"minimum_{sector}"])
    for sector in SECTORS
}
priority = [
    st.session_state[f"priority_{index}"]
    for index in range(len(SECTORS))
]
priority_valid = (
    len(priority) == len(SECTORS)
    and len(set(priority)) == len(SECTORS)
    and set(priority) == set(SECTORS)
)

# ============================================================
# NAVIGAZIONE
# ============================================================

st.sidebar.title("💧 AQUA COMMONS AI")
st.sidebar.caption("WATER MANAGEMENT PLATFORM")

page = st.sidebar.radio(
    "NAVIGAZIONE",
    [
        "Water Dashboard",
        "Allocation Simulator",
        "Impact Analysis",
        "Decision Report",
    ],
)

st.sidebar.divider()
st.sidebar.caption("TERRITORIO PILOTA")
st.sidebar.write(TERRITORY)
st.sidebar.write(REGION)
st.sidebar.divider()
st.sidebar.caption("PROTOTIPO DIMOSTRATIVO")

# ============================================================
# 01 - WATER DASHBOARD
# ============================================================

if page == "Water Dashboard":
    st.title("Water Dashboard")
    st.write(
        "Panoramica della disponibilità idrica, della domanda "
        "e dei fabbisogni dei diversi settori."
    )
    st.info(
        "PROTOTIPO — I valori sono simulati e modificabili "
        "nell'Allocation Simulator. Non rappresentano misurazioni "
        "ufficiali del bacino Brenta–Bacchiglione."
    )

    dashboard_total_demand = sum(demands.values())
    dashboard_total_minimum = sum(minimums.values())
    theoretical_shortage = max(0.0, dashboard_total_demand - availability)
    theoretical_coverage = (
        min(availability, dashboard_total_demand) / dashboard_total_demand * 100
        if dashboard_total_demand > 0
        else 100.0
    )
    feasible = dashboard_total_minimum <= availability + 1e-9

    st.subheader("Indicatori principali")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Disponibilità idrica", f"{availability:.1f} hm³")
    c2.metric("Domanda complessiva", f"{dashboard_total_demand:.1f} hm³")
    c3.metric("Deficit teorico", f"{theoretical_shortage:.1f} hm³")
    c4.metric("Copertura teorica", f"{theoretical_coverage:.1f}%")

    st.caption(
        "La copertura teorica confronta disponibilità e domanda totale; "
        "non sostituisce il risultato di una specifica strategia di allocazione."
    )

    if feasible:
        st.success(
            f"Scenario compatibile con i vincoli minimi inseriti "
            f"({dashboard_total_minimum:.1f} hm³ richiesti)."
        )
    else:
        st.error(
            f"Scenario non fattibile: le quote minime sommano "
            f"{dashboard_total_minimum:.1f} hm³, oltre la disponibilità "
            f"di {availability:.1f} hm³."
        )

    st.divider()
    st.subheader("Fabbisogno per settore")
    demand_df = pd.DataFrame(
        {
            "Settore": SECTORS,
            "Fabbisogno (hm³)": [demands[s] for s in SECTORS],
            "Quota minima (hm³)": [minimums[s] for s in SECTORS],
        }
    )

    left, right = st.columns([1.4, 1])
    with left:
        st.bar_chart(demand_df.set_index("Settore")[["Fabbisogno (hm³)"]])
    with right:
        st.dataframe(
            demand_df,
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Copertura teorica della domanda")
    st.progress(min(max(theoretical_coverage / 100, 0), 1))
    st.write(f"Copertura teorica: **{theoretical_coverage:.1f}%**")
    st.write(f"Domanda non coperta in termini teorici: **{theoretical_shortage:.1f} hm³**")

# ============================================================
# 02 - ALLOCATION SIMULATOR
# ============================================================

elif page == "Allocation Simulator":
    st.title("Allocation Simulator")
    st.write(
        "Modifica la disponibilità idrica, i fabbisogni e le quote minime "
        "per confrontare due strategie alternative di allocazione."
    )
    st.info(
        "PROTOTIPO — I valori iniziali sono simulati. Le quote minime "
        "sono ipotesi del modello dimostrativo, non soglie normative ufficiali."
    )

    st.subheader("1. Parametri dello scenario")
    availability = st.number_input(
        "Disponibilità idrica totale (hm³)",
        min_value=0.0,
        max_value=1000.0,
        step=5.0,
        key="availability",
    )

    st.markdown("#### Fabbisogni e quote minime")
    header = st.columns([2, 1, 1])
    header[0].markdown("**Settore**")
    header[1].markdown("**Domanda (hm³)**")
    header[2].markdown("**Quota minima (hm³)**")

    demands = {}
    minimums = {}

    for sector in SECTORS:
        demand_key = f"demand_{sector}"
        minimum_key = f"minimum_{sector}"

        # Mantiene sempre la condizione quota minima <= domanda.
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
            label_visibility="collapsed",
        )

        minimums[sector] = cols[2].number_input(
            f"Minimo {sector}",
            min_value=0.0,
            max_value=float(demands[sector]),
            step=1.0,
            key=minimum_key,
            label_visibility="collapsed",
        )

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Disponibilità", f"{availability:.1f} hm³")
    m2.metric("Domanda totale", f"{total_demand:.1f} hm³")
    m3.metric("Quote minime richieste", f"{total_minimum:.1f} hm³")

    if total_minimum > availability + 1e-9:
        st.error(
            "SCENARIO NON FATTIBILE: le quote minime richieste superano "
            "la disponibilità idrica. Riduci le quote minime o aumenta "
            "la disponibilità prima di confrontare le strategie."
        )
    else:
        st.success("Le quote minime inserite sono compatibili con la disponibilità.")

        st.subheader("2. Definizione delle priorità")
        st.write(
            "L'ordine viene applicato esclusivamente alla strategia "
            "«Allocazione per priorità»."
        )

        priority = []
        for index in range(len(SECTORS)):
            selected = st.selectbox(
                f"Priorità {index + 1}",
                options=SECTORS,
                key=f"priority_{index}",
            )
            priority.append(selected)

        if len(set(priority)) != len(SECTORS):
            st.error(
                "Ogni settore deve comparire una sola volta. "
                "Correggi l'ordine delle priorità."
            )
        else:
            st.divider()
            st.subheader("3. Risultati della simulazione")

            prop_df, proportional_allocations = get_scenario(
                availability, demands, minimums, priority, "proporzionale"
            )
            priority_df, priority_allocations = get_scenario(
                availability, demands, minimums, priority, "priorità"
            )

            tab1, tab2 = st.tabs(
                ["Allocazione proporzionale", "Allocazione per priorità"]
            )

            with tab1:
                st.markdown("#### Strategia proporzionale")
                st.write(
                    "Dopo l'assegnazione delle quote minime, la risorsa residua "
                    "viene distribuita in proporzione ai fabbisogni ancora "
                    "insoddisfatti."
                )
                st.dataframe(prop_df, hide_index=True, use_container_width=True)
                st.bar_chart(
                    prop_df.set_index("Settore")[
                        ["Domanda (hm³)", "Acqua assegnata (hm³)"]
                    ]
                )

            with tab2:
                st.markdown("#### Strategia per priorità")
                st.write(
                    "Dopo l'assegnazione delle quote minime, la risorsa residua "
                    "viene distribuita seguendo l'ordine scelto."
                )
                st.dataframe(priority_df, hide_index=True, use_container_width=True)
                st.bar_chart(
                    priority_df.set_index("Settore")[
                        ["Domanda (hm³)", "Acqua assegnata (hm³)"]
                    ]
                )

            st.divider()
            st.subheader("4. Confronto tra strategie")
            comparison_sector_df = pd.DataFrame(
                {
                    "Settore": SECTORS,
                    "Deficit proporzionale (hm³)": [
                        round(max(0.0, demands[s] - proportional_allocations[s]), 2)
                        for s in SECTORS
                    ],
                    "Deficit per priorità (hm³)": [
                        round(max(0.0, demands[s] - priority_allocations[s]), 2)
                        for s in SECTORS
                    ],
                }
            )
            st.dataframe(
                comparison_sector_df,
                hide_index=True,
                use_container_width=True,
            )

            total_prop_deficit = sum(
                max(0.0, demands[s] - proportional_allocations[s])
                for s in SECTORS
            )
            total_priority_deficit = sum(
                max(0.0, demands[s] - priority_allocations[s])
                for s in SECTORS
            )

            a, b = st.columns(2)
            a.metric("Deficit totale - proporzionale", f"{total_prop_deficit:.2f} hm³")
            b.metric("Deficit totale - per priorità", f"{total_priority_deficit:.2f} hm³")

            st.caption(
                "Le strategie sono strumenti di confronto, non raccomandazioni "
                "automatiche. L'allocazione effettiva deve rispettare la "
                "normativa, i vincoli fisici e le competenze delle autorità."
            )

# ============================================================
# 03 - IMPACT ANALYSIS
# ============================================================

elif page == "Impact Analysis":
    st.title("Impact Analysis")
    st.write(
        "Valutazione delle conseguenze sui settori produttivi, sugli usi civili "
        "e sul parametro ambientale ipotizzato nello scenario."
    )
    st.info(
        "PROTOTIPO — Gli indicatori sono calcolati sui parametri simulati "
        "inseriti nell'Allocation Simulator."
    )

    if total_minimum > availability + 1e-9:
        st.error(
            "Non è possibile elaborare un'analisi valida: le quote minime "
            "superano la disponibilità. Torna all'Allocation Simulator "
            "e modifica i parametri."
        )
    elif not priority_valid:
        st.error(
            "L'ordine delle priorità non è valido: ogni settore deve "
            "comparire una sola volta. Correggilo nell'Allocation Simulator."
        )
    else:
        selected_strategy = st.selectbox(
            "Scegli la strategia da analizzare",
            ["Allocazione proporzionale", "Allocazione per priorità"],
            key="impact_strategy",
        )

        strategy = (
            "proporzionale"
            if selected_strategy == "Allocazione proporzionale"
            else "priorità"
        )

        analysis = build_analysis(
            availability, demands, minimums, priority, strategy
        )

        st.divider()
        st.subheader("1. Quadro generale dello scenario")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Disponibilità idrica", f"{availability:.1f} hm³")
        c2.metric("Acqua assegnata", f"{analysis['total_allocated']:.1f} hm³")
        c3.metric("Deficit complessivo", f"{analysis['total_shortage']:.1f} hm³")
        c4.metric("Domanda soddisfatta", f"{analysis['coverage']:.1f}%")

        unused_water = max(0.0, availability - analysis["total_allocated"])
        if unused_water > 1e-6:
            st.caption(
                f"Acqua non assegnata: {unused_water:.2f} hm³. "
                "La disponibilità residua supera la domanda ancora soddisfacibile."
            )

        st.divider()
        st.subheader("2. Impatto sui settori produttivi")
        st.write(
            "L'indicatore considera il volume di domanda non soddisfatto "
            "in agricoltura e industria."
        )
        e1, e2, e3 = st.columns(3)
        e1.metric("Deficit agricoltura", f"{analysis['agricultural_shortage']:.2f} hm³")
        e2.metric("Deficit industria", f"{analysis['industrial_shortage']:.2f} hm³")
        e3.metric("Deficit produttivo", f"{analysis['productive_shortage']:.2f} hm³")
        st.caption(
            "Il deficit produttivo è un indicatore volumetrico. Non equivale "
            "a una perdita economica in euro: per stimarla servirebbero "
            "dati specifici su produzioni, costi e valore aggiunto."
        )

        st.divider()
        st.subheader("3. Impatto sugli usi civili")
        s1, s2, s3 = st.columns(3)
        s1.metric("Domanda civile", f"{demands['Usi civili']:.2f} hm³")
        s2.metric(
            "Acqua assegnata",
            f"{analysis['allocations']['Usi civili']:.2f} hm³",
        )
        s3.metric("Copertura civile", f"{analysis['civil_coverage']:.1f}%")

        st.write(
            f"Deficit degli usi civili: **{analysis['civil_shortage']:.2f} hm³**"
        )
        if analysis["civil_shortage"] > 1e-6:
            st.warning(
                "La domanda civile inserita non è interamente soddisfatta. "
                "Occorre verificare la tutela dei fabbisogni essenziali, "
                "delle utenze vulnerabili e degli obblighi di servizio."
            )
        else:
            st.success(
                "La domanda civile inserita nello scenario risulta interamente "
                "soddisfatta. Questo risultato dipende dai parametri impostati."
            )

        st.divider()
        st.subheader("4. Parametro ambientale dello scenario")
        a1, a2, a3 = st.columns(3)
        a1.metric(
            "Quota minima ipotizzata",
            f"{analysis['environmental_minimum']:.2f} hm³",
        )
        a2.metric(
            "Acqua assegnata all'ambiente",
            f"{analysis['environmental_allocated']:.2f} hm³",
        )
        a3.metric(
            "Scostamento dalla quota minima",
            f"{analysis['environmental_constraint_gap']:.2f} hm³",
        )

        st.warning(
            "ATTENZIONE: la quota ambientale è un vincolo ipotizzato "
            "nel prototipo e viene assegnata dal modello come quota minima. "
            "Il suo rispetto matematico non dimostra la tutela effettiva "
            "dell'ecosistema e non sostituisce il calcolo del deflusso "
            "ecologico, le verifiche idrologiche sito-specifiche o gli "
            "obblighi normativi applicabili."
        )

        st.divider()
        st.subheader("5. Distribuzione degli impatti")
        st.dataframe(
            analysis["results_df"],
            hide_index=True,
            use_container_width=True,
        )

        st.markdown("#### Domanda e acqua assegnata")
        st.bar_chart(
            analysis["results_df"].set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

        st.markdown("#### Distribuzione del deficit")
        st.bar_chart(
            analysis["results_df"].set_index("Settore")[["Deficit (hm³)"]]
        )

        st.divider()
        st.subheader("6. Sintesi dell'analisi")
        st.write(
            f"La strategia selezionata è **{selected_strategy.lower()}**. "
            f"Su una disponibilità di **{availability:.1f} hm³**, "
            f"il modello assegna **{analysis['total_allocated']:.1f} hm³**."
        )
        st.write(
            f"Il deficit complessivo è **{analysis['total_shortage']:.1f} hm³**. "
            f"Il deficit produttivo (agricoltura e industria) è "
            f"**{analysis['productive_shortage']:.2f} hm³**; "
            f"la copertura degli usi civili è "
            f"**{analysis['civil_coverage']:.1f}%**."
        )
        st.caption(
            "L'analisi organizza indicatori quantitativi e supporta il confronto "
            "tra scenari. Non formula decisioni automatiche né sostituisce "
            "le autorità competenti."
        )

# ============================================================
# 04 - DECISION REPORT
# ============================================================

elif page == "Decision Report":
    st.title("Decision Report")
    st.write(
        "Documento strutturato per organizzare i parametri, i risultati "
        "dell'allocazione, gli indicatori e il confronto tra strategie."
    )
    st.info(
        "Il report utilizza i parametri correnti dell'Allocation Simulator. "
        "I valori del prototipo sono simulati e non costituiscono dati ufficiali."
    )

    if total_minimum > availability + 1e-9:
        st.error(
            "Impossibile generare il report: le quote minime superano "
            "la disponibilità idrica. Correggi lo scenario nell'Allocation Simulator."
        )
    elif not priority_valid:
        st.error(
            "Impossibile generare il report: l'ordine delle priorità non è valido. "
            "Ogni settore deve comparire una sola volta nell'Allocation Simulator."
        )
    else:
        report_strategy_name = st.selectbox(
            "Strategia da approfondire nel report",
            ["Allocazione proporzionale", "Allocazione per priorità"],
            key="report_strategy",
        )
        report_strategy = (
            "proporzionale"
            if report_strategy_name == "Allocazione proporzionale"
            else "priorità"
        )

        report_analysis = build_analysis(
            availability, demands, minimums, priority, report_strategy
        )
        proportional_analysis, priority_analysis, comparison_df = build_comparison(
            availability, demands, minimums, priority
        )

        st.caption(
            "Il report usa gli stessi parametri e le stesse funzioni di calcolo "
            "dell'Allocation Simulator e dell'Impact Analysis."
        )

        st.divider()
        st.subheader("1. Sintesi dello scenario")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Disponibilità", f"{availability:.1f} hm³")
        r2.metric("Domanda totale", f"{report_analysis['total_demand']:.1f} hm³")
        r3.metric("Acqua assegnata", f"{report_analysis['total_allocated']:.1f} hm³")
        r4.metric("Deficit complessivo", f"{report_analysis['total_shortage']:.1f} hm³")

        st.write(f"**Territorio:** {TERRITORY}")
        st.write(f"**Regione:** {REGION}")
        st.write(f"**Strategia approfondita:** {report_strategy_name}")
        st.write(f"**Copertura complessiva:** {report_analysis['coverage']:.1f}%")

        st.divider()
        st.subheader("2. Risultati dell'allocazione")
        st.dataframe(
            report_analysis["results_df"],
            hide_index=True,
            use_container_width=True,
        )
        st.bar_chart(
            report_analysis["results_df"].set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

        st.divider()
        st.subheader("3. Indicatori di impatto")
        impact1, impact2, impact3 = st.columns(3)

        with impact1:
            st.markdown("**Settori produttivi**")
            st.metric(
                "Deficit produttivo",
                f"{report_analysis['productive_shortage']:.2f} hm³",
            )
            st.caption("Volume non soddisfatto in agricoltura e industria; non è una perdita in euro.")

        with impact2:
            st.markdown("**Usi civili**")
            st.metric(
                "Copertura civile",
                f"{report_analysis['civil_coverage']:.1f}%",
            )
            st.caption(
                f"Deficit: {report_analysis['civil_shortage']:.2f} hm³"
            )

        with impact3:
            st.markdown("**Parametro ambientale**")
            st.metric(
                "Quota minima ipotizzata",
                f"{report_analysis['environmental_minimum']:.2f} hm³",
            )
            st.caption(
                f"Assegnata: {report_analysis['environmental_allocated']:.2f} hm³"
            )

        st.warning(
            "La quota ambientale è un parametro di scenario imposto dal modello. "
            "Il suo rispetto non costituisce una verifica del deflusso ecologico "
            "o della conformità normativa."
        )

        st.divider()
        st.subheader("4. Confronto tra strategie")
        st.dataframe(
            comparison_df,
            hide_index=True,
            use_container_width=True,
        )

        st.divider()
        st.subheader("5. Considerazioni per la valutazione")
        st.write(
            f"La strategia approfondita è **{report_strategy_name.lower()}**. "
            f"Il deficit complessivo risultante è "
            f"**{report_analysis['total_shortage']:.2f} hm³**."
        )

        if report_analysis["civil_shortage"] > 1e-6:
            st.warning(
                "La domanda civile inserita non è interamente soddisfatta. "
                "È necessario approfondire la tutela dei fabbisogni essenziali."
            )
        else:
            st.info(
                "La domanda civile inserita risulta interamente soddisfatta "
                "nei limiti delle ipotesi del modello."
            )

        if report_strategy == "priorità":
            st.write("**Ordine di priorità applicato:** " + " > ".join(priority))
        else:
            st.write(
                "**Ordine di priorità:** non applicabile alla strategia "
                "proporzionale."
            )

        st.caption(
            "Le considerazioni sono indicatori di supporto, non raccomandazioni "
            "automatiche. La valutazione finale compete alle autorità responsabili."
        )

        st.divider()
        st.subheader("6. Esportazione del documento")
        st.write(
            "Il PDF contiene sintesi, parametri, risultati settoriali, "
            "indicatori, confronto tra strategie e limiti del prototipo."
        )

        pdf_bytes = generate_pdf_report(
            report_analysis,
            availability,
            demands,
            minimums,
            report_strategy_name,
            priority,
            comparison_df,
        )

        st.download_button(
            label="📄 Scarica Decision Report in PDF",
            data=pdf_bytes,
            file_name="AQUA_COMMONS_AI_Decision_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.caption(
            "Il documento è generato dai dati dello scenario corrente. "
            "Se modifichi i parametri, il report si aggiorna al successivo ricalcolo."
        )
