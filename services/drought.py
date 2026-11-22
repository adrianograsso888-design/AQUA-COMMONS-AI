
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
# PESI DEGLI INDICATORI
# ============================================================

INDICATOR_WEIGHTS = {
    "Portata fluviale": 25,
    "Riserve negli invasi": 25,
    "Livello delle falde": 15,
    "Deficit pluviometrico": 20,
    "Anomalia termica": 15,
}


# ============================================================
# VALIDAZIONE DEGLI INDICATORI
# ============================================================

def validate_indicator(value, name):

    if value is None:

        raise ValueError(
            f"Indicatore mancante: {name}."
        )

    try:

        value = float(value)

    except (TypeError, ValueError):

        raise ValueError(
            f"Indicatore non numerico: {name}."
        )

    if not pd_is_finite(value):

        raise ValueError(
            f"Indicatore non valido: {name}."
        )

    return value


def pd_is_finite(value):

    import math

    return math.isfinite(value)


# ============================================================
# VALUTAZIONE DELLE CONDIZIONI IDROLOGICHE
# ============================================================

def evaluate_hydrological_conditions(overview):

    signals = []

    hydrology = overview["hydrology"]

    flow_variation = validate_indicator(
        hydrology["river_flow"]["variation_percentage"],
        "Variazione della portata fluviale"
    )

    reservoir_variation = validate_indicator(
        hydrology["reservoir_storage"]["variation_percentage"],
        "Variazione delle riserve negli invasi"
    )

    groundwater_variation = validate_indicator(
        hydrology["groundwater_level"]["variation_percentage"],
        "Variazione del livello delle falde"
    )

    if flow_variation <= -RISK_THRESHOLDS["river_flow_decline"]:

        signals.append({
            "indicator": "Portata fluviale",
            "value": flow_variation,
            "unit": "%",
            "severity": "warning",
            "message": (
                "È stata rilevata una diminuzione "
                "della portata fluviale."
            ),
        })

    if reservoir_variation <= -RISK_THRESHOLDS["reservoir_decline"]:

        signals.append({
            "indicator": "Riserve negli invasi",
            "value": reservoir_variation,
            "unit": "%",
            "severity": "warning",
            "message": (
                "È stata rilevata una diminuzione "
                "delle riserve negli invasi."
            ),
        })

    if groundwater_variation <= -RISK_THRESHOLDS["groundwater_decline"]:

        signals.append({
            "indicator": "Livello delle falde",
            "value": groundwater_variation,
            "unit": "%",
            "severity": "warning",
            "message": (
                "È stata rilevata una diminuzione "
                "del livello delle falde."
            ),
        })

    return signals


# ============================================================
# VALUTAZIONE DELLE CONDIZIONI CLIMATICHE
# ============================================================

def evaluate_climatic_conditions(overview):

    signals = []

    climate = overview["climate"]

    rainfall_deficit = validate_indicator(
        climate["rainfall"]["deficit_percentage"],
        "Deficit pluviometrico"
    )

    temperature_anomaly = validate_indicator(
        climate["temperature"]["anomaly_c"],
        "Anomalia termica"
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

    score = 0

    detected_indicators = set()

    for signal in signals:

        indicator = signal["indicator"]

        if indicator not in INDICATOR_WEIGHTS:

            continue

        if indicator in detected_indicators:

            continue

        detected_indicators.add(indicator)

        score += INDICATOR_WEIGHTS[indicator]

    return min(score, 100)


# ============================================================
# CLASSIFICAZIONE DEL LIVELLO DI ATTENZIONE
# ============================================================

def classify_drought_attention(score):

    score = validate_indicator(
        score,
        "Indice di attenzione"
    )

    if score < 0 or score > 100:

        raise ValueError(
            "L'indice deve essere compreso tra 0 e 100."
        )

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

        "thresholds": RISK_THRESHOLDS.copy(),

        "weights": INDICATOR_WEIGHTS.copy(),

        "method": (
            "Indice dimostrativo basato su soglie e pesi "
            "predefiniti. Non costituisce un indice scientifico "
            "ufficiale di siccità e non produce previsioni."
        ),

    }
