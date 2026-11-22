
# ============================================================
# AQUA COMMONS AI
# HYDROLOGY SERVICE
# Monitoraggio dei parametri idrologici
# ============================================================

import pandas as pd


# ============================================================
# CONFIGURAZIONE DEL DATASET DIMOSTRATIVO
# ============================================================

DEMO_SOURCE = "Dataset simulato AQUA COMMONS AI"

DEMO_TERRITORY = "Bacino dimostrativo"

DEMO_FLOW = [
    18.5, 17.9, 18.2, 16.8, 16.1, 15.7, 16.3,
    15.2, 14.8, 14.5, 13.9, 14.2, 13.4, 12.8
]

DEMO_RESERVOIR = [
    72.0, 71.8, 71.5, 71.2, 70.9, 70.5, 70.2,
    69.9, 69.5, 69.2, 68.9, 68.5, 68.2, 67.8
]

DEMO_GROUNDWATER = [
    8.2, 8.2, 8.1, 8.1, 8.0, 8.0, 7.9,
    7.9, 7.8, 7.8, 7.7, 7.7, 7.6, 7.6
]


# ============================================================
# CARICAMENTO DEI DATI IDROLOGICI DIMOSTRATIVI
# ============================================================

def load_demo_hydrology():

    dates = pd.date_range(
        end=pd.Timestamp.today().normalize(),
        periods=14,
        freq="D"
    )

    data = pd.DataFrame({
        "date": dates,
        "river_flow_m3s": DEMO_FLOW,
        "reservoir_storage_hm3": DEMO_RESERVOIR,
        "groundwater_level_m": DEMO_GROUNDWATER,
    })

    data["data_type"] = "simulated"

    data["source"] = DEMO_SOURCE

    data["territory"] = DEMO_TERRITORY

    data["quality"] = "dato simulato"

    return data


# ============================================================
# VALIDAZIONE DEI DATI IDROLOGICI
# ============================================================

def validate_hydrology(data):

    required_columns = [
        "date",
        "river_flow_m3s",
        "reservoir_storage_hm3",
        "groundwater_level_m",
        "data_type",
        "source",
        "territory",
        "quality",
    ]

    if not isinstance(data, pd.DataFrame):

        raise TypeError(
            "I dati idrologici devono essere un DataFrame Pandas."
        )

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            f"Colonne idrologiche mancanti: {missing}"
        )

    numeric_columns = [
        "river_flow_m3s",
        "reservoir_storage_hm3",
        "groundwater_level_m",
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

    if (data[numeric_columns] < 0).any().any():

        raise ValueError(
            "Sono presenti valori idrologici negativi."
        )

    return True


# ============================================================
# CALCOLO DELLA VARIAZIONE TEMPORALE
# ============================================================

def calculate_variation(series):

    if len(series) < 2:
        return 0.0

    initial_value = float(series.iloc[0])

    final_value = float(series.iloc[-1])

    if initial_value == 0:
        return 0.0

    variation = (
        (final_value - initial_value)
        / initial_value
    ) * 100

    return variation


# ============================================================
# ANALISI DELLE TENDENZE IDROLOGICHE
# ============================================================

def analyze_hydrology(data):

    validate_hydrology(data)

    if data.empty:

        raise ValueError(
            "Non sono disponibili osservazioni idrologiche."
        )

    data = data.sort_values("date").reset_index(drop=True)

    latest = data.iloc[-1]

    flow_variation = calculate_variation(
        data["river_flow_m3s"]
    )

    reservoir_variation = calculate_variation(
        data["reservoir_storage_hm3"]
    )

    groundwater_variation = calculate_variation(
        data["groundwater_level_m"]
    )

    return {

        "latest_date": latest["date"],

        "river_flow": {
            "value": float(latest["river_flow_m3s"]),
            "unit": "m³/s",
            "variation_percentage": flow_variation,
        },

        "reservoir_storage": {
            "value": float(latest["reservoir_storage_hm3"]),
            "unit": "hm³",
            "variation_percentage": reservoir_variation,
        },

        "groundwater_level": {
            "value": float(latest["groundwater_level_m"]),
            "unit": "m",
            "variation_percentage": groundwater_variation,
        },

        "observations": len(data),

        "data_type": latest["data_type"],

        "source": latest["source"],

        "territory": latest["territory"],

        "quality": latest["quality"],
    }


# ============================================================
# CARICAMENTO E ANALISI INTEGRATA
# ============================================================

def get_hydrology_data(mode="simulated"):

    if mode == "simulated":

        data = load_demo_hydrology()

    elif mode == "official":

        raise NotImplementedError(
            "Il collegamento alle fonti idrologiche ufficiali "
            "verrà implementato successivamente."
        )

    else:

        raise ValueError(
            "Modalità idrologica non riconosciuta."
        )

    validate_hydrology(data)

    analysis = analyze_hydrology(data)

    return {
        "data": data,
        "analysis": analysis,
    }
