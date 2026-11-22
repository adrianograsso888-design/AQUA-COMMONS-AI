
# ============================================================
# AQUA COMMONS AI
# MAP RENDERER
# Visualizzazione cartografica interattiva con PyDeck
# ============================================================

import pandas as pd
import pydeck as pdk


# ============================================================
# CONFIGURAZIONE DEI COLORI
# ============================================================

CATEGORY_COLORS = {

    "Idrologia": [30, 136, 229, 200],

    "Clima": [255, 152, 0, 200],

    "Invasi": [0, 150, 136, 200],

    "Falda": [121, 85, 72, 200],

    "Altro": [120, 120, 120, 200],

}


# ============================================================
# PREPARAZIONE DEI COLORI
# ============================================================

def assign_map_colors(map_data):

    colored_data = map_data.copy()

    colored_data["color"] = colored_data[
        "category"
    ].apply(
        lambda category: CATEGORY_COLORS.get(
            category,
            CATEGORY_COLORS["Altro"],
        )
    )

    return colored_data


# ============================================================
# CALCOLO DEL CENTRO DELLA MAPPA
# ============================================================

def calculate_map_view(map_data):

    if map_data.empty:

        return {

            "latitude": 45.0,

            "longitude": 11.0,

            "zoom": 7,

            "pitch": 0,

        }

    return {

        "latitude": float(
            map_data["latitude"].mean()
        ),

        "longitude": float(
            map_data["longitude"].mean()
        ),

        "zoom": 9,

        "pitch": 0,

    }


# ============================================================
# CREAZIONE DEL LIVELLO CARTOGRAFICO
# ============================================================

def create_monitoring_layer(map_data):

    if map_data.empty:

        return None

    colored_data = assign_map_colors(
        map_data
    )

    layer = pdk.Layer(

        "ScatterplotLayer",

        data=colored_data,

        get_position=[
            "longitude",
            "latitude",
        ],

        get_fill_color="color",

        get_radius=1800,

        radius_min_pixels=6,

        radius_max_pixels=18,

        pickable=True,

        auto_highlight=True,

    )

    return layer


# ============================================================
# CREAZIONE DELLA MAPPA
# ============================================================

def create_monitoring_map(map_data):

    if map_data.empty:

        return None

    view = calculate_map_view(
        map_data
    )

    layer = create_monitoring_layer(
        map_data
    )

    tooltip = {

        "html": """
        <div>
            <b>{name}</b>
            <br/>
            Categoria: {category}
        </div>
        """,

        "style": {

            "backgroundColor": "#20242b",

            "color": "white",

            "fontSize": "13px",

            "padding": "10px",

        },

    }

    deck = pdk.Deck(

        layers=[layer],

        initial_view_state=pdk.ViewState(

            latitude=view["latitude"],

            longitude=view["longitude"],

            zoom=view["zoom"],

            pitch=view["pitch"],

        ),

        tooltip=tooltip,

        map_style="light",

    )

    return deck


# ============================================================
# RENDERING STREAMLIT
# ============================================================

def render_monitoring_map(st, map_data):

    if map_data.empty:

        st.warning(
            "Non sono disponibili punti geografici da visualizzare."
        )

        return

    deck = create_monitoring_map(
        map_data
    )

    st.pydeck_chart(

        deck,

        use_container_width=True,

    )

    st.caption(
        "Mappa dimostrativa: le coordinate visualizzate "
        "non rappresentano necessariamente stazioni reali."
    )
