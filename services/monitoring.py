
# ============================================================
# AQUA COMMONS AI
# INTEGRATED MONITORING
# Quadro integrato di monitoraggio territoriale
# ============================================================

from services.data_integration import run_data_integration

from services.drought import run_drought_assessment

from services.map_service import load_map_data


# ============================================================
# CARICAMENTO DEL QUADRO COMPLETO
# ============================================================

def load_monitoring_dashboard(mode="simulated"):

    integrated = run_data_integration(mode)

    drought = run_drought_assessment(mode)

    geography = load_map_data(mode)

    overview = integrated["overview"]

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
