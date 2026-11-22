
# ============================================================
# AQUA COMMONS AI
# MAP VISUALIZATION
# Preparazione dei dati per la cartografia interattiva
# ============================================================

import pandas as pd


# ============================================================
# CONFIGURAZIONE DELLA MAPPA
# ============================================================

MAP_CONFIG = {

    "initial_zoom": 8,

    "map_style": "light",

    "latitude_column": "latitude",

    "longitude_column": "longitude",

    "name_column": "name",

    "category_column": "category",

}


# ============================================================
# NORMALIZZAZIONE DELLE COLONNE
# ============================================================

COLUMN_ALIASES = {

    "latitude": [
        "latitude",
        "lat",
        "Latitude",
        "Lat",
    ],

    "longitude": [
        "longitude",
        "lon",
        "long",
        "lng",
        "Longitude",
        "Lon",
        "Long",
    ],

    "name": [
        "name",
        "label",
        "station",
        "location",
        "Nome",
    ],

    "category": [
        "category",
        "type",
        "kind",
        "Categoria",
        "Tipo",
    ],

}


def find_column(data, possible_names):

    for column in possible_names:

        if column in data.columns:

            return column

    return None


# ============================================================
# PREPARAZIONE DEI PUNTI GEOGRAFICI
# ============================================================

def prepare_map_points(data):

    if isinstance(data, dict):

        data = data.get("data", pd.DataFrame())

    if not isinstance(data, pd.DataFrame):

        raise TypeError(
            "I dati geografici devono essere un DataFrame."
        )

    if data.empty:

        return pd.DataFrame(
            columns=[
                "latitude",
                "longitude",
                "name",
                "category",
            ]
        )

    latitude_column = find_column(
        data,
        COLUMN_ALIASES["latitude"],
    )

    longitude_column = find_column(
        data,
        COLUMN_ALIASES["longitude"],
    )

    name_column = find_column(
        data,
        COLUMN_ALIASES["name"],
    )

    category_column = find_column(
        data,
        COLUMN_ALIASES["category"],
    )

    if latitude_column is None or longitude_column is None:

        raise ValueError(
            "Non sono state trovate le colonne delle coordinate."
        )

    map_data = pd.DataFrame()

    map_data["latitude"] = pd.to_numeric(
        data[latitude_column],
        errors="coerce",
    )

    map_data["longitude"] = pd.to_numeric(
        data[longitude_column],
        errors="coerce",
    )

    if name_column is not None:

        map_data["name"] = (
            data[name_column]
            .fillna("Punto senza nome")
            .astype(str)
        )

    else:

        map_data["name"] = "Punto di monitoraggio"

    if category_column is not None:

        map_data["category"] = (
            data[category_column]
            .fillna("Altro")
            .astype(str)
        )

    else:

        map_data["category"] = "Altro"

    map_data = map_data.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    map_data = map_data[
        map_data["latitude"].between(-90, 90)
        &
        map_data["longitude"].between(-180, 180)
    ]

    map_data = map_data.reset_index(drop=True)

    return map_data


# ============================================================
# CONTROLLO QUALITÀ DEI DATI CARTOGRAFICI
# ============================================================

def validate_map_points(map_data):

    required_columns = [
        "latitude",
        "longitude",
        "name",
        "category",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in map_data.columns
    ]

    if missing_columns:

        return {

            "valid": False,

            "total_points": len(map_data),

            "valid_coordinates": 0,

            "message": (
                "Colonne mancanti: "
                + ", ".join(missing_columns)
            ),

        }

    if map_data.empty:

        return {

            "valid": False,

            "total_points": 0,

            "valid_coordinates": 0,

            "message": "Nessun punto geografico disponibile.",

        }

    coordinates_valid = (
        map_data["latitude"].between(-90, 90)
        &
        map_data["longitude"].between(-180, 180)
    )

    valid_count = int(
        coordinates_valid.sum()
    )

    all_valid = bool(
        coordinates_valid.all()
    )

    return {

        "valid": all_valid,

        "total_points": len(map_data),

        "valid_coordinates": valid_count,

        "message": (
            "Coordinate valide."
            if all_valid
            else "Sono presenti coordinate non valide."
        ),

    }


# ============================================================
# FILTRO PER CATEGORIA
# ============================================================

def filter_map_points(map_data, selected_categories):

    if map_data.empty:

        return map_data.copy()

    if not selected_categories:

        return map_data.iloc[0:0].copy()

    filtered = map_data[
        map_data["category"].isin(
            selected_categories
        )
    ].copy()

    return filtered.reset_index(drop=True)


# ============================================================
# RIEPILOGO CARTOGRAFICO
# ============================================================

def get_map_summary(map_data):

    if map_data.empty:

        return {

            "total_points": 0,

            "categories": 0,

            "category_breakdown": {},

            "valid_coordinates": 0,

            "center_latitude": None,

            "center_longitude": None,

        }

    category_counts = (
        map_data["category"]
        .value_counts()
        .to_dict()
    )

    valid_coordinates = (
        map_data["latitude"].between(-90, 90)
        &
        map_data["longitude"].between(-180, 180)
    )

    return {

        "total_points": len(map_data),

        "categories": len(category_counts),

        "category_breakdown": category_counts,

        "valid_coordinates": int(
            valid_coordinates.sum()
        ),

        "center_latitude": float(
            map_data["latitude"].mean()
        ),

        "center_longitude": float(
            map_data["longitude"].mean()
        ),

    }
