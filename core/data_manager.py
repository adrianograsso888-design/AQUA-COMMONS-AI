
# ============================================================
# AQUA COMMONS AI
# DATA MANAGER
# Gestione centralizzata dei dati idrici
# ============================================================

from datetime import datetime

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
    """
    Crea una registrazione standardizzata.

    Ogni dato conserva:
    - nome
    - valore
    - unità di misura
    - fonte
    - tipologia
    - data di rilevazione
    - territorio
    - qualità
    """

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
    """
    Carica i valori dimostrativi iniziali.

    ATTENZIONE:
    questi valori sono simulati e non rappresentano
    misurazioni ufficiali di un bacino idrografico.
    """

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

    return pd.DataFrame(records)


# ============================================================
# VALIDAZIONE DEI DATI
# ============================================================

def validate_data(data):

    required_columns = [
        "name",
        "value",
        "unit",
        "source",
        "data_type",
        "timestamp",
        "territory",
        "quality",
    ]

    if not isinstance(data, pd.DataFrame):
        raise TypeError("Il dataset deve essere un DataFrame Pandas.")

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Colonne mancanti nel dataset: {missing_columns}"
        )

    if data["value"].isna().any():
        raise ValueError("Sono presenti valori mancanti.")

    if not pd.to_numeric(
        data["value"], errors="coerce"
    ).notna().all():
        raise ValueError("Sono presenti valori non numerici.")

    allowed_types = [
        "official",
        "manual",
        "simulated",
    ]

    invalid_types = ~data["data_type"].isin(allowed_types)

    if invalid_types.any():
        raise ValueError("Tipologia di dato non riconosciuta.")

    return True


# ============================================================
# GESTIONE DEL CARICAMENTO DEI DATI
# ============================================================

def load_data(mode="simulated"):

    if mode == "simulated":

        data = load_demo_data()

    elif mode == "manual":

        data = pd.DataFrame(
            columns=[
                "name",
                "value",
                "unit",
                "source",
                "data_type",
                "timestamp",
                "territory",
                "quality",
            ]
        )

    elif mode == "official":

        # Il collegamento alle fonti istituzionali
        # verrà implementato nei moduli successivi.

        data = pd.DataFrame(
            columns=[
                "name",
                "value",
                "unit",
                "source",
                "data_type",
                "timestamp",
                "territory",
                "quality",
            ]
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

        "sources": data["source"].nunique(),

        "territories": data["territory"].nunique(),
    }
