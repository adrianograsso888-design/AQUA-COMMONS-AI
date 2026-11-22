import pandas as pd

from services.hydrology import get_hydrology_data
from services.climate import get_climate_data
from services.geography import get_geography_data


def load_integrated_data(mode="simulated"):

    hydrology = get_hydrology_data(mode)
    climate = get_climate_data(mode)
    geography = get_geography_data(mode)

    return {
        "hydrology": hydrology,
        "climate": climate,
        "geography": geography,
    }


def integrate_time_series(hydrology_data, climate_data):

    hydrology = hydrology_data.copy()
    climate = climate_data.copy()

    hydrology["date"] = pd.to_datetime(hydrology["date"])
    climate["date"] = pd.to_datetime(climate["date"])

    integrated = pd.merge(
        hydrology,
        climate,
        on="date",
        how="outer",
        suffixes=("_hydrology", "_climate"),
    )

    return integrated.sort_values("date").reset_index(drop=True)


def analyze_data_provenance(data):

    if data.empty:
        return {
            "status": "empty",
            "message": "Nessun dato disponibile.",
            "sources": [],
            "data_types": [],
            "total_dates": 0,
        }

    type_columns = [
        column for column in [
            "data_type",
            "data_type_hydrology",
            "data_type_climate",
        ]
        if column in data.columns
    ]

    source_columns = [
        column for column in [
            "source",
            "source_hydrology",
            "source_climate",
        ]
        if column in data.columns
    ]

    data_types = set()
    sources = set()

    for column in type_columns:
        data_types.update(
            data[column].dropna().astype(str).unique()
        )

    for column in source_columns:
        sources.update(
            data[column].dropna().astype(str).unique()
        )

    data_types = sorted(data_types)
    sources = sorted(sources)

    if data_types == ["simulated"]:
        status = "simulated"
        message = "Il dataset contiene esclusivamente dati simulati."

    elif data_types == ["official"]:
        status = "official"
        message = "Il dataset contiene esclusivamente dati ufficiali."

    elif not data_types:
        status = "unknown"
        message = "La tipologia dei dati non è disponibile."

    else:
        status = "hybrid"
        message = "Il dataset contiene tipologie differenti di dati."

    return {
        "status": status,
        "message": message,
        "sources": sources,
        "data_types": data_types,
        "total_dates": len(data),
    }


def build_integrated_overview(
    hydrology_analysis,
    climate_analysis,
    geography_summary,
):

    return {
        "territory": hydrology_analysis["territory"],

        "hydrology": {
            "river_flow": hydrology_analysis["river_flow"],
            "reservoir_storage": hydrology_analysis["reservoir_storage"],
            "groundwater_level": hydrology_analysis["groundwater_level"],
        },

        "climate": {
            "rainfall": climate_analysis["rainfall"],
            "temperature": climate_analysis["temperature"],
        },

        "geography": {
            "total_locations": geography_summary["total_locations"],
            "categories": geography_summary["categories"],
        },

        "data_status": "simulated",
    }


def run_data_integration(mode="simulated"):

    datasets = load_integrated_data(mode)

    hydrology_data = datasets["hydrology"]["data"]
    climate_data = datasets["climate"]["data"]

    integrated_series = integrate_time_series(
        hydrology_data,
        climate_data,
    )

    provenance = analyze_data_provenance(
        integrated_series
    )

    overview = build_integrated_overview(
        datasets["hydrology"]["analysis"],
        datasets["climate"]["analysis"],
        datasets["geography"]["summary"],
    )

    return {
        "hydrology": datasets["hydrology"],
        "climate": datasets["climate"],
        "geography": datasets["geography"],
        "integrated_series": integrated_series,
        "provenance": provenance,
        "overview": overview,
    }
