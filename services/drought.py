
# ============================================================
# AQUA COMMONS AI
# DROUGHT EARLY WARNING SYSTEM
# Monitoraggio e individuazione dello stress idrico
# ============================================================

from services.data_integration import run_data_integration


# ============================================================
# SOGLIE DIMOSTRATIVE
# ============================================================

RISK_THRESHOLDS = {
    "river_flow_decline": 10.0,
    "reservoir_decline": 10.0,
    "groundwater_decline": 5.0,
    "rainfall_deficit": 20.0,
    "temperature_anomaly": 2.0,
}


# ============================================================
# VALUTAZIONE DELLE SINGOLE CONDIZIONI
# ============================================================

def evaluate_hydrological_conditions(overview):

    signals = []

    hydrology = overview["hydrology"]

    flow_variation = (
        hydrology["river_flow"]["variation_percentage"]
    )

    reservoir_variation = (
        hydrology["reservoir_storage"]["variation_percentage"]
    )

    groundwater_variation = (
        hydrology["groundwater_level"]["variation_percentage"]
    )

    if flow_variation <= -RISK_THRESHOLDS["river_flow_decline"]:

        signals.append({
            "indicator": "Portata fluviale",
            "value": flow_variation,
            "unit": "%",
            "severity": "warning",
            "message": (
                "È stata rilevata una diminuzione della portata fluviale."
            ),
        })

    if reservoir_variation <= -RISK_THRESHOLDS["reservoir_decline"]:

        signals.append({
            "indicator": "Riserve negli invasi",
            "value": reservoir_variation,
            "unit": "%",
            "severity": "warning",
            "message": (
                "È stata rilevata una diminuzione delle riserve negli invasi."
            ),
        })

    if groundwater_variation <= -RISK_THRESHOLDS["groundwater_decline"]:

        signals.append({
            "indicator": "Livello delle falde",
            "value": groundwater_variation,
            "unit": "%",
            "severity": "warning",
            "message": (
                "È stata rilevata una diminuzione del livello delle falde."
            ),
        })

    return signals


# ============================================================
# VALUTAZIONE DELLE CONDIZIONI CLIMATICHE
# ============================================================

def evaluate_climatic_conditions(overview):

    signals = []

    climate = overview["climate"]

    rainfall_deficit = (
        climate["rainfall"]["deficit_percentage"]
    )

    temperature_anomaly = (
        climate["temperature"]["anomaly_c"]
    )

    if rainfall_deficit >= RISK_THRESHOLDS["rainfall_deficit"]:

        signals.append({
            "indicator": "Deficit pluviometrico",
            "value": rainfall_deficit,
            "unit": "%",
            "severity": "warning",
            "message": (
                "Le precipitazioni risultano inferiori "
                "ai valori di riferimento."
            ),
        })

    if temperature_anomaly >= RISK_THRESHOLDS["temperature_anomaly"]:

        signals.append({
            "indicator": "Anomalia termica",
            "value": temperature_anomaly,
            "unit": "°C",
            "severity": "warning",
            "message": (
                "La temperatura media risulta superiore "
                "al valore di riferimento."
            ),
        })

    return signals


# ============================================================
# CALCOLO DELL'INDICE DIMOSTRATIVO DI ATTENZIONE
# ============================================================

def calculate_attention_index(signals):

    weights = {
        "Portata fluviale": 25,
        "Riserve negli invasi": 25,
        "Livello delle falde": 15,
        "Deficit pluviometrico": 20,
        "Anomalia termica": 15,
    }

    score = sum(
        weights.get(signal["indicator"], 0)
        for signal in signals
    )

    return min(score, 100)


# ============================================================
# CLASSIFICAZIONE DEL LIVELLO DI ATTENZIONE
# ============================================================

def classify_drought_attention(score):

    if score < 20:

        return "Basso"

    elif score < 40:

        return "Moderato"

    elif score < 70:

        return "Elevato"

    else:

        return "Molto elevato"


# ============================================================
# GENERAZIONE DELLE RACCOMANDAZIONI
# ============================================================

def generate_prevention_recommendations(signals):

    recommendations = []

    indicators = {
        signal["indicator"]
        for signal in signals
    }

    if "Portata fluviale" in indicators:

        recommendations.append(
            "Approfondire il monitoraggio delle portate "
            "e verificare i deflussi ecologici."
        )

    if "Riserve negli invasi" in indicators:

        recommendations.append(
            "Verificare i volumi effettivamente disponibili "
            "negli invasi e la loro evoluzione."
        )

    if "Livello delle falde" in indicators:

        recommendations.append(
            "Monitorare l'andamento delle falde "
            "e le condizioni di ricarica."
        )

    if "Deficit pluviometrico" in indicators:

        recommendations.append(
            "Valutare il deficit delle precipitazioni "
            "e aggiornare il monitoraggio meteorologico."
        )

    if "Anomalia termica" in indicators:

        recommendations.append(
            "Valutare il possibile aumento della domanda idrica "
            "e dell'evapotraspirazione."
        )

    if not recommendations:

        recommendations.append(
            "Continuare il monitoraggio periodico "
            "delle condizioni idriche e climatiche."
        )

    recommendations.append(
        "Le segnalazioni sono indicative e non costituiscono "
        "un'allerta ufficiale o una previsione di siccità."
    )

    return recommendations


# ============================================================
# ESECUZIONE COMPLETA DEL SISTEMA DI ALLERTA
# ============================================================

def run_drought_assessment(mode="simulated"):

    integrated_data = run_data_integration(mode)

    overview = integrated_data["overview"]

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

        "method": (
            "Indice dimostrativo basato su soglie e pesi "
            "predefiniti. Non costituisce un indice scientifico "
            "ufficiale di siccità."
        ),

    }
