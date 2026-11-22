
# ============================================================
# AQUA COMMONS AI
# CONFIGURAZIONE GENERALE DELLA PIATTAFORMA
# ============================================================

APP_NAME = "AQUA COMMONS AI"

APP_DESCRIPTION = (
    "Integrated Water Intelligence and Decision Support Platform"
)

# ============================================================
# SETTORI DI UTILIZZO DELLA RISORSA IDRICA
# ============================================================

SECTORS = [
    "Agricoltura",
    "Usi civili",
    "Industria",
    "Ambiente",
]

# ============================================================
# PARAMETRI DIMOSTRATIVI INIZIALI
# ============================================================

DEFAULT_DEMAND = {
    "Agricoltura": 70.0,
    "Usi civili": 25.0,
    "Industria": 15.0,
    "Ambiente": 15.0,
}

DEFAULT_MINIMUM = {
    "Agricoltura": 30.0,
    "Usi civili": 25.0,
    "Industria": 5.0,
    "Ambiente": 15.0,
}

DEFAULT_AVAILABILITY = 100.0

# ============================================================
# MODALITÀ DELLA PIATTAFORMA
# ============================================================

PLATFORM_MODES = [
    "Demo generica",
    "Analisi territoriale",
]

DEFAULT_PLATFORM_MODE = "Demo generica"

# ============================================================
# TERRITORIO
# ============================================================

DEFAULT_TERRITORY = "Bacino dimostrativo"

DEFAULT_REGION = "Territorio non specificato"

PILOT_TERRITORY = "Bacino Brenta–Bacchiglione"

PILOT_REGION = "Veneto, Italia"

# ============================================================
# CONFIGURAZIONE DATI
# ============================================================

DATA_MODES = [
    "Dati ufficiali",
    "Dati manuali",
    "Dati simulati",
]

# ============================================================
# CONFIGURAZIONE DEL MOTORE AI
# ============================================================

AI_ENGINE_NAME = "AQUA AI ENGINE"

AI_FEATURES = [
    "Analisi integrata dei dati",
    "Individuazione delle anomalie",
    "Valutazione del rischio idrico",
    "Confronto tra scenari",
    "Valutazione degli impatti",
    "Generazione di spiegazioni",
]

# ============================================================
# UNITÀ DI MISURA
# ============================================================

WATER_VOLUME_UNIT = "hm³"

PERCENTAGE_UNIT = "%"
