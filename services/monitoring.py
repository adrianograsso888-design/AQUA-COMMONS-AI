
# ============================================================
# AQUA COMMONS AI
# INTEGRATED MONITORING
# Quadro integrato di monitoraggio territoriale
# ============================================================

from services.data_integration import run_data_integration

from services.drought import (
    evaluate_hydrological_conditions,
    evaluate_climatic_conditions,
    calculate_attention_index,
    classify_drought_attention,
    generate_prevention_recommendations,
    RISK_THRESHOLDS,
    INDICATOR_WEIGHTS,
)

from services.map_service import load_map_data


# ============================================================
# ANALISI INTEGRATA DEL RISCHIO
# ============================================================

def analyze_integrated_drought(overview):

    hydrological_signals = evaluate_hydrological_conditions(
        overview
    )

    climatic_signals = evaluate_climatic_conditions(
        overview
    )

    all_signals = (
        hydrological_signals
        + climatic_signals
    )

    attention_index = calculate_attention_index(
        all_signals
    )

    attention_level = classify_drought_attention(
        attention_index
    )

    recommendations = generate_prevention_recommendations(
        all_signals
    )

    return {

        "territory": overview["territory"],

        "attention_index": attention_index,

        "attention_level": attention_level,

        "hydrological_signals": hydrological_signals,

        "climatic_signals": climatic_signals,

        "all_signals": all_signals,

        "signal_count": len(all_signals),

        "recommendations": recommendations,

        "data_type": "simulated",

        "thresholds": RISK_THRESHOLDS.copy(),

        "weights": INDICATOR_WEIGHTS.copy(),

        "method": (
            "Indice dimostrativo basato su soglie e pesi "
            "predefiniti. Non costituisce un indice scientifico "
            "ufficiale di siccità e non produce previsioni."
        ),

    }


# ============================================================
# CARICAMENTO DEL QUADRO COMPLETO
# ============================================================

def load_monitoring_dashboard(mode="simulated"):

    integrated = run_data_integration(mode)

    overview = integrated["overview"]

    drought = analyze_integrated_drought(
        overview
    )

    geography = load_map_data(mode)

    return {

        "territory": overview["territory"],

        "hydrology": overview["hydrology"],

        "climate": overview["climate"],

        "drought": drought,

        "geography": geography,

        "provenance": integrated["provenance"],

        "integrated_series": integrated["integrated_series"],

        "data_type": mode,

    }


# ============================================================
# GENERAZIONE DEL RIEPILOGO
# ============================================================

def generate_monitoring_summary(monitoring):

    drought = monitoring["drought"]

    hydrology = monitoring["hydrology"]

    climate = monitoring["climate"]

    return {

        "territory": monitoring["territory"],

        "attention_level": drought["attention_level"],

        "attention_index": drought["attention_index"],

        "signal_count": drought["signal_count"],

        "river_flow_variation": (
            hydrology["river_flow"]["variation_percentage"]
        ),

        "reservoir_variation": (
            hydrology["reservoir_storage"]["variation_percentage"]
        ),

        "groundwater_variation": (
            hydrology["groundwater_level"]["variation_percentage"]
        ),

        "rainfall_deficit": (
            climate["rainfall"]["deficit_percentage"]
        ),

        "temperature_anomaly": (
            climate["temperature"]["anomaly_c"]
        ),

        "monitoring_points": (
            monitoring["geography"]["summary"]["total_points"]
        ),

        "data_status": (
            monitoring["provenance"]["status"]
        ),

    }


# ============================================================
# GENERAZIONE DELLE SEGNALAZIONI
# ============================================================

def generate_monitoring_alerts(monitoring):

    alerts = []

    drought = monitoring["drought"]

    for signal in drought["all_signals"]:

        alerts.append({

            "category": signal["indicator"],

            "severity": signal["severity"],

            "message": signal["message"],

            "value": signal["value"],

            "unit": signal["unit"],

        })

    if not alerts:

        alerts.append({

            "category": "Monitoraggio generale",

            "severity": "info",

            "message": (
                "Non sono stati rilevati segnali "
                "che superano le soglie dimostrative."
            ),

            "value": None,

            "unit": None,

        })

    return alerts


# ============================================================
# ESECUZIONE COMPLETA DEL MONITORAGGIO
# ============================================================

def run_integrated_monitoring(mode="simulated"):

    monitoring = load_monitoring_dashboard(mode)

    summary = generate_monitoring_summary(
        monitoring
    )

    alerts = generate_monitoring_alerts(
        monitoring
    )

    return {

        "monitoring": monitoring,

        "summary": summary,

        "alerts": alerts,

        "status": "completed",

    }
