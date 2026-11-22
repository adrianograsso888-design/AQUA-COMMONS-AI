
# ============================================================
# AQUA COMMONS AI
# CLIMATE SERVICE
# Monitoraggio delle condizioni climatiche
# ============================================================

import pandas as pd


# ============================================================
# CONFIGURAZIONE DEL DATASET DIMOSTRATIVO
# ============================================================

DEMO_SOURCE = "Dataset climatico simulato AQUA COMMONS AI"

DEMO_TERRITORY = "Bacino dimostrativo"

DEMO_RAINFALL = [
    8.0, 5.0, 2.0, 0.0, 1.0, 0.0, 3.0,
    0.0, 0.0, 1.0, 0.0, 2.0, 0.0, 0.0
]

DEMO_TEMPERATURE = [
    18.0, 19.0, 20.0, 21.0, 21.5, 22.0, 23.0,
    22.5, 24.0, 23.5, 24.5, 25.0, 24.0, 25.5
]

DEMO_REFERENCE_RAINFALL = [
    6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0,
    6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0
]

DEMO_REFERENCE_TEMPERATURE = [
    17.0, 17.0, 17.0, 17.0, 17.0, 17.0, 17.0,
    17.0, 17.0, 17.0, 17.0, 17.0, 17.0, 17.0
]


# ============================================================
# CARICAMENTO DEI DATI CLIMATICI
# ============================================================

def load_demo_climate():

    dates = pd.date_range(
        end=pd.Timestamp.today().normalize(),
        periods=14,
        freq="D"
    )

    data = pd.DataFrame({

        "date": dates,

        "rainfall_mm": DEMO_RAINFALL,

        "temperature_c": DEMO_TEMPERATURE,

        "reference_rainfall_mm": DEMO_REFERENCE_RAINFALL,

        "reference_temperature_c": DEMO_REFERENCE_TEMPERATURE,

    })

    data["data_type"] = "simulated"

    data["source"] = DEMO_SOURCE

    data["territory"] = DEMO_TERRITORY

    data["quality"] = "dato simulato"

    return data


# ============================================================
# VALIDAZIONE DEI DATI
# ============================================================

def validate_climate(data):

    required_columns = [

        "date",
        "rainfall_mm",
        "temperature_c",
        "reference_rainfall_mm",
        "reference_temperature_c",
        "data_type",
        "source",
        "territory",
        "quality",

    ]

    if not isinstance(data, pd.DataFrame):

        raise TypeError(
            "I dati climatici devono essere un DataFrame Pandas."
        )

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            f"Colonne climatiche mancanti: {missing}"
        )

    numeric_columns = [

        "rainfall_mm",
        "temperature_c",
        "reference_rainfall_mm",
        "reference_temperature_c",

    ]

    for column in numeric_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        if data[column].isna().any():

            raise ValueError(
                f"Valori mancanti o non numerici in {column}."
            )

    if (data["rainfall_mm"] < 0).any():

        raise ValueError(
            "Le precipitazioni non possono essere negative."
        )

    if (data["reference_rainfall_mm"] < 0).any():

        raise ValueError(
            "Le precipitazioni di riferimento non possono essere negative."
        )

    return True


# ============================================================
# CALCOLO DEL DEFICIT PLUVIOMETRICO
# ============================================================

def calculate_rainfall_deficit(data):

    observed = float(
        data["rainfall_mm"].sum()
    )

    reference = float(
        data["reference_rainfall_mm"].sum()
    )

    difference = reference - observed

    deficit = max(difference, 0.0)

    surplus = max(-difference, 0.0)

    deficit_percentage = (

        deficit / reference * 100

        if reference > 0

        else 0.0

    )

    return {

        "observed_mm": observed,

        "reference_mm": reference,

        "deficit_mm": deficit,

        "surplus_mm": surplus,

        "deficit_percentage": deficit_percentage,

    }


# ============================================================
# CALCOLO DELL'ANOMALIA TERMICA
# ============================================================

def calculate_temperature_anomaly(data):

    observed = float(
        data["temperature_c"].mean()
    )

    reference = float(
        data["reference_temperature_c"].mean()
    )

    anomaly = observed - reference

    return {

        "observed_average_c": observed,

        "reference_average_c": reference,

        "anomaly_c": anomaly,

    }


# ============================================================
# ANALISI CLIMATICA COMPLETA
# ============================================================

def analyze_climate(data):

    validate_climate(data)

    if data.empty:

        raise ValueError(
            "Non sono disponibili osservazioni climatiche."
        )

    data = data.sort_values(
        "date"
    ).reset_index(drop=True)

    rainfall = calculate_rainfall_deficit(
        data
    )

    temperature = calculate_temperature_anomaly(
        data
    )

    return {

        "latest_date": data.iloc[-1]["date"],

        "rainfall": rainfall,

        "temperature": temperature,

        "observations": len(data),

        "data_type": data.iloc[-1]["data_type"],

        "source": data.iloc[-1]["source"],

        "territory": data.iloc[-1]["territory"],

        "quality": data.iloc[-1]["quality"],

    }


# ============================================================
# CARICAMENTO DEL SERVIZIO CLIMATICO
# ============================================================

def get_climate_data(mode="simulated"):

    if mode == "simulated":

        data = load_demo_climate()

    elif mode == "official":

        raise NotImplementedError(
            "Il collegamento alle fonti climatiche ufficiali "
            "verrà implementato successivamente."
        )

    else:

        raise ValueError(
            "Modalità climatica non riconosciuta."
        )

    validate_climate(data)

    analysis = analyze_climate(data)

    return {

        "data": data,

        "analysis": analysis,

    }
