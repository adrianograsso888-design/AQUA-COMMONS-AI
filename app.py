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

from core.config import (
    APP_NAME,
    APP_DESCRIPTION,
    SECTORS,
    DEFAULT_DEMAND,
    DEFAULT_MINIMUM,
    DEFAULT_AVAILABILITY,
    PLATFORM_MODES,
    DEFAULT_PLATFORM_MODE,
    PILOT_TERRITORY,
    PILOT_REGION,
)

from core.allocation import (
    calculate_results,
    compare_strategies,
)

from core.impact import (
    calculate_global_impacts,
    calculate_sector_impacts,
    compare_impacts,
)

from core.data_manager import load_data

from core.ai_engine import (
    run_integrated_analysis,
)

from services.data_integration import (
    run_data_integration,
)

from services.drought import (
    run_drought_assessment,
)

from services.monitoring import (
    run_integrated_monitoring,
)

from services.map_service import (
    display_map,
    load_map_data,
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
# CONFIGURAZIONE GRAFICA
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
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #DFE7EE;
    }

    .aqua-card {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #DFE7EE;
        margin-bottom: 10px;
    }

    .aqua-small {
        color: #607586;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INIZIALIZZAZIONE DELLO STATO
# ============================================================

def initialize_session_state():

    if "scenario_availability" not in st.session_state:
        st.session_state["scenario_availability"] = (
            DEFAULT_AVAILABILITY
        )

    if "platform_mode" not in st.session_state:
        st.session_state["platform_mode"] = (
            DEFAULT_PLATFORM_MODE
        )

    if "scenario_priority" not in st.session_state:
        st.session_state["scenario_priority"] = list(SECTORS)

    for sector in SECTORS:

        demand_key = f"scenario_demand_{sector}"
        minimum_key = f"scenario_minimum_{sector}"

        if demand_key not in st.session_state:
            st.session_state[demand_key] = DEFAULT_DEMAND[sector]

        if minimum_key not in st.session_state:
            st.session_state[minimum_key] = DEFAULT_MINIMUM[sector]


initialize_session_state()


# ============================================================
# RECUPERO DEI PARAMETRI DELLO SCENARIO
# ============================================================

def get_current_scenario():

    availability = float(
        st.session_state["scenario_availability"]
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

    priority = list(
        st.session_state["scenario_priority"]
    )

    return availability, demands, minimums, priority


def scenario_is_valid(availability, demands, minimums, priority):

    if availability < 0:
        return False, "La disponibilità idrica non può essere negativa."

    for sector in SECTORS:

        if demands[sector] < 0:
            return False, f"Domanda non valida per {sector}."

        if minimums[sector] < 0:
            return False, f"Quota minima non valida per {sector}."

        if minimums[sector] > demands[sector]:
            return False, (
                f"La quota minima di {sector} supera la domanda."
            )

    if sum(minimums.values()) > availability + 1e-9:

        return False, (
            "La somma delle quote minime supera la disponibilità idrica."
        )

    if (
        len(priority) != len(SECTORS)
        or set(priority) != set(SECTORS)
    ):

        return False, "L'ordine delle priorità non è valido."

    return True, "Scenario valido."


# ============================================================
# CALCOLO DELLE STRATEGIE
# ============================================================

def calculate_scenario_results(
    availability,
    demands,
    minimums,
    priority,
):

    proportional = calculate_results(
        availability,
        demands,
        minimums,
        strategy="proportional",
        priority_order=priority,
    )

    priority_result = calculate_results(
        availability,
        demands,
        minimums,
        strategy="priority",
        priority_order=priority,
    )

    return proportional, priority_result


def get_strategy_results(
    availability,
    demands,
    minimums,
    priority,
    strategy,
):

    return calculate_results(
        availability,
        demands,
        minimums,
        strategy=strategy,
        priority_order=priority,
    )


# ============================================================
# FUNZIONI DI SUPPORTO
# ============================================================

def format_number(value, decimals=2):

    try:
        return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    except (TypeError, ValueError):
        return "N/D"


def show_data_status(status):

    labels = {
        "simulated": "Dati simulati",
        "official": "Dati ufficiali",
        "manual": "Dati manuali",
        "hybrid": "Dati ibridi",
        "unknown": "Provenienza non verificata",
        "empty": "Nessun dato",
        "error": "Errore nella verifica",
    }

    return labels.get(status, str(status))


def show_prototype_notice():

    st.info(
        "PROTOTIPO DIMOSTRATIVO — I dati attualmente disponibili "
        "sono simulati e non rappresentano misurazioni ufficiali. "
        "Le analisi sono strumenti di supporto e non sostituiscono "
        "le decisioni delle autorità competenti."
    )


def build_sector_dataframe(results):

    rows = []

    for sector in SECTORS:

        values = results["sectors"][sector]

        rows.append({
            "Settore": sector,
            "Domanda (hm³)": values["demand"],
            "Quota minima (hm³)": values["minimum"],
            "Acqua assegnata (hm³)": values["allocated"],
            "Deficit (hm³)": values["shortage"],
            "Copertura (%)": values["coverage"],
        })

    return pd.DataFrame(rows)


def get_strategy_label(strategy):

    if strategy == "proportional":
        return "Allocazione proporzionale"

    return "Allocazione per priorità"


# ============================================================
# GENERAZIONE DEL PDF
# ============================================================

def generate_pdf_report(
    results,
    availability,
    demands,
    minimums,
    priority,
    strategy_label,
    comparison,
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
        spaceAfter=12,
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

    def add_table(data, widths):

        table = Table(
            data,
            colWidths=widths,
            repeatRows=1,
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#123B56"),
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
                    colors.HexColor("#D5DEE6"),
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ])
        )

        elements.append(table)

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    elements.append(
        Paragraph("AQUA COMMONS AI", title_style)
    )

    elements.append(
        Paragraph(
            "DECISION SUPPORT REPORT",
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph(
            f"Generato il: {generated_at}",
            body_style,
        )
    )

    elements.append(Spacer(1, 12))

    global_impacts = calculate_global_impacts(results)

    elements.append(
        Paragraph("1. Sintesi dello scenario", heading_style)
    )

    summary_data = [
        ["Indicatore", "Valore"],
        ["Disponibilità idrica", f"{availability:.2f} hm³"],
        ["Domanda complessiva", f"{global_impacts['total_demand']:.2f} hm³"],
        ["Acqua assegnata", f"{global_impacts['total_allocated']:.2f} hm³"],
        ["Deficit complessivo", f"{global_impacts['total_shortage']:.2f} hm³"],
        ["Strategia", strategy_label],
    ]

    add_table(summary_data, [8 * cm, 8 * cm])

    elements.append(
        Paragraph("2. Parametri dello scenario", heading_style)
    )

    parameter_data = [
        ["Settore", "Domanda", "Quota minima"],
    ]

    for sector in SECTORS:

        parameter_data.append([
            sector,
            f"{demands[sector]:.2f} hm³",
            f"{minimums[sector]:.2f} hm³",
        ])

    add_table(parameter_data, [6 * cm, 5 * cm, 5 * cm])

    elements.append(
        Paragraph("3. Risultati dell'allocazione", heading_style)
    )

    allocation_data = [
        ["Settore", "Assegnata", "Deficit", "Copertura"],
    ]

    for sector in SECTORS:

        values = results["sectors"][sector]

        allocation_data.append([
            sector,
            f"{values['allocated']:.2f}",
            f"{values['shortage']:.2f}",
            f"{values['coverage']:.1f}%",
        ])

    add_table(
        allocation_data,
        [4.5 * cm, 4 * cm, 4 * cm, 4 * cm],
    )

    elements.append(
        Paragraph("4. Confronto tra strategie", heading_style)
    )

    comparison_data = [
        ["Indicatore", "Proporzionale", "Per priorità"],
    ]

    for sector in SECTORS:

        comparison_data.append([
            sector,
            f"{comparison['proportional']['sectors'][sector]['allocated']:.2f} hm³",
            f"{comparison['priority']['sectors'][sector]['allocated']:.2f} hm³",
        ])

    add_table(
        comparison_data,
        [6 * cm, 5 * cm, 5 * cm],
    )

    elements.append(
        Paragraph("5. Ordine delle priorità", heading_style)
    )

    elements.append(
        Paragraph(
            " &gt; ".join(priority),
            body_style,
        )
    )

    elements.append(
        Paragraph("6. Limiti e responsabilità", heading_style)
    )

    notes = [
        "Il documento utilizza parametri dimostrativi e non costituisce una misurazione ufficiale.",
        "Le quote minime sono ipotesi del modello e non rappresentano automaticamente soglie normative.",
        "La quota ambientale del modello non sostituisce le verifiche del deflusso ecologico.",
        "Gli indicatori volumetrici non rappresentano perdite economiche monetarie.",
        "Il sistema supporta il confronto tra scenari e non assume decisioni amministrative automatiche.",
        "La decisione finale compete alle autorità responsabili.",
    ]

    for note in notes:

        elements.append(
            Paragraph(f"• {note}", body_style)
        )

        elements.append(Spacer(1, 4))

    document.build(elements)

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# INTESTAZIONE E NAVIGAZIONE
# ============================================================

st.sidebar.title("💧 AQUA COMMONS AI")

st.sidebar.caption(
    "INTEGRATED WATER INTELLIGENCE PLATFORM"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGAZIONE",
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

st.sidebar.divider()

st.sidebar.subheader("Configurazione territoriale")

platform_mode = st.sidebar.selectbox(
    "Modalità piattaforma",
    PLATFORM_MODES,
    index=PLATFORM_MODES.index(
        st.session_state["platform_mode"]
    ),
    key="platform_mode_selector",
)

st.session_state["platform_mode"] = platform_mode

if platform_mode == "Analisi territoriale":

    st.sidebar.write(f"Territorio pilota: {PILOT_TERRITORY}")
    st.sidebar.write(f"Regione: {PILOT_REGION}")

else:

    st.sidebar.write("Demo territoriale generica")

st.sidebar.divider()

st.sidebar.caption(
    "Versione dimostrativa | AQUA COMMONS AI"
)


# ============================================================
# RECUPERO DELLO SCENARIO
# ============================================================

availability, demands, minimums, priority = get_current_scenario()

valid_scenario, scenario_message = scenario_is_valid(
    availability,
    demands,
    minimums,
    priority,
)


# ============================================================
# 01 - OVERVIEW DASHBOARD
# ============================================================

if page == "Overview Dashboard":

    st.title("AQUA COMMONS AI")

    st.subheader(
        "Integrated Water Intelligence and Decision Support Platform"
    )

    st.write(
        "Piattaforma per il monitoraggio delle risorse idriche, "
        "l'individuazione di condizioni di stress e il confronto "
        "trasparente di scenari alternativi di allocazione."
    )

    show_prototype_notice()

    st.divider()

    st.subheader("Quadro generale dello scenario")

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())

    theoretical_shortage = max(
        0.0,
        total_demand - availability,
    )

    theoretical_coverage = (
        min(availability, total_demand) / total_demand * 100
        if total_demand > 0
        else 100.0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Disponibilità idrica",
        f"{format_number(availability, 1)} hm³",
    )

    c2.metric(
        "Domanda complessiva",
        f"{format_number(total_demand, 1)} hm³",
    )

    c3.metric(
        "Deficit teorico",
        f"{format_number(theoretical_shortage, 1)} hm³",
    )

    c4.metric(
        "Copertura teorica",
        f"{format_number(theoretical_coverage, 1)}%",
    )

    if valid_scenario:

        st.success(
            "Scenario compatibile con i fabbisogni minimi impostati."
        )

    else:

        st.error(scenario_message)

    st.divider()

    st.subheader("Distribuzione della domanda")

    demand_df = pd.DataFrame({
        "Settore": SECTORS,
        "Domanda": [demands[s] for s in SECTORS],
        "Quota minima": [minimums[s] for s in SECTORS],
    })

    left, right = st.columns([1.3, 1])

    with left:

        st.bar_chart(
            demand_df.set_index("Settore")[["Domanda"]]
        )

    with right:

        st.dataframe(
            demand_df,
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    st.subheader("Architettura funzionale")

    module_columns = st.columns(4)

    modules = [
        (
            "01",
            "Integrated Monitoring",
            "Integrazione dei dati idrologici, climatici e territoriali.",
        ),
        (
            "02",
            "Drought Early Warning",
            "Individuazione di segnali di attenzione e stress idrico.",
        ),
        (
            "03",
            "Allocation Simulator",
            "Confronto tra strategie di distribuzione della risorsa.",
        ),
        (
            "04",
            "Impact Analysis",
            "Analisi degli effetti sui settori e sui diversi utilizzatori.",
        ),
    ]

    for column, module in zip(module_columns, modules):

        with column:

            st.markdown(
                f"""
                <div class="aqua-card">
                    <h3>{module[0]}</h3>
                    <b>{module[1]}</b>
                    <p class="aqua-small">{module[2]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(
        "L'architettura attuale utilizza moduli deterministici e "
        "regole di analisi. Non è ancora integrato un modello "
        "predittivo di machine learning."
    )


# ============================================================
# 02 - INTEGRATED MONITORING
# ============================================================

elif page == "Integrated Monitoring":

    st.title("Integrated Monitoring")

    st.write(
        "Quadro integrato delle condizioni idrologiche, climatiche "
        "e territoriali."
    )

    show_prototype_notice()

    with st.spinner("Elaborazione del monitoraggio integrato..."):

        try:

            monitoring_result = run_integrated_monitoring(
                mode="simulated"
            )

            monitoring = monitoring_result["monitoring"]
            summary = monitoring_result["summary"]
            alerts = monitoring_result["alerts"]

        except Exception as error:

            st.error(
                "Non è stato possibile completare il monitoraggio integrato."
            )

            st.exception(error)

            st.stop()

    st.success("Elaborazione del monitoraggio completata.")

    st.divider()

    st.subheader("Provenienza dei dati")

    data_status = summary.get(
        "data_status",
        monitoring.get("provenance", {}).get("status", "unknown"),
    )

    st.metric(
        "Stato della provenienza",
        show_data_status(data_status),
    )

    provenance = monitoring.get("provenance", {})

    if provenance.get("message"):

        st.caption(provenance["message"])

    st.divider()

    st.subheader("Indicatori idrologici")

    hydrology = monitoring["hydrology"]

    flow = hydrology["river_flow"]
    reservoir = hydrology["reservoir_storage"]
    groundwater = hydrology["groundwater_level"]

    h1, h2, h3 = st.columns(3)

    h1.metric(
        "Portata fluviale",
        f"{format_number(flow['latest_value'])} m³/s",
        delta=f"{format_number(flow['variation_percentage'], 1)}%",
    )

    h2.metric(
        "Riserve negli invasi",
        f"{format_number(reservoir['latest_value'])} hm³",
        delta=f"{format_number(reservoir['variation_percentage'], 1)}%",
    )

    h3.metric(
        "Livello falde",
        f"{format_number(groundwater['latest_value'])} m",
        delta=f"{format_number(groundwater['variation_percentage'], 1)}%",
    )

    st.caption(
        "Le variazioni rappresentano il confronto tra il primo e "
        "l'ultimo dato del periodo dimostrativo."
    )

    st.divider()

    st.subheader("Indicatori climatici")

    climate = monitoring["climate"]

    rainfall = climate["rainfall"]
    temperature = climate["temperature"]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Precipitazioni osservate",
        f"{format_number(rainfall['observed_mm'], 1)} mm",
    )

    c2.metric(
        "Deficit pluviometrico",
        f"{format_number(rainfall['deficit_percentage'], 1)}%",
    )

    c3.metric(
        "Anomalia termica",
        f"{format_number(temperature['anomaly_c'], 1)} °C",
    )

    st.divider()

    st.subheader("Indice dimostrativo di attenzione")

    drought = monitoring["drought"]

    d1, d2, d3 = st.columns(3)

    d1.metric(
        "Indice di attenzione",
        f"{drought['attention_index']}/100",
    )

    d2.metric(
        "Livello di attenzione",
        drought["attention_level"],
    )

    d3.metric(
        "Segnali rilevati",
        drought["signal_count"],
    )

    st.progress(
        max(
            0.0,
            min(
                1.0,
                drought["attention_index"] / 100,
            ),
        )
    )

    st.caption(drought["method"])

    st.divider()

    st.subheader("Segnalazioni del sistema")

    if alerts:

        for alert in alerts:

            message = alert.get(
                "message",
                str(alert),
            )

            severity = alert.get(
                "severity",
                "info",
            )

            if severity in ["high", "critical", "error"]:

                st.error(message)

            elif severity in ["warning", "medium"]:

                st.warning(message)

            else:

                st.info(message)

    else:

        st.info(
            "Non sono disponibili segnalazioni aggiuntive."
        )

    st.divider()

    st.subheader("Sintesi del monitoraggio")

    st.write(
        f"Punti geografici monitorati: "
        f"**{summary.get('monitoring_points', 'N/D')}**"
    )

    st.write(
        f"Record temporali analizzati: "
        f"**{summary.get('data_records', 'N/D')}**"
    )

    st.caption(
        "Il monitoraggio è dimostrativo. Le soglie e i valori "
        "non costituiscono un sistema ufficiale di allerta."
    )


# ============================================================
# 03 - DROUGHT EARLY WARNING
# ============================================================

elif page == "Drought Early Warning":

    st.title("Drought Early Warning System")

    st.write(
        "Individuazione di segnali di stress idrico attraverso "
        "indicatori idrologici e climatici."
    )

    show_prototype_notice()

    with st.spinner("Valutazione delle condizioni idriche e climatiche..."):

        try:

            drought = run_drought_assessment(
                mode="simulated"
            )

        except Exception as error:

            st.error(
                "Impossibile completare la valutazione della siccità."
            )

            st.exception(error)

            st.stop()

    st.subheader("Livello di attenzione")

    d1, d2, d3 = st.columns(3)

    d1.metric(
        "Indice di attenzione",
        f"{drought['attention_index']}/100",
    )

    d2.metric(
        "Classificazione",
        drought["attention_level"],
    )

    d3.metric(
        "Segnali rilevati",
        drought["signal_count"],
    )

    st.progress(
        drought["attention_index"] / 100
    )

    st.caption(drought["method"])

    st.divider()

    st.subheader("Segnali idrologici")

    hydrological_signals = drought["hydrological_signals"]

    if hydrological_signals:

        for signal in hydrological_signals:

            st.warning(
                f"**{signal['indicator']}** — "
                f"{format_number(signal['value'], 1)} "
                f"{signal['unit']}. {signal['message']}"
            )

    else:

        st.success(
            "Non sono stati rilevati segnali idrologici "
            "oltre le soglie dimostrative impostate."
        )

    st.divider()

    st.subheader("Segnali climatici")

    climatic_signals = drought["climatic_signals"]

    if climatic_signals:

        for signal in climatic_signals:

            st.warning(
                f"**{signal['indicator']}** — "
                f"{format_number(signal['value'], 1)} "
                f"{signal['unit']}. {signal['message']}"
            )

    else:

        st.success(
            "Non sono stati rilevati segnali climatici "
            "oltre le soglie dimostrative impostate."
        )

    st.divider()

    st.subheader("Soglie di attenzione")

    thresholds_df = pd.DataFrame([
        {
            "Indicatore": "Diminuzione portata fluviale",
            "Soglia": f"{drought['thresholds']['river_flow_decline']}%",
        },
        {
            "Indicatore": "Diminuzione riserve negli invasi",
            "Soglia": f"{drought['thresholds']['reservoir_decline']}%",
        },
        {
            "Indicatore": "Diminuzione livello falde",
            "Soglia": f"{drought['thresholds']['groundwater_decline']}%",
        },
        {
            "Indicatore": "Deficit pluviometrico",
            "Soglia": f"{drought['thresholds']['rainfall_deficit']}%",
        },
        {
            "Indicatore": "Anomalia termica",
            "Soglia": f"{drought['thresholds']['temperature_anomaly']} °C",
        },
    ])

    st.dataframe(
        thresholds_df,
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    st.subheader("Raccomandazioni preventive")

    for recommendation in drought["recommendations"]:

        st.markdown(f"- {recommendation}")

    st.warning(
        "L'indice è dimostrativo e basato su soglie e pesi "
        "predefiniti. Non è un indice scientifico ufficiale, "
        "non produce previsioni e non costituisce un'allerta "
        "istituzionale."
    )


# ============================================================
# 04 - GEOGRAPHICAL INTELLIGENCE
# ============================================================

elif page == "Geographical Intelligence":

    st.title("Geographical Intelligence")

    st.write(
        "Visualizzazione geografica dei punti dimostrativi "
        "di monitoraggio idrologico, climatico e territoriale."
    )

    show_prototype_notice()

    st.subheader("Mappa interattiva")

    try:

        display_map(
            st,
            mode="simulated",
        )

    except Exception as error:

        st.error(
            "Non è stato possibile caricare la mappa."
        )

        st.exception(error)

    st.divider()

    st.subheader("Informazioni territoriali")

    try:

        map_result = load_map_data(
            mode="simulated"
        )

        map_summary = map_result["summary"]

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "Punti geografici",
            map_summary["total_points"],
        )

        m2.metric(
            "Categorie",
            map_summary["categories"],
        )

        m3.metric(
            "Coordinate valide",
            map_summary["valid_coordinates"],
        )

        st.caption(
            "Le coordinate sono illustrative e non identificano "
            "necessariamente stazioni di monitoraggio reali."
        )

    except Exception as error:

        st.warning(
            "Non è stato possibile recuperare il riepilogo geografico."
        )

        st.exception(error)


# ============================================================
# 05 - ALLOCATION SIMULATOR
# ============================================================

elif page == "Allocation Simulator":

    st.title("Allocation Simulator")

    st.write(
        "Simulazione e confronto di strategie alternative "
        "di distribuzione della risorsa idrica."
    )

    show_prototype_notice()

    st.subheader("1. Disponibilità idrica")

    availability_input = st.number_input(
        "Disponibilità idrica totale (hm³)",
        min_value=0.0,
        max_value=1000.0,
        step=5.0,
        value=float(
            st.session_state["scenario_availability"]
        ),
        key="availability_editor",
    )

    st.session_state["scenario_availability"] = availability_input

    st.divider()

    st.subheader("2. Domanda e fabbisogni minimi")

    for sector in SECTORS:

        st.markdown(f"**{sector}**")

        col1, col2 = st.columns(2)

        demand_key = f"scenario_demand_{sector}"
        minimum_key = f"scenario_minimum_{sector}"

        with col1:

            new_demand = st.number_input(
                f"Domanda {sector} (hm³)",
                min_value=0.0,
                max_value=1000.0,
                step=1.0,
                value=float(st.session_state[demand_key]),
                key=f"editor_demand_{sector}",
            )

        with col2:

            new_minimum = st.number_input(
                f"Quota minima {sector} (hm³)",
                min_value=0.0,
                max_value=1000.0,
                step=1.0,
                value=float(st.session_state[minimum_key]),
                key=f"editor_minimum_{sector}",
            )

        st.session_state[demand_key] = new_demand
        st.session_state[minimum_key] = new_minimum

        if new_minimum > new_demand:

            st.error(
                f"La quota minima di {sector} non può superare "
                "la domanda del settore."
            )

    st.divider()

    st.subheader("3. Ordine delle priorità")

    current_priority = list(
        st.session_state["scenario_priority"]
    )

    priority_options = []

    for index in range(len(SECTORS)):

        current_value = current_priority[index]

        available_options = [
            sector
            for sector in SECTORS
            if sector not in priority_options
            or sector == current_value
        ]

        selected = st.selectbox(
            f"Priorità {index + 1}",
            options=available_options,
            index=available_options.index(current_value),
            key=f"priority_editor_{index}",
        )

        priority_options.append(selected)

    st.session_state["scenario_priority"] = priority_options

    availability, demands, minimums, priority = get_current_scenario()

    valid_scenario, scenario_message = scenario_is_valid(
        availability,
        demands,
        minimums,
        priority,
    )

    st.divider()

    st.subheader("4. Riepilogo dei parametri")

    total_demand = sum(demands.values())
    total_minimum = sum(minimums.values())

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Disponibilità",
        f"{format_number(availability, 1)} hm³",
    )

    c2.metric(
        "Domanda totale",
        f"{format_number(total_demand, 1)} hm³",
    )

    c3.metric(
        "Quote minime",
        f"{format_number(total_minimum, 1)} hm³",
    )

    if not valid_scenario:

        st.error(scenario_message)

        st.stop()

    st.success("Parametri dello scenario validi.")

    st.divider()

    st.subheader("5. Risultati delle strategie")

    try:

        proportional, priority_result = calculate_scenario_results(
            availability,
            demands,
            minimums,
            priority,
        )

    except Exception as error:

        st.error(
            "Errore durante il calcolo delle strategie."
        )

        st.exception(error)

        st.stop()

    tab1, tab2 = st.tabs([
        "Allocazione proporzionale",
        "Allocazione per priorità",
    ])

    with tab1:

        st.markdown("#### Strategia proporzionale")

        st.write(
            "Dopo l'assegnazione delle quote minime, "
            "la risorsa residua viene distribuita in proporzione "
            "ai fabbisogni ancora insoddisfatti."
        )

        proportional_df = build_sector_dataframe(
            proportional
        )

        st.dataframe(
            proportional_df,
            hide_index=True,
            use_container_width=True,
        )

        st.bar_chart(
            proportional_df.set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

    with tab2:

        st.markdown("#### Strategia per priorità")

        st.write(
            "Dopo l'assegnazione delle quote minime, "
            "la risorsa residua viene distribuita seguendo "
            "l'ordine di priorità configurato."
        )

        priority_df = build_sector_dataframe(
            priority_result
        )

        st.dataframe(
            priority_df,
            hide_index=True,
            use_container_width=True,
        )

        st.bar_chart(
            priority_df.set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

    st.divider()

    st.subheader("6. Confronto tra strategie")

    comparison = compare_strategies(
        availability,
        demands,
        minimums,
        priority,
    )

    comparison_df = pd.DataFrame([
        {
            "Indicatore": "Acqua assegnata",
            "Proporzionale": proportional["total_allocated"],
            "Per priorità": priority_result["total_allocated"],
        },
        {
            "Indicatore": "Deficit complessivo",
            "Proporzionale": proportional["total_demand"] - proportional["total_allocated"],
            "Per priorità": priority_result["total_demand"] - priority_result["total_allocated"],
        },
    ])

    st.dataframe(
        comparison_df,
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Le strategie sono strumenti di confronto. "
        "La scelta effettiva deve considerare vincoli fisici, "
        "normativi, ambientali e sociali."
    )


# ============================================================
# 06 - IMPACT ANALYSIS
# ============================================================

elif page == "Impact Analysis":

    st.title("Impact Analysis")

    st.write(
        "Valutazione degli effetti distributivi dell'allocazione "
        "sui diversi settori utilizzatori."
    )

    show_prototype_notice()

    if not valid_scenario:

        st.error(scenario_message)

        st.stop()

    selected_strategy = st.selectbox(
        "Strategia da analizzare",
        [
            "Allocazione proporzionale",
            "Allocazione per priorità",
        ],
        key="impact_strategy",
    )

    strategy = (
        "proportional"
        if selected_strategy == "Allocazione proporzionale"
        else "priority"
    )

    try:

        results = get_strategy_results(
            availability,
            demands,
            minimums,
            priority,
            strategy,
        )

        global_impacts = calculate_global_impacts(
            results
        )

        sector_impacts = calculate_sector_impacts(
            results
        )

        ai_analysis = run_integrated_analysis(
            load_data("simulated"),
            results,
        )

    except Exception as error:

        st.error(
            "Non è stato possibile completare l'analisi degli impatti."
        )

        st.exception(error)

        st.stop()

    st.divider()

    st.subheader("1. Quadro generale")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Domanda totale",
        f"{format_number(global_impacts['total_demand'])} hm³",
    )

    c2.metric(
        "Acqua assegnata",
        f"{format_number(global_impacts['total_allocated'])} hm³",
    )

    c3.metric(
        "Deficit totale",
        f"{format_number(global_impacts['total_shortage'])} hm³",
    )

    c4.metric(
        "Copertura della domanda",
        f"{format_number(global_impacts['coverage'], 1)}%",
    )

    st.divider()

    st.subheader("2. Impatti settoriali")

    impact_rows = []

    for sector in SECTORS:

        impact = sector_impacts[sector]

        impact_rows.append({
            "Settore": sector,
            "Domanda (hm³)": impact["demand"],
            "Assegnata (hm³)": impact["allocated"],
            "Deficit (hm³)": impact["shortage"],
            "Copertura (%)": impact["coverage"],
        })

    impact_df = pd.DataFrame(impact_rows)

    st.dataframe(
        impact_df,
        hide_index=True,
        use_container_width=True,
    )

    st.bar_chart(
        impact_df.set_index("Settore")[["Deficit (hm³)"]]
    )

    st.divider()

    st.subheader("3. Rischio rispetto alla domanda")

    water_risk = ai_analysis["water_risk"]

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Livello di rischio",
        water_risk["risk_level"],
    )

    r2.metric(
        "Domanda non soddisfatta",
        f"{format_number(water_risk['shortage_percentage'], 1)}%",
    )

    r3.metric(
        "Deficit",
        f"{format_number(water_risk['total_shortage'])} hm³",
    )

    st.caption(water_risk["method"])

    st.divider()

    st.subheader("4. Distribuzione degli effetti")

    scenario_analysis = ai_analysis["scenario_analysis"]

    st.write(
        f"Settore maggiormente interessato dal deficit: "
        f"**{scenario_analysis['most_affected_sector']}**."
    )

    st.write(
        f"Settore con il deficit assoluto minore: "
        f"**{scenario_analysis['least_affected_sector']}**."
    )

    for observation in scenario_analysis["observations"]:

        st.markdown(f"- {observation}")

    st.divider()

    st.subheader("5. Controllo dei dati")

    quality = ai_analysis["data_quality"]

    q1, q2 = st.columns(2)

    q1.metric(
        "Stato dei dati",
        show_data_status(quality["status"]),
    )

    q2.metric(
        "Record analizzati",
        quality.get("records", 0),
    )

    st.write(quality["message"])

    anomalies = ai_analysis["anomalies"]

    if anomalies:

        st.warning(
            f"Rilevate {len(anomalies)} anomalie nei dati."
        )

        st.dataframe(
            pd.DataFrame(anomalies),
            hide_index=True,
            use_container_width=True,
        )

    else:

        st.success(
            "Non sono state rilevate anomalie secondo i controlli implementati."
        )

    st.divider()

    st.subheader("6. Spiegazione della decisione")

    for explanation in ai_analysis["decision_explanation"]:

        st.markdown(f"- {explanation}")

    st.caption(
        "Il motore attuale applica regole deterministiche e "
        "calcoli matematici. Non è un modello predittivo addestrato."
    )


# ============================================================
# 07 - DECISION REPORT
# ============================================================

elif page == "Decision Report":

    st.title("Decision Report")

    st.write(
        "Generazione di un documento strutturato per confrontare "
        "gli scenari di allocazione e i relativi effetti."
    )

    show_prototype_notice()

    if not valid_scenario:

        st.error(scenario_message)

        st.stop()

    report_strategy_name = st.selectbox(
        "Strategia da approfondire",
        [
            "Allocazione proporzionale",
            "Allocazione per priorità",
        ],
        key="report_strategy",
    )

    report_strategy = (
        "proportional"
        if report_strategy_name == "Allocazione proporzionale"
        else "priority"
    )

    try:

        results = get_strategy_results(
            availability,
            demands,
            minimums,
            priority,
            report_strategy,
        )

        comparison = compare_strategies(
            availability,
            demands,
            minimums,
            priority,
        )

    except Exception as error:

        st.error(
            "Non è stato possibile preparare il report."
        )

        st.exception(error)

        st.stop()

    global_impacts = calculate_global_impacts(
        results
    )

    st.divider()

    st.subheader("1. Sintesi dello scenario")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Disponibilità",
        f"{format_number(availability)} hm³",
    )

    c2.metric(
        "Domanda",
        f"{format_number(global_impacts['total_demand'])} hm³",
    )

    c3.metric(
        "Acqua assegnata",
        f"{format_number(global_impacts['total_allocated'])} hm³",
    )

    c4.metric(
        "Deficit",
        f"{format_number(global_impacts['total_shortage'])} hm³",
    )

    st.write(
        f"**Strategia:** {report_strategy_name}"
    )

    st.write(
        f"**Ordine di priorità:** {' > '.join(priority)}"
    )

    st.divider()

    st.subheader("2. Risultati settoriali")

    results_df = build_sector_dataframe(
        results
    )

    st.dataframe(
        results_df,
        hide_index=True,
        use_container_width=True,
    )

    st.bar_chart(
        results_df.set_index("Settore")[
            ["Domanda (hm³)", "Acqua assegnata (hm³)"]
        ]
    )

    st.divider()

    st.subheader("3. Confronto tra strategie")

    comparison_data = []

    for sector in SECTORS:

        comparison_data.append({
            "Settore": sector,
            "Acqua proporzionale (hm³)": comparison["proportional"]["sectors"][sector]["allocated"],
            "Acqua per priorità (hm³)": comparison["priority"]["sectors"][sector]["allocated"],
            "Differenza (hm³)": comparison["priority"]["sectors"][sector]["allocated"] - comparison["proportional"]["sectors"][sector]["allocated"],
        })

    comparison_df = pd.DataFrame(
        comparison_data
    )

    st.dataframe(
        comparison_df,
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    st.subheader("4. Impatti e responsabilità")

    sector_impacts = calculate_sector_impacts(
        results
    )

    for sector in SECTORS:

        impact = sector_impacts[sector]

        st.write(
            f"**{sector}:** deficit di "
            f"{format_number(impact['shortage'])} hm³ "
            f"e copertura del "
            f"{format_number(impact['coverage'], 1)}%."
        )

    st.warning(
        "Il modello non determina automaticamente la distribuzione "
        "effettiva della risorsa. La valutazione finale deve considerare "
        "normativa applicabile, fabbisogni essenziali, deflussi ecologici, "
        "disponibilità fisica e competenze delle autorità."
    )

    st.divider()

    st.subheader("5. Esportazione del documento")

    try:

        pdf_bytes = generate_pdf_report(
            results,
            availability,
            demands,
            minimums,
            priority,
            report_strategy_name,
            comparison,
        )

        st.download_button(
            label="📄 Scarica Decision Report in PDF",
            data=pdf_bytes,
            file_name="AQUA_COMMONS_AI_Decision_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as error:

        st.error(
            "Non è stato possibile generare il PDF."
        )

        st.exception(error)

    st.caption(
        "Il documento viene generato utilizzando i parametri "
        "dello scenario attualmente configurato."
    )
