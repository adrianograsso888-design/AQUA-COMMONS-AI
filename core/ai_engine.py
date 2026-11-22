
# ============================================================
# AQUA COMMONS AI
# AI ENGINE
# Motore centrale di analisi e supporto decisionale
# ============================================================

from math import isfinite

from core.config import SECTORS

from core.impact import (
    calculate_global_impacts,
    calculate_sector_impacts,
    compare_impacts,
)


# ============================================================
# COLONNE NECESSARIE PER L'ANALISI DEI DATI
# ============================================================

REQUIRED_DATA_COLUMNS = [
    "name",
    "value",
    "source",
    "data_type",
]


# ============================================================
# 1. DATA INTELLIGENCE
# ============================================================

def analyze_data_quality(data):

    if data is None or data.empty:

        return {
            "status": "error",
            "message": "Non sono disponibili dati da analizzare.",
            "records": 0,
            "sources": [],
            "source_count": 0,
            "simulated_records": 0,
            "official_records": 0,
            "manual_records": 0,
        }

    missing_columns = [
        column
        for column in REQUIRED_DATA_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:

        return {
            "status": "error",
            "message": (
                "Mancano alcune colonne necessarie: "
                + ", ".join(missing_columns)
            ),
            "records": len(data),
            "sources": [],
            "source_count": 0,
        }

    records = len(data)

    simulated = int(
        (data["data_type"] == "simulated").sum()
    )

    official = int(
        (data["data_type"] == "official").sum()
    )

    manual = int(
        (data["data_type"] == "manual").sum()
    )

    # CORREZIONE:
    # sources deve essere una lista e non un intero.
    sources = sorted(
        data["source"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    source_count = len(sources)

    if simulated == records:

        status = "simulated"

    elif official == records:

        status = "official"

    elif manual == records:

        status = "manual"

    else:

        status = "hybrid"

    return {
        "status": status,
        "records": records,
        "simulated_records": simulated,
        "official_records": official,
        "manual_records": manual,
        "sources": sources,
        "source_count": source_count,
        "message": "Dataset analizzato correttamente.",
    }


# ============================================================
# 2. ANOMALY DETECTION
# ============================================================

def detect_anomalies(data):

    anomalies = []

    if data is None or data.empty:

        return anomalies

    missing_columns = [
        column
        for column in ["name", "value"]
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            "Impossibile rilevare anomalie. "
            "Mancano le colonne: "
            + ", ".join(missing_columns)
        )

    for index, row in data.iterrows():

        variable = str(row["name"])
        raw_value = row["value"]

        try:

            value = float(raw_value)

        except (TypeError, ValueError):

            anomalies.append({
                "row": str(index),
                "variable": variable,
                "value": str(raw_value),
                "problem": "Valore mancante o non numerico.",
                "severity": "high",
            })

            continue

        if not isfinite(value):

            anomalies.append({
                "row": str(index),
                "variable": variable,
                "value": str(raw_value),
                "problem": "Valore non finito o non valido.",
                "severity": "high",
            })

        elif value < 0:

            anomalies.append({
                "row": str(index),
                "variable": variable,
                "value": value,
                "problem": "Valore negativo non ammesso.",
                "severity": "high",
            })

    return anomalies


# ============================================================
# 3. WATER RISK ASSESSMENT
# ============================================================

def assess_water_risk(results):

    global_impacts = calculate_global_impacts(results)

    demand = global_impacts["total_demand"]

    shortage = global_impacts["total_shortage"]

    shortage_percentage = (
        shortage / demand * 100
        if demand > 0
        else 0.0
    )

    if shortage_percentage == 0:

        risk = "Basso"

    elif shortage_percentage <= 15:

        risk = "Moderato"

    elif shortage_percentage <= 30:

        risk = "Elevato"

    else:

        risk = "Critico"

    return {
        "risk_level": risk,
        "shortage_percentage": shortage_percentage,
        "total_shortage": shortage,
        "total_demand": demand,
        "method": (
            "Classificazione dimostrativa basata sulla "
            "percentuale di domanda non soddisfatta. "
            "Non rappresenta un indice scientifico "
            "di siccità o una previsione."
        ),
    }


# ============================================================
# 4. SCENARIO INTELLIGENCE
# ============================================================

def analyze_scenario(results):

    global_impacts = calculate_global_impacts(results)

    sector_impacts = calculate_sector_impacts(results)

    most_affected = max(
        SECTORS,
        key=lambda sector: sector_impacts[sector]["shortage"]
    )

    least_affected = min(
        SECTORS,
        key=lambda sector: sector_impacts[sector]["shortage"]
    )

    observations = []

    if global_impacts["total_shortage"] > 0:

        observations.append(
            "La disponibilità idrica non soddisfa "
            "integralmente la domanda complessiva."
        )

    else:

        observations.append(
            "La domanda complessiva risulta soddisfatta."
        )

    if not global_impacts["minimums_respected"]:

        observations.append(
            "Almeno un fabbisogno minimo non risulta rispettato."
        )

    else:

        observations.append(
            "Tutti i fabbisogni minimi risultano rispettati."
        )

    observations.append(
        f"Il settore con la maggiore carenza assoluta è: "
        f"{most_affected}."
    )

    return {
        "observations": observations,
        "most_affected_sector": most_affected,
        "least_affected_sector": least_affected,
        "coverage_gap": global_impacts["coverage_gap"],
    }


# ============================================================
# 5. COMPARATIVE SCENARIO INTELLIGENCE
# ============================================================

def compare_scenarios(first_results, second_results):

    comparison = compare_impacts(
        first_results,
        second_results
    )

    sector_effects = comparison["sectors"]

    sectors_receiving_more = []
    sectors_receiving_less = []

    for sector in SECTORS:

        difference = sector_effects[sector][
            "allocation_difference"
        ]

        if difference > 1e-9:

            sectors_receiving_more.append(sector)

        elif difference < -1e-9:

            sectors_receiving_less.append(sector)

    return {
        "comparison": comparison,
        "sectors_receiving_more": sectors_receiving_more,
        "sectors_receiving_less": sectors_receiving_less,
    }


# ============================================================
# 6. DECISION ASSISTANT
# ============================================================

def generate_decision_explanation(results):

    global_impacts = calculate_global_impacts(results)

    sector_impacts = calculate_sector_impacts(results)

    risk = assess_water_risk(results)

    most_affected = max(
        SECTORS,
        key=lambda sector: sector_impacts[sector]["shortage"]
    )

    explanation = []

    explanation.append(
        f"Livello di rischio rispetto alla domanda: "
        f"{risk['risk_level']}."
    )

    explanation.append(
        f"Domanda complessiva: "
        f"{global_impacts['total_demand']:.2f} hm³."
    )

    explanation.append(
        f"Acqua assegnata: "
        f"{global_impacts['total_allocated']:.2f} hm³."
    )

    explanation.append(
        f"Domanda non soddisfatta: "
        f"{global_impacts['total_shortage']:.2f} hm³."
    )

    explanation.append(
        f"Il settore maggiormente colpito "
        f"in termini assoluti è {most_affected}."
    )

    if global_impacts["minimums_respected"]:

        explanation.append(
            "I fabbisogni minimi impostati risultano rispettati."
        )

    else:

        explanation.append(
            "ATTENZIONE: alcuni fabbisogni minimi "
            "non risultano rispettati."
        )

    explanation.append(
        "La classificazione del rischio è dimostrativa "
        "e basata sul deficit di allocazione."
    )

    explanation.append(
        "Questa analisi costituisce un supporto tecnico: "
        "non rappresenta una decisione amministrativa "
        "e non sostituisce la valutazione dell'autorità competente."
    )

    return explanation


# ============================================================
# 7. ANALISI INTEGRATA
# ============================================================

def run_integrated_analysis(data, results):

    data_quality = analyze_data_quality(data)

    anomalies = detect_anomalies(data)

    water_risk = assess_water_risk(results)

    scenario = analyze_scenario(results)

    decision_explanation = generate_decision_explanation(
        results
    )

    return {
        "data_quality": data_quality,
        "anomalies": anomalies,
        "water_risk": water_risk,
        "scenario_analysis": scenario,
        "decision_explanation": decision_explanation,
        "analysis_type": "deterministic_rule_based",
        "is_predictive_model": False,
    }
