# ============================================================
# AQUA COMMONS AI
# INTEGRATED WATER INTELLIGENCE AND DECISION SUPPORT
# Applicazione principale
# ============================================================

import streamlit as st
import pandas as pd

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import cm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ============================================================
# CORE
# ============================================================

from core.config import (
    APP_NAME,
    APP_DESCRIPTION,
    SECTORS,
    DEFAULT_DEMAND,
    DEFAULT_MINIMUM,
    DEFAULT_AVAILABILITY,
    PILOT_TERRITORY,
    PILOT_REGION,
)

from core.data_manager import load_data

from core.allocation import (
    calculate_results,
)

from core.impact import (
    calculate_global_impacts,
    calculate_sector_impacts,
    generate_impact_summary,
)

from core.ai_engine import (
    run_integrated_analysis,
)

# ============================================================
# SERVICES
# ============================================================

from services.monitoring import (
    run_integrated_monitoring,
)

from services.drought import (
    run_drought_assessment,
)

from services.map_service import (
    display_map,
)


# ============================================================
# CONFIGURAZIONE STREAMLIT
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STILE GRAFICO
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f5f8fc;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #12304a;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e2eaf2;
        padding: 16px;
        border-radius: 12px;
    }

    .info-box {
        background-color: #eaf3fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2384b8;
        margin-bottom: 15px;
    }

    .warning-box {
        background-color: #fff4df;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #e49b24;
        margin-bottom: 15px;
    }

    .success-box {
        background-color: #e9f6ef;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #27965b;
        margin-bottom: 15px;
    }

    .small-text {
        color: #64748b;
        font-size: 0.85rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIGURAZIONE GENERALE
# ============================================================

DATA_MODE = "simulated"

GENERIC_TERRITORY = "Territorio dimostrativo"
GENERIC_REGION = "Italia"

PILOT_MODE_LABEL = "Analisi territoriale"

DISCLAIMER = (
    "I valori visualizzati nella versione dimostrativa sono simulati "
    "e non rappresentano misurazioni ufficiali del territorio. "
    "Le analisi sono basate su regole deterministiche e non costituiscono "
    "previsioni scientifiche o decisioni amministrative automatiche."
)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():

    if "platform_mode" not in st.session_state:
        st.session_state.platform_mode = "Demo generica"

    if "scenario_availability" not in st.session_state:
        st.session_state.scenario_availability = float(
            DEFAULT_AVAILABILITY
        )

    for sector in SECTORS:

        demand_key = f"scenario_demand_{sector}"
        minimum_key = f"scenario_minimum_{sector}"

        if demand_key not in st.session_state:
            st.session_state[demand_key] = float(
                DEFAULT_DEMAND[sector]
            )

        if minimum_key not in st.session_state:
            st.session_state[minimum_key] = float(
                DEFAULT_MINIMUM[sector]
            )


initialize_session_state()


# ============================================================
# FUNZIONI GENERALI
# ============================================================

def get_territory():

    if st.session_state.platform_mode == PILOT_MODE_LABEL:

        return (
            PILOT_TERRITORY,
            PILOT_REGION,
        )

    return (
        GENERIC_TERRITORY,
        GENERIC_REGION,
    )


def format_number(value, decimals=1):

    try:

        return (
            f"{float(value):,.{decimals}f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except (TypeError, ValueError):

        return "N/D"


def get_scenario_inputs():

    availability = float(
        st.session_state.scenario_availability
    )

    demands = {
        sector: float(
            st.session_state[f"scenario_demand_{sector}"]
        )
        for sector in SECTORS
    }

    minimums = {
        sector: float(
            st.session_state[f"scenario_minimum_{sector}"]
        )
        for sector in SECTORS
    }

    return availability, demands, minimums


def validate_scenario(
    availability,
    demands,
    minimums,
):

    errors = []

    if availability < 0:

        errors.append(
            "La disponibilità idrica non può essere negativa."
        )

    for sector in SECTORS:

        if demands[sector] < 0:

            errors.append(
                f"La domanda di {sector} non può essere negativa."
            )

        if minimums[sector] < 0:

            errors.append(
                f"Il fabbisogno minimo di {sector} non può essere negativo."
            )

        if minimums[sector] > demands[sector]:

            errors.append(
                f"Il fabbisogno minimo di {sector} supera la domanda."
            )

    if sum(minimums.values()) > availability:

        errors.append(
            "La disponibilità idrica non è sufficiente "
            "a rispettare tutti i fabbisogni minimi."
        )

    return errors


def get_analysis_data():

    return load_data(DATA_MODE)


# ============================================================
# FORMATTAZIONE DEI RISULTATI
# ============================================================

def build_results_dataframe(results):

    rows = []

    for sector in SECTORS:

        values = results["sectors"][sector]

        rows.append({
            "Settore": sector,
            "Domanda (hm³)": values["demand"],
            "Fabbisogno minimo (hm³)": values["minimum"],
            "Acqua assegnata (hm³)": values["allocated"],
            "Carenza (hm³)": values["shortage"],
            "Copertura (%)": values["coverage"],
        })

    return pd.DataFrame(rows)


def display_results_metrics(results):

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Disponibilità",
        f"{format_number(results['availability'])} hm³",
    )

    col2.metric(
        "Domanda totale",
        f"{format_number(results['total_demand'])} hm³",
    )

    col3.metric(
        "Acqua assegnata",
        f"{format_number(results['total_allocated'])} hm³",
    )

    col4.metric(
        "Carenza complessiva",
        f"{format_number(results['total_shortage'])} hm³",
    )


def display_decision_explanation(explanation):

    """
    Trasforma la spiegazione decisionale in testo leggibile.
    Gestisce liste, dizionari e stringhe.
    """

    if isinstance(explanation, list):

        for item in explanation:

            if isinstance(item, str):

                st.markdown(f"- {item}")

            elif isinstance(item, dict):

                for key, value in item.items():

                    label = key.replace("_", " ").capitalize()

                    st.markdown(
                        f"- **{label}:** {value}"
                    )

            else:

                st.markdown(f"- {str(item)}")

    elif isinstance(explanation, dict):

        for key, value in explanation.items():

            label = key.replace("_", " ").capitalize()

            st.markdown(
                f"**{label}:** {value}"
            )

    elif isinstance(explanation, str):

        st.write(explanation)

    else:

        st.info(
            "Non è disponibile una spiegazione decisionale."
        )


def display_water_risk(water_risk):

    """
    Visualizza la valutazione del rischio in forma leggibile.
    """

    if not isinstance(water_risk, dict):

        st.info(
            "Non è disponibile una valutazione del rischio."
        )

        return

    risk_level = water_risk.get(
        "risk_level",
        "N/D",
    )

    shortage_percentage = water_risk.get(
        "shortage_percentage",
        0,
    )

    total_shortage = water_risk.get(
        "total_shortage",
        0,
    )

    total_demand = water_risk.get(
        "total_demand",
        0,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Livello di rischio",
        str(risk_level),
    )

    col2.metric(
        "Domanda non soddisfatta",
        f"{format_number(shortage_percentage)}%",
    )

    col3.metric(
        "Carenza idrica",
        f"{format_number(total_shortage)} hm³",
    )

    st.caption(
        f"Domanda complessiva: {format_number(total_demand)} hm³."
    )

    method = water_risk.get("method")

    if method:

        st.info(method)


def display_impact_summary(summary):

    """
    Visualizza gli impatti attraverso metriche e testi,
    evitando la stampa diretta di dizionari Python.
    """

    if not isinstance(summary, dict):

        st.info(
            "La sintesi degli impatti non è disponibile "
            "in un formato strutturato."
        )

        if isinstance(summary, list):

            for item in summary:
                st.markdown(f"- {item}")

        elif isinstance(summary, str):

            st.write(summary)

        return

    st.markdown(
        "#### Quadro generale degli impatti"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Copertura complessiva",
        f"{format_number(summary.get('overall_coverage', 0))}%",
    )

    col2.metric(
        "Carenza complessiva",
        f"{format_number(summary.get('total_shortage', 0))} hm³",
    )

    col3.metric(
        "Differenza di copertura",
        f"{format_number(summary.get('coverage_gap', 0))} punti",
    )

    st.divider()

    st.markdown(
        "#### Distribuzione degli impatti"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "**Settore maggiormente colpito**"
        )

        st.write(
            summary.get(
                "most_affected_sector",
                "N/D",
            )
        )

        st.metric(
            "Carenza del settore",
            f"{format_number(summary.get('most_affected_shortage', 0))} hm³",
        )

    with col2:

        st.markdown(
            "**Settore con maggiore copertura**"
        )

        st.write(
            summary.get(
                "best_covered_sector",
                "N/D",
            )
        )

        st.metric(
            "Copertura del settore",
            f"{format_number(summary.get('best_covered_percentage', 0))}%",
        )

    st.divider()

    if summary.get("minimums_respected") is True:

        st.success(
            "Tutti i fabbisogni minimi impostati risultano rispettati."
        )

    elif summary.get("minimums_respected") is False:

        st.warning(
            "Uno o più fabbisogni minimi non risultano rispettati."
        )


# ============================================================
# GENERAZIONE PDF
# ============================================================

def create_pdf_report(
    territory,
    region,
    results,
    impacts,
    strategy,
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

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            textColor=colors.HexColor("#12304a"),
            spaceAfter=15,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#176b87"),
            spaceBefore=15,
            spaceAfter=8,
        )
    )

    story = []

    story.append(
        Paragraph(
            "AQUA COMMONS AI",
            styles["ReportTitle"],
        )
    )

    story.append(
        Paragraph(
            "Integrated Water Intelligence and Decision Support Platform",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f"<b>Territorio:</b> {territory}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Regione:</b> {region}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Strategia:</b> {strategy}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # QUADRO GENERALE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "1. Quadro generale",
            styles["SectionTitle"],
        )
    )

    general_data = [
        ["Indicatore", "Valore"],
        [
            "Disponibilità idrica",
            f"{format_number(results['availability'])} hm³",
        ],
        [
            "Domanda complessiva",
            f"{format_number(results['total_demand'])} hm³",
        ],
        [
            "Acqua assegnata",
            f"{format_number(results['total_allocated'])} hm³",
        ],
        [
            "Carenza complessiva",
            f"{format_number(impacts['total_shortage'])} hm³",
        ],
        [
            "Acqua non assegnata",
            f"{format_number(results['unused_water'])} hm³",
        ],
    ]

    general_table = Table(
        general_data,
        colWidths=[
            9 * cm,
            7 * cm,
        ],
    )

    general_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#12304a"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#ccd6e0"),
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.HexColor("#f4f8fb"),
            ),
        ])
    )

    story.append(general_table)

    # --------------------------------------------------------
    # DISTRIBUZIONE SETTORIALE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "2. Distribuzione settoriale",
            styles["SectionTitle"],
        )
    )

    sector_data = [[
        "Settore",
        "Domanda",
        "Minimo",
        "Assegnazione",
        "Carenza",
    ]]

    for sector in SECTORS:

        values = results["sectors"][sector]

        sector_data.append([
            sector,
            format_number(values["demand"]),
            format_number(values["minimum"]),
            format_number(values["allocated"]),
            format_number(values["shortage"]),
        ])

    sector_table = Table(
        sector_data,
        colWidths=[
            4 * cm,
            2.5 * cm,
            2.5 * cm,
            3.5 * cm,
            2.5 * cm,
        ],
    )

    sector_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#176b87"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#ccd6e0"),
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.HexColor("#f4f8fb"),
            ),
        ])
    )

    story.append(sector_table)

    # --------------------------------------------------------
    # IMPATTI
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "3. Interpretazione degli impatti",
            styles["SectionTitle"],
        )
    )

    summary = generate_impact_summary(results)

    if isinstance(summary, dict):

        impact_text = (
            f"Copertura complessiva: "
            f"{format_number(summary.get('overall_coverage', 0))}%. "
            f"Carenza complessiva: "
            f"{format_number(summary.get('total_shortage', 0))} hm³. "
            f"Settore maggiormente colpito: "
            f"{summary.get('most_affected_sector', 'N/D')}. "
            f"Settore con maggiore copertura: "
            f"{summary.get('best_covered_sector', 'N/D')}."
        )

    elif isinstance(summary, list):

        impact_text = " ".join(
            str(item) for item in summary
        )

    else:

        impact_text = str(summary)

    story.append(
        Paragraph(
            impact_text,
            styles["Normal"],
        )
    )

    # --------------------------------------------------------
    # NOTA METODOLOGICA
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "4. Nota metodologica",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            DISCLAIMER,
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Il presente documento costituisce uno strumento "
            "di supporto all'analisi. Le decisioni definitive "
            "restano di competenza delle autorità responsabili.",
            styles["Normal"],
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("# 💧 AQUA COMMONS AI")

    st.caption(
        "Integrated Water Intelligence"
    )

    st.divider()

    st.markdown(
        "### Configurazione"
    )

    st.selectbox(
        "Modalità territoriale",
        [
            "Demo generica",
            PILOT_MODE_LABEL,
        ],
        key="platform_mode",
    )

    territory, region = get_territory()

    st.caption(
        f"Territorio: {territory}"
    )

    st.caption(
        f"Regione: {region}"
    )

    st.divider()

    page = st.radio(
        "Navigazione",
        [
            "Overview Dashboard",
            "Integrated Monitoring",
            "Drought Early Warning",
            "Geographical Intelligence",
            "Allocation Simulator",
            "Impact Analysis",
            "Decision Report",
        ],
    )

    st.divider()

    st.caption(
        "AQUA COMMONS AI"
    )

    st.caption(
        "Human-centred water governance"
    )


