# ============================================================
# AQUA COMMONS AI
# DATA MANAGER
# Gestione centralizzata dei dati idrici
# ============================================================

from datetime import datetime
from math import isfinite

import pandas as pd

from core.config import (
    SECTORS,
    DEFAULT_DEMAND,
    DEFAULT_MINIMUM,
    DEFAULT_AVAILABILITY,
)


# ============================================================
# STRUTTURA STANDARD DEI DATI
# ============================================================

DATA_COLUMNS = [
    "name",
    "value",
    "unit",
    "source",
    "data_type",
    "timestamp",
    "territory",
    "quality",
]

ALLOWED_DATA_TYPES = [
    "official",
    "manual",
    "simulated",
]


# ============================================================
# CREAZIONE DI UNA REGISTRAZIONE
# ============================================================

def create_data_record(
    name,
    value,
    unit,
    source,
    data_type="simulated",
    timestamp=None,
    territory=None,
    quality="non verificata",
):

    if timestamp is None:
        timestamp = datetime.now().isoformat()

    return {
        "name": name,
        "value": value,
        "unit": unit,
        "source": source,
        "data_type": data_type,
        "timestamp": timestamp,
        "territory": territory,
        "quality": quality,
    }


# ============================================================
# DATASET DIMOSTRATIVO
# ============================================================

def load_demo_data():

    records = []

    records.append(
        create_data_record(
            name="Disponibilità idrica",
            value=DEFAULT_AVAILABILITY,
            unit="hm³",
            source="Dataset dimostrativo AQUA COMMONS AI",
            data_type="simulated",
            quality="dato simulato",
        )
    )

    for sector in SECTORS:

        records.append(
            create_data_record(
                name=f"Domanda idrica - {sector}",
                value=DEFAULT_DEMAND[sector],
                unit="hm³",
            source="Dataset dimostrativo AQUA COMMONS AI",
            data_type="simulated",
            quality="dato simulato",
        )
        )

        records.append(
            create_data_record(
                name=f"Fabbisogno minimo - {sector}",
                value=DEFAULT_MINIMUM[sector],
                unit="hm³",
                source="Dataset dimostrativo AQUA COMMONS AI",
                data_type="simulated",
                quality="dato simulato",
            )
        )

    return pd.DataFrame(
        records,
        columns=DATA_COLUMNS,
    )


# ============================================================
# VALIDAZIONE DEI DATI
# ============================================================

def validate_data(data):

    if not isinstance(data, pd.DataFrame):

        raise TypeError(
            "Il dataset deve essere un DataFrame Pandas."
        )

    missing_columns = [
        column
        for column in DATA_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Colonne mancanti nel dataset: {missing_columns}"
        )

    if data.empty:
        return True

    # --------------------------------------------------------
    # CONTROLLO DEI CAMPI TESTUALI
    # --------------------------------------------------------

    text_columns = [
        "name",
        "unit",
        "source",
        "data_type",
        "timestamp",
        "quality",
    ]

    for column in text_columns:

        if data[column].isna().any():

            raise ValueError(
                f"Sono presenti valori mancanti nella colonna {column}."
            )

        empty_values = (
            data[column]
            .astype(str)
            .str.strip()
            .eq("")
        )

        if empty_values.any():

            raise ValueError(
                f"Sono presenti valori vuoti nella colonna {column}."
            )

    # --------------------------------------------------------
    # CONTROLLO DEI VALORI NUMERICI
    # --------------------------------------------------------

    numeric_values = pd.to_numeric(
        data["value"],
        errors="coerce",
    )

    if numeric_values.isna().any():

        raise ValueError(
            "Sono presenti valori mancanti o non numerici."
        )

    for value in numeric_values:

        if not isfinite(float(value)):

            raise ValueError(
                "Sono presenti valori numerici non finiti."
            )

    # --------------------------------------------------------
    # CONTROLLO DELLA TIPOLOGIA DEI DATI
    # --------------------------------------------------------

    invalid_types = ~data["data_type"].isin(
        ALLOWED_DATA_TYPES
    )

    if invalid_types.any():

        raise ValueError(
            "Tipologia di dato non riconosciuta."
        )

    return True


# ============================================================
# GESTIONE DEL CARICAMENTO DEI DATI
# ============================================================

def load_data(mode="simulated"):

    if mode == "simulated":

        data = load_demo_data()

    elif mode == "manual":

        data = pd.DataFrame(
            columns=DATA_COLUMNS
        )

    elif mode == "official":

        # Il collegamento alle fonti istituzionali
        # verrà implementato nei moduli successivi.

        data = pd.DataFrame(
            columns=DATA_COLUMNS
        )

    else:

        raise ValueError(
            "Modalità di caricamento non riconosciuta."
        )

    validate_data(data)

    return data


# ============================================================
# RIEPILOGO DEL DATASET
# ============================================================

def get_data_summary(data):

    validate_data(data)

    return {
        "total_records": len(data),

        "official_records": int(
            (data["data_type"] == "official").sum()
        ),

        "manual_records": int(
            (data["data_type"] == "manual").sum()
        ),

        "simulated_records": int(
            (data["data_type"] == "simulated").sum()
        ),

        "sources": int(
            data["source"].nunique()
        ),

        "territories": int(
            data["territory"].nunique()
        ),
    }
