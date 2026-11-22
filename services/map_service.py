
# ============================================================
# AQUA COMMONS AI
# MAP SERVICE
# Collegamento tra dati geografici e visualizzazione
# ============================================================

from services.geography import get_geography_data

from services.map_visualization import (
    prepare_map_points,
    validate_map_points,
    filter_map_points,
    get_map_summary,
)

from services.map_renderer import (
    render_monitoring_map,
)


# ============================================================
# CARICAMENTO DEI DATI CARTOGRAFICI
# ============================================================

def load_map_data(mode="simulated"):

    geography = get_geography_data(mode)

    raw_data = geography["data"]

    map_data = prepare_map_points(
        raw_data
    )

    validation = validate_map_points(
        map_data
    )

    summary = get_map_summary(
        map_data
    )

    return {

        "data": map_data,

        "validation": validation,

        "summary": summary,

        "data_type": mode,

    }


# ============================================================
# APPLICAZIONE DEI FILTRI
# ============================================================

def apply_map_filters(map_data, selected_categories):

    filtered_data = filter_map_points(
        map_data,
        selected_categories,
    )

    return {

        "data": filtered_data,

        "summary": get_map_summary(
            filtered_data
        ),

    }


# ============================================================
# VISUALIZZAZIONE COMPLETA
# ============================================================

def display_map(st, mode="simulated"):

    map_result = load_map_data(mode)

    map_data = map_result["data"]

    validation = map_result["validation"]

    if not validation["valid"]:

        st.warning(
            validation["message"]
        )

        return map_result

    if map_data.empty:

        st.info(
            "Non sono disponibili punti geografici "
            "per la visualizzazione."
        )

        return map_result

    categories = sorted(
        map_data["category"].dropna().unique().tolist()
    )

    selected_categories = st.multiselect(
        "Categorie da visualizzare",
        options=categories,
        default=categories,
        key="map_categories",
    )

    filtered_result = apply_map_filters(
        map_data,
        selected_categories,
    )

    filtered_data = filtered_result["data"]

    filtered_summary = filtered_result["summary"]

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Punti geografici",
            filtered_summary["total_points"],
        )

    with col2:

        st.metric(
            "Categorie visualizzate",
            filtered_summary["categories"],
        )

    with col3:

        st.metric(
            "Coordinate valide",
            filtered_summary["valid_coordinates"],
        )

    if filtered_data.empty:

        st.info(
            "Nessun punto corrisponde ai filtri selezionati."
        )

    else:

        render_monitoring_map(
            st,
            filtered_data,
        )

    st.caption(
        "Fonte: dataset dimostrativo. "
        "Le coordinate sono illustrative e non rappresentano "
        "necessariamente stazioni o infrastrutture reali."
    )

    return map_result