# ============================================================
# HEADER GENERALE
# ============================================================

territory, region = get_territory()

st.title(
    "💧 AQUA COMMONS AI"
)

st.markdown(
    APP_DESCRIPTION
)

st.caption(
    f"Territorio analizzato: {territory} | {region}"
)

st.markdown(
    f"""
    <div class="warning-box">
    <b>Modalità dimostrativa:</b> {DISCLAIMER}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 1. OVERVIEW DASHBOARD
# ============================================================

if page == "Overview Dashboard":

    st.header(
        "Overview Dashboard"
    )

    st.write(
        "Una visione sintetica della disponibilità idrica, "
        "della domanda settoriale e delle condizioni di allocazione."
    )

    availability, demands, minimums = get_scenario_inputs()

    errors = validate_scenario(
        availability,
        demands,
        minimums,
    )

    if errors:

        for error in errors:
            st.error(error)

    else:

        results = calculate_results(
            availability,
            demands,
            minimums,
            strategy="proportional",
        )

        display_results_metrics(results)

        st.divider()

        col1, col2 = st.columns([1.4, 1])

        with col1:

            st.subheader(
                "Distribuzione idrica"
            )

            dataframe = build_results_dataframe(
                results
            )

            chart_data = dataframe.set_index(
                "Settore"
            )[
                [
                    "Domanda (hm³)",
                    "Acqua assegnata (hm³)",
                ]
            ]

            st.bar_chart(chart_data)

        with col2:

            st.subheader(
                "Indicatori di sistema"
            )

            coverage = (
                results["total_allocated"]
                / results["total_demand"] * 100
                if results["total_demand"] > 0
                else 100
            )

            st.metric(
                "Copertura della domanda",
                f"{format_number(coverage)}%",
            )

            st.metric(
                "Carenza idrica",
                f"{format_number(results['total_shortage'])} hm³",
            )

            if results["total_minimum"] <= results["total_allocated"]:

                st.success(
                    "I fabbisogni minimi risultano rispettati."
                )

            else:

                st.error(
                    "I fabbisogni minimi non risultano rispettati."
                )

        st.divider()

        st.subheader(
            "Quadro settoriale"
        )

        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader(
        "Qualità e provenienza dei dati"
    )

    try:

        data = get_analysis_data()

        if data.empty:

            st.info(
                "Non sono disponibili record nel dataset selezionato."
            )

        else:

            st.metric(
                "Record disponibili",
                len(data),
            )

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as error:

        st.error(
            f"Impossibile caricare i dati: {error}"
        )


# ============================================================
# 2. INTEGRATED MONITORING
# ============================================================

elif page == "Integrated Monitoring":

    st.header(
        "Integrated Monitoring"
    )

    st.write(
        "Monitoraggio integrato delle condizioni idrologiche, "
        "climatiche e territoriali."
    )

    if st.button(
        "Aggiorna monitoraggio",
        type="primary",
    ):

        st.rerun()

    try:

        with st.spinner(
            "Elaborazione dei dati integrati..."
        ):

            monitoring_result = run_integrated_monitoring(
                mode=DATA_MODE
            )

        monitoring = monitoring_result["monitoring"]

        summary = monitoring_result["summary"]

        alerts = monitoring_result["alerts"]

        st.success(
            "Monitoraggio elaborato correttamente."
        )

        st.divider()

        st.subheader(
            "Indicatori principali"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Indice di attenzione",
            f"{format_number(summary.get('attention_index', 0))}/100",
        )

        col2.metric(
            "Livello di attenzione",
            str(summary.get("attention_level", "N/D")),
        )

        col3.metric(
            "Segnali rilevati",
            summary.get("signal_count", 0),
        )

        col4.metric(
            "Punti geografici",
            summary.get("monitoring_points", 0),
        )

        st.divider()

        st.subheader(
            "Condizioni idrologiche e climatiche"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "#### Idrologia"
            )

            st.write(
                "Variazione portata fluviale:",
                f"{format_number(summary.get('river_flow_variation', 0))}%",
            )

            st.write(
                "Variazione invasi:",
                f"{format_number(summary.get('reservoir_variation', 0))}%",
            )

            st.write(
                "Variazione falde:",
                f"{format_number(summary.get('groundwater_variation', 0))}%",
            )

        with col2:

            st.markdown(
                "#### Clima"
            )

            st.write(
                "Deficit pluviometrico:",
                f"{format_number(summary.get('rainfall_deficit', 0))}%",
            )

            st.write(
                "Anomalia termica:",
                f"{format_number(summary.get('temperature_anomaly', 0))} °C",
            )

        st.divider()

        st.subheader(
            "Provenienza dei dati"
        )

        provenance = monitoring.get(
            "provenance",
            {},
        )

        st.write(
            "Stato:",
            summary.get(
                "data_status",
                provenance.get("status", "simulated"),
            ),
        )

        sources = summary.get(
            "data_sources",
            provenance.get("sources", []),
        )

        if isinstance(sources, list):

            st.write(
                "Fonti:",
                ", ".join(str(source) for source in sources),
            )

        else:

            st.write(
                "Fonti:",
                str(sources),
            )

        st.caption(
            f"Record temporali disponibili: "
            f"{summary.get('data_records', 0)}"
        )

        st.divider()

        st.subheader(
            "Serie temporali integrate"
        )

        integrated_series = monitoring.get(
            "integrated_series"
        )

        if (
            isinstance(integrated_series, pd.DataFrame)
            and not integrated_series.empty
        ):

            st.dataframe(
                integrated_series,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "Non sono disponibili serie temporali integrate."
            )

        st.divider()

        st.subheader(
            "Segnalazioni del sistema"
        )

        if alerts:

            for alert in alerts:

                if isinstance(alert, dict):

                    message = alert.get(
                        "message",
                        "Segnalazione disponibile.",
                    )

                    level = str(
                        alert.get("level", "info")
                    ).lower()

                    if level in [
                        "critical",
                        "high",
                        "elevato",
                    ]:

                        st.error(message)

                    elif level in [
                        "warning",
                        "moderate",
                        "moderato",
                    ]:

                        st.warning(message)

                    else:

                        st.info(message)

                else:

                    st.info(str(alert))

        else:

            st.info(
                "Non sono presenti segnalazioni."
            )

    except Exception as error:

        st.error(
            f"Errore durante il monitoraggio integrato: {error}"
        )


# ============================================================
# 3. DROUGHT EARLY WARNING
# ============================================================

elif page == "Drought Early Warning":

    st.header(
        "Drought Early Warning System"
    )

    st.write(
        "Individuazione di condizioni potenzialmente critiche "
        "attraverso indicatori idrologici e climatici."
    )

    try:

        with st.spinner(
            "Valutazione delle condizioni di stress idrico..."
        ):

            drought = run_drought_assessment(
                mode=DATA_MODE
            )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Indice di attenzione",
            f"{format_number(drought['attention_index'])}/100",
        )

        col2.metric(
            "Livello di attenzione",
            drought["attention_level"],
        )

        col3.metric(
            "Segnali rilevati",
            drought["signal_count"],
        )

        st.divider()

        st.subheader(
            "Indicatori di stress idrico"
        )

        signals = drought.get(
            "all_signals",
            [],
        )

        if signals:

            signal_rows = []

            for signal in signals:

                if isinstance(signal, dict):

                    signal_rows.append({
                        "Indicatore": signal.get(
                            "indicator",
                            signal.get("name", "N/D"),
                        ),
                        "Valore": signal.get(
                            "value",
                            "N/D",
                        ),
                        "Soglia": signal.get(
                            "threshold",
                            "N/D",
                        ),
                        "Condizione": signal.get(
                            "status",
                            signal.get("message", "N/D"),
                        ),
                    })

            if signal_rows:

                st.dataframe(
                    pd.DataFrame(signal_rows),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "I segnali sono disponibili ma non presentano "
                    "una struttura tabellare."
                )

        else:

            st.info(
                "Non sono stati rilevati segnali di attenzione."
            )

        st.divider()

        st.subheader(
            "Raccomandazioni preventive"
        )

        recommendations = drought.get(
            "recommendations",
            [],
        )

        if recommendations:

            for recommendation in recommendations:

                if isinstance(recommendation, str):

                    st.markdown(
                        f"- {recommendation}"
                    )

                else:

                    st.markdown(
                        f"- {str(recommendation)}"
                    )

        else:

            st.info(
                "Non sono disponibili raccomandazioni."
            )

        st.divider()

        st.subheader(
            "Metodo di valutazione"
        )

        st.write(
            drought.get(
                "method",
                "Sistema deterministico basato su soglie e pesi dimostrativi.",
            )
        )

        st.warning(
            "L'indice è un indicatore sperimentale di attenzione. "
            "Le soglie e i pesi sono dimostrativi e non rappresentano "
            "un indice scientifico ufficialmente calibrato. "
            "Il sistema non effettua previsioni di siccità."
        )

    except Exception as error:

        st.error(
            f"Errore nella valutazione della siccità: {error}"
        )


# ============================================================
# 4. GEOGRAPHICAL INTELLIGENCE
# ============================================================

elif page == "Geographical Intelligence":

    st.header(
        "Geographical Intelligence"
    )

    st.write(
        "Visualizzazione geografica dei punti di monitoraggio "
        "idrologico, climatico e territoriale."
    )

    st.markdown(
        """
        <div class="info-box">
        La mappa permette di esplorare la distribuzione geografica
        degli indicatori e delle infrastrutture monitorate.
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        display_map(
            st,
            mode=DATA_MODE,
        )

    except Exception as error:

        st.error(
            f"Errore durante la visualizzazione geografica: {error}"
        )

    st.warning(
        "Le coordinate mostrate nella demo sono illustrative "
        "e non identificano necessariamente stazioni o infrastrutture reali."
    )


# ============================================================
# 5. ALLOCATION SIMULATOR
# ============================================================

elif page == "Allocation Simulator":

    st.header(
        "Water Allocation Simulator"
    )

    st.write(
        "Simula la distribuzione della risorsa idrica tra i diversi "
        "settori e confronta strategie alternative."
    )

    st.subheader(
        "1. Disponibilità idrica"
    )

    availability = st.number_input(
        "Risorsa idrica disponibile (hm³)",
        min_value=0.0,
        max_value=100000.0,
        step=1.0,
        key="availability_input",
        value=float(
            st.session_state.scenario_availability
        ),
    )

    st.session_state.scenario_availability = availability

    st.subheader(
        "2. Domanda e fabbisogni minimi"
    )

    for sector in SECTORS:

        col1, col2 = st.columns(2)

        with col1:

            demand = st.number_input(
                f"Domanda - {sector} (hm³)",
                min_value=0.0,
                max_value=100000.0,
                step=1.0,
                key=f"demand_input_{sector}",
                value=float(
                    st.session_state[f"scenario_demand_{sector}"]
                ),
            )

        with col2:

            minimum = st.number_input(
                f"Fabbisogno minimo - {sector} (hm³)",
                min_value=0.0,
                max_value=100000.0,
                step=1.0,
                key=f"minimum_input_{sector}",
                value=float(
                    st.session_state[f"scenario_minimum_{sector}"]
                ),
            )

        st.session_state[
            f"scenario_demand_{sector}"
        ] = demand

        st.session_state[
            f"scenario_minimum_{sector}"
        ] = minimum

    demands = {
        sector: st.session_state[
            f"scenario_demand_{sector}"
        ]
        for sector in SECTORS
    }

    minimums = {
        sector: st.session_state[
            f"scenario_minimum_{sector}"
        ]
        for sector in SECTORS
    }

    errors = validate_scenario(
        availability,
        demands,
        minimums,
    )

    if errors:

        for error in errors:
            st.error(error)

    else:

        st.success(
            "Parametri dello scenario validi."
        )

        st.divider()

        st.subheader(
            "3. Confronto delle strategie"
        )

        proportional_results = calculate_results(
            availability,
            demands,
            minimums,
            strategy="proportional",
        )

        priority_order = st.multiselect(
            "Ordine di priorità per l'allocazione",
            options=SECTORS,
            default=list(SECTORS),
            max_selections=len(SECTORS),
        )

        if len(priority_order) != len(SECTORS):

            st.warning(
                "Seleziona tutti i settori per completare "
                "il confronto delle strategie."
            )

        else:

            priority_results = calculate_results(
                availability,
                demands,
                minimums,
                strategy="priority",
                priority_order=priority_order,
            )

            tab1, tab2 = st.tabs([
                "Allocazione proporzionale",
                "Allocazione per priorità",
            ])

            with tab1:

                st.subheader(
                    "Distribuzione proporzionale"
                )

                display_results_metrics(
                    proportional_results
                )

                st.dataframe(
                    build_results_dataframe(
                        proportional_results
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.bar_chart(
                    build_results_dataframe(
                        proportional_results
                    ).set_index("Settore")[
                        [
                            "Domanda (hm³)",
                            "Acqua assegnata (hm³)",
                        ]
                    ]
                )

            with tab2:

                st.subheader(
                    "Distribuzione secondo le priorità"
                )

                display_results_metrics(
                    priority_results
                )

                st.dataframe(
                    build_results_dataframe(
                        priority_results
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.bar_chart(
                    build_results_dataframe(
                        priority_results
                    ).set_index("Settore")[
                        [
                            "Domanda (hm³)",
                            "Acqua assegnata (hm³)",
                        ]
                    ]
                )

            st.divider()

            st.subheader(
                "Differenze tra le strategie"
            )

            comparison_rows = []

            for sector in SECTORS:

                proportional = (
                    proportional_results["sectors"][sector]["allocated"]
                )

                priority = (
                    priority_results["sectors"][sector]["allocated"]
                )

                comparison_rows.append({
                    "Settore": sector,
                    "Proporzionale": proportional,
                    "Per priorità": priority,
                    "Differenza": priority - proportional,
                })

            st.dataframe(
                pd.DataFrame(comparison_rows),
                use_container_width=True,
                hide_index=True,
            )

            st.info(
                "Le strategie sono strumenti di confronto. "
                "L'ordine di priorità deve riflettere vincoli normativi, "
                "fabbisogni essenziali e obiettivi definiti "
                "dall'autorità competente."
            )


# ============================================================
# 6. IMPACT ANALYSIS
# ============================================================

elif page == "Impact Analysis":

    st.header(
        "Impact Analysis"
    )

    st.write(
        "Valutazione degli effetti distributivi delle diverse "
        "strategie di allocazione."
    )

    availability, demands, minimums = get_scenario_inputs()

    errors = validate_scenario(
        availability,
        demands,
        minimums,
    )

    if errors:

        for error in errors:
            st.error(error)

    else:

        strategy_choice = st.selectbox(
            "Strategia da analizzare",
            [
                "Proporzionale",
                "Per priorità",
            ],
            key="impact_strategy",
        )

        if strategy_choice == "Proporzionale":

            results = calculate_results(
                availability,
                demands,
                minimums,
                strategy="proportional",
            )

        else:

            priority_order = st.multiselect(
                "Ordine di priorità",
                options=SECTORS,
                default=list(SECTORS),
                max_selections=len(SECTORS),
                key="impact_priority_order",
            )

            if len(priority_order) != len(SECTORS):

                st.warning(
                    "Seleziona tutti i settori per procedere."
                )

                results = None

            else:

                results = calculate_results(
                    availability,
                    demands,
                    minimums,
                    strategy="priority",
                    priority_order=priority_order,
                )

        if results is not None:

            impacts = calculate_global_impacts(
                results
            )

            sector_impacts = calculate_sector_impacts(
                results
            )

            st.divider()

            st.subheader(
                "Indicatori globali"
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Domanda complessiva",
                f"{format_number(impacts['total_demand'])} hm³",
            )

            col2.metric(
                "Carenza complessiva",
                f"{format_number(impacts['total_shortage'])} hm³",
            )

            col3.metric(
                "Risorsa assegnata",
                f"{format_number(impacts['total_allocated'])} hm³",
            )

            st.divider()

            st.subheader(
                "Impatto per settore"
            )

            impact_rows = []

            for sector in SECTORS:

                impact = sector_impacts[sector]

                allocation = results["sectors"][sector]

                impact_rows.append({
                    "Settore": sector,
                    "Domanda": allocation["demand"],
                    "Assegnazione": allocation["allocated"],
                    "Carenza": allocation["shortage"],
                    "Copertura (%)": allocation["coverage"],
                })

            impact_df = pd.DataFrame(
                impact_rows
            )

            st.dataframe(
                impact_df,
                use_container_width=True,
                hide_index=True,
            )

            st.bar_chart(
                impact_df.set_index("Settore")[
                    ["Carenza"]
                ]
            )

            st.divider()

            st.subheader(
                "Analisi deterministica"
            )

            try:

                data = get_analysis_data()

                analysis = run_integrated_analysis(
                    data,
                    results,
                )

                data_quality = analysis.get(
                    "data_quality",
                    {},
                )

                water_risk = analysis.get(
                    "water_risk",
                    {},
                )

                st.markdown(
                    "#### Qualità dei dati"
                )

                if isinstance(data_quality, dict):

                    status = data_quality.get(
                        "status",
                        "N/D",
                    )

                    st.metric(
                        "Provenienza dei dati",
                        str(status).capitalize(),
                    )

                    sources = data_quality.get(
                        "sources",
                        [],
                    )

                    if sources:

                        st.caption(
                            "Fonti: "
                            + ", ".join(
                                str(source)
                                for source in sources
                            )
                        )

                else:

                    st.write(
                        str(data_quality)
                    )

                st.markdown(
                    "#### Valutazione del rischio"
                )

                display_water_risk(
                    water_risk
                )

                st.divider()

                st.markdown(
                    "#### Metodo di analisi"
                )

                st.write(
                    "Analisi basata su regole deterministiche."
                )

                if analysis.get("is_predictive_model") is False:

                    st.caption(
                        "Il sistema non utilizza un modello predittivo "
                        "addestrato. Le valutazioni sono ottenute "
                        "attraverso regole e calcoli deterministici."
                    )

            except Exception as error:

                st.error(
                    f"Errore nell'analisi integrata: {error}"
                )

            st.divider()

            st.subheader(
                "Interpretazione degli impatti"
            )

            try:

                summary = generate_impact_summary(
                    results
                )

                display_impact_summary(
                    summary
                )

            except Exception as error:

                st.error(
                    f"Impossibile generare la sintesi degli impatti: {error}"
                )

            st.divider()

            st.warning(
                "La piattaforma non attribuisce automaticamente "
                "valori monetari ai danni economici e sociali. "
                "Gli impatti economici richiedono dati territoriali "
                "e settoriali verificati."
            )


# ============================================================
# 7. DECISION REPORT
# ============================================================

elif page == "Decision Report":

    st.header(
        "Decision Report"
    )

    st.write(
        "Generazione di un report sintetico a supporto "
        "della valutazione delle decisioni di allocazione."
    )

    availability, demands, minimums = get_scenario_inputs()

    errors = validate_scenario(
        availability,
        demands,
        minimums,
    )

    if errors:

        for error in errors:
            st.error(error)

    else:

        strategy_choice = st.selectbox(
            "Strategia di allocazione per il report",
            [
                "Proporzionale",
                "Per priorità",
            ],
            key="report_strategy",
        )

        priority_order = list(SECTORS)

        if strategy_choice == "Per priorità":

            priority_order = st.multiselect(
                "Ordine di priorità",
                options=SECTORS,
                default=list(SECTORS),
                max_selections=len(SECTORS),
                key="report_priority_order",
            )

        if (
            strategy_choice == "Per priorità"
            and len(priority_order) != len(SECTORS)
        ):

            st.warning(
                "Seleziona tutti i settori per generare il report."
            )

        else:

            if strategy_choice == "Proporzionale":

                results = calculate_results(
                    availability,
                    demands,
                    minimums,
                    strategy="proportional",
                )

            else:

                results = calculate_results(
                    availability,
                    demands,
                    minimums,
                    strategy="priority",
                    priority_order=priority_order,
                )

            impacts = calculate_global_impacts(
                results
            )

            st.divider()

            st.subheader(
                "Anteprima del report"
            )

            st.markdown(
                f"**Territorio:** {territory}"
            )

            st.markdown(
                f"**Regione:** {region}"
            )

            st.markdown(
                f"**Strategia:** {strategy_choice}"
            )

            display_results_metrics(
                results
            )

            st.dataframe(
                build_results_dataframe(results),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            st.subheader(
                "Sintesi decisionale"
            )

            try:

                data = get_analysis_data()

                analysis = run_integrated_analysis(
                    data,
                    results,
                )

                explanation = analysis.get(
                    "decision_explanation",
                    [],
                )

                display_decision_explanation(
                    explanation
                )

                st.divider()

                st.subheader(
                    "Valutazione del rischio"
                )

                display_water_risk(
                    analysis.get(
                        "water_risk",
                        {},
                    )
                )

            except Exception as error:

                st.warning(
                    f"Impossibile generare la sintesi decisionale: {error}"
                )

            st.divider()

            st.subheader(
                "Esportazione"
            )

            try:

                pdf = create_pdf_report(
                    territory,
                    region,
                    results,
                    impacts,
                    strategy_choice,
                )

                st.download_button(
                    label="📄 Scarica Decision Report PDF",
                    data=pdf,
                    file_name="AQUA_COMMONS_AI_Decision_Report.pdf",
                    mime="application/pdf",
                    type="primary",
                )

            except Exception as error:

                st.error(
                    f"Errore nella generazione del PDF: {error}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#718096;
        padding:10px;
    ">

        <b>AQUA COMMONS AI</b><br>

        Integrated Water Intelligence and Decision Support Platform<br>

        <span style="font-size:0.8rem;">
            Human-centred water governance · Transparency · Sustainability
        </span>

    </div>
    """,
    unsafe_allow_html=True,
)
