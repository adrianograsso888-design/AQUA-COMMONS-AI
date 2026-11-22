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

def analyze_integrated_drought(overview, data_status="simulated"):

    if not isinstance(overview, dict):
        raise TypeError(
            "Il quadro informativo deve essere un dizionario."
        )

    required_sections = [
        "territory",
        "hydrology",
        "climate",
    ]

    for section in required_sections:

        if section not in overview:
            raise ValueError(
                f"Manca la sezione {section} nel quadro informativo."
            )

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

        "data_type": data_status,

        "thresholds": RISK_THRESHOLDS.copy(),

        "weights": INDICATOR_WEIGHTS.copy(),

        "method": (
            "Indice dimostrativo basato su soglie e pesi "
            "predefiniti. Non costituisce un indice scientifico "
            "ufficiale di siccità e non produce previsioni. "
            "Le soglie e i pesi richiedono calibrazione "
            "su dati territoriali validati."
        ),

    }


# ============================================================
# CARICAMENTO DEL QUADRO COMPLETO
# ============================================================

def load_monitoring_dashboard(mode="simulated"):

    integrated = run_data_integration(mode)

    overview = integrated["overview"]

    provenance = integrated["provenance"]

    drought = analyze_integrated_drought(
        overview,
        data_status=provenance["status"],
    )

    geography = load_map_data(mode)

    return {

        "territory": overview["territory"],

        "hydrology": overview["hydrology"],

        "climate": overview["climate"],

        "drought": drought,

        "geography": geography,

        "provenance": provenance,

        "integrated_series": integrated["integrated_series"],

        "data_type": provenance["status"],

    }


# ============================================================
# GENERAZIONE DEL RIEPILOGO
# ============================================================

def generate_monitoring_summary(monitoring):

    drought = monitoring["drought"]

    hydrology = monitoring["hydrology"]

    climate = monitoring["climate"]

    geography = monitoring["geography"]

    provenance = monitoring["provenance"]

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
            geography["summary"]["total_points"]
        ),

        "data_status": provenance["status"],

        "data_sources": provenance["sources"],

        "data_records": provenance["total_dates"],

    }


# ============================================================
# GENERAZIONE DELLE SEGNALAZIONI
# ============================================================

def generate_monitoring_alerts(monitoring):

    alerts = []

    drought = monitoring["drought"]

    data_status = monitoring["provenance"]["status"]

    for signal in drought["all_signals"]:

        alerts.append({

            "category": signal["indicator"],

            "severity": signal["severity"],

            "message": signal["message"],

            "value": signal["value"],

            "unit": signal["unit"],

            "data_status": data_status,

            "is_operational": data_status == "official",

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

            "data_status": data_status,

            "is_operational": False,

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

        "analysis_type": "deterministic_rule_based",

    }
