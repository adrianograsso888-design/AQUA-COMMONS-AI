
# ============================================================
# AQUA COMMONS AI
# GEOGRAPHY SERVICE
# Gestione delle informazioni geografiche e territoriali
# ============================================================

import pandas as pd


# ============================================================
# CONFIGURAZIONE GEOGRAFICA DIMOSTRATIVA
# ============================================================

DEMO_TERRITORY = {
    "name": "Bacino dimostrativo",
    "region": "Territorio non specificato",
    "country": "Italia",
    "data_type": "simulated",
    "source": "Dataset geografico dimostrativo AQUA COMMONS AI",
}


# ============================================================
# PUNTI GEOGRAFICI DIMOSTRATIVI
# ============================================================

DEMO_LOCATIONS = [

    {
        "name": "Stazione idrometrica A",
        "category": "Stazione di monitoraggio",
        "latitude": 45.70,
        "longitude": 11.75,
        "indicator": "Portata fluviale",
        "value": 18.5,
        "unit": "m³/s",
    },

    {
        "name": "Stazione idrometrica B",
        "category": "Stazione di monitoraggio",
        "latitude": 45.65,
        "longitude": 11.85,
        "indicator": "Portata fluviale",
        "value": 14.2,
        "unit": "m³/s",
    },

    {
        "name": "Inv as o dimostrativo",
        "category": "Inv as o",
        "latitude": 45.60,
        "longitude": 11.90,
        "indicator": "Volume immagazzinato",
        "value": 68.0,
        "unit": "hm³",
    },

    {
        "name": "Stazione climatica A",
        "category": "Stazione climatica",
        "latitude": 45.75,
        "longitude": 11.80,
        "indicator": "Temperatura",
        "value": 25.5,
        "unit": "°C",
    },

]


# ============================================================
# CARICAMENTO DEI PUNTI GEOGRAFICI
# ============================================================

def load_demo_locations():

    data = pd.DataFrame(DEMO_LOCATIONS)

    data["territory"] = DEMO_TERRITORY["name"]

    data["data_type"] = "simulated"

    data["source"] = (
        "Dataset geografico dimostrativo AQUA COMMONS AI"
    )

    data["quality"] = "coordinate simulate"

    return data


# ============================================================
# VALIDAZIONE DELLE COORDINATE
# ============================================================

def validate_geography(data):

    required_columns = [

        "name",

        "category",

        "latitude",

        "longitude",

        "indicator",

        "value",

        "unit",

        "territory",

        "data_type",

        "source",

        "quality",

    ]

    if not isinstance(data, pd.DataFrame):

        raise TypeError(
            "I dati geografici devono essere un DataFrame Pandas."
        )

    missing = [

        column

        for column in required_columns

        if column not in data.columns

    ]

    if missing:

        raise ValueError(
            f"Colonne geografiche mancanti: {missing}"
        )

    for column in ["latitude", "longitude", "value"]:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        if data[column].isna().any():

            raise ValueError(
                f"Valori non validi nella colonna {column}."
            )

    if not data["latitude"].between(-90, 90).all():

        raise ValueError(
            "Sono presenti latitudini non valide."
        )

    if not data["longitude"].between(-180, 180).all():

        raise ValueError(
            "Sono presenti longitudini non valide."
        )

    return True


# ============================================================
# FILTRAGGIO PER CATEGORIA
# ============================================================

def filter_locations(data, category=None):

    validate_geography(data)

    if category is None:

        return data.copy()

    return data[
        data["category"] == category
    ].copy()


# ============================================================
# RIEPILOGO TERRITORIALE
# ============================================================

def get_geography_summary(data):

    validate_geography(data)

    return {

        "total_locations": len(data),

        "categories": (
            data["category"]
            .value_counts()
            .to_dict()
        ),

        "territories": (
            data["territory"]
            .dropna()
            .unique()
            .tolist()
        ),

        "data_type": (
            data["data_type"]
            .unique()
            .tolist()
        ),

        "source": (
            data["source"]
            .unique()
            .tolist()
        ),

    }


# ============================================================
# PREPARAZIONE DEI DATI PER LA MAPPA
# ============================================================

def prepare_map_data(data):

    validate_geography(data)

    map_data = data.copy()

    map_data = map_data.rename(
        columns={

            "latitude": "lat",

            "longitude": "lon",

        }
    )

    return map_data[
        [
            "name",
            "category",
            "lat",
            "lon",
            "indicator",
            "value",
            "unit",
            "territory",
            "data_type",
        ]
    ]


# ============================================================
# CARICAMENTO DEL SERVIZIO GEOGRAFICO
# ============================================================

def get_geography_data(mode="simulated"):

    if mode == "simulated":

        data = load_demo_locations()

    elif mode == "official":

        raise NotImplementedError(
            "Il collegamento ai dati geografici ufficiali "
            "verrà implementato successivamente."
        )

    else:

        raise ValueError(
            "Modalità geografica non riconosciuta."
        )

    validate_geography(data)

    return {

        "data": data,

        "map_data": prepare_map_data(data),

        "summary": get_geography_summary(data),

        "territory": DEMO_TERRITORY,

    }
