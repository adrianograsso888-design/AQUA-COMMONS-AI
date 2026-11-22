# ============================================================
# AQUA COMMONS AI
# WATER ALLOCATION ENGINE
# Motore di allocazione e distribuzione della risorsa idrica
# ============================================================

from core.config import SECTORS


# ============================================================
# VALIDAZIONE DEGLI INPUT
# ============================================================

def validate_inputs(
    availability,
    demands,
    minimums,
    priority_order=None,
):
    """
    Verifica la coerenza dei parametri di allocazione.
    """

    if availability is None:
        raise ValueError(
            "La disponibilità idrica non può essere vuota."
        )

    availability = float(availability)

    if availability < 0:
        raise ValueError(
            "La disponibilità idrica non può essere negativa."
        )

    if not isinstance(demands, dict):
        raise ValueError(
            "La domanda deve essere fornita come dizionario."
        )

    if not isinstance(minimums, dict):
        raise ValueError(
            "I fabbisogni minimi devono essere forniti come dizionario."
        )

    if set(demands.keys()) != set(SECTORS):
        raise ValueError(
            "La domanda deve contenere esattamente tutti i settori previsti."
        )

    if set(minimums.keys()) != set(SECTORS):
        raise ValueError(
            "I fabbisogni minimi devono contenere esattamente tutti i settori."
        )

    for sector in SECTORS:

        demand = float(demands[sector])
        minimum = float(minimums[sector])

        if demand < 0:
            raise ValueError(
                f"La domanda di {sector} non può essere negativa."
            )

        if minimum < 0:
            raise ValueError(
                f"Il fabbisogno minimo di {sector} non può essere negativo."
            )

        if minimum > demand:
            raise ValueError(
                f"Il fabbisogno minimo di {sector} supera la domanda."
            )

    total_minimum = sum(
        float(minimums[sector])
        for sector in SECTORS
    )

    if total_minimum > availability:
        raise ValueError(
            "La disponibilità idrica non è sufficiente "
            "a rispettare tutti i fabbisogni minimi."
        )

    if priority_order is not None:

        if (
            len(priority_order) != len(SECTORS)
            or set(priority_order) != set(SECTORS)
        ):
            raise ValueError(
                "L'ordine di priorità deve contenere tutti i settori "
                "una sola volta."
            )

    return True


# ============================================================
# ALLOCAZIONE PROPORZIONALE
# ============================================================

def proportional_allocation(
    availability,
    demands,
    minimums,
):
    """
    Distribuisce la risorsa idrica secondo una logica proporzionale.

    1. Garantisce prima i fabbisogni minimi.
    2. Distribuisce la risorsa residua proporzionalmente
       alla domanda ancora non soddisfatta.
    3. Rispetta il limite massimo della domanda di ogni settore.
    """

    allocations = {
        sector: float(minimums[sector])
        for sector in SECTORS
    }

    remaining_water = (
        float(availability)
        - sum(allocations.values())
    )

    while remaining_water > 1e-9:

        eligible_sectors = [
            sector
            for sector in SECTORS
            if allocations[sector] < float(demands[sector]) - 1e-9
        ]

        if not eligible_sectors:
            break

        remaining_demands = {
            sector: (
                float(demands[sector])
                - allocations[sector]
            )
            for sector in eligible_sectors
        }

        total_remaining_demand = sum(
            remaining_demands.values()
        )

        if total_remaining_demand <= 0:
            break

        distributed = 0.0

        for sector in eligible_sectors:

            proportional_share = (
                remaining_water
                * remaining_demands[sector]
                / total_remaining_demand
            )

            available_capacity = (
                float(demands[sector])
                - allocations[sector]
            )

            amount = min(
                proportional_share,
                available_capacity,
            )

            allocations[sector] += amount
            distributed += amount

        remaining_water -= distributed

        if distributed <= 1e-9:
            break

    return allocations


# ============================================================
# ALLOCAZIONE PER PRIORITÀ
# ============================================================

def priority_allocation(
    availability,
    demands,
    minimums,
    priority_order,
):
    """
    Distribuisce la risorsa secondo un ordine di priorità.

    1. Garantisce i fabbisogni minimi.
    2. Assegna la risorsa residua seguendo l'ordine stabilito.
    3. Non supera mai la domanda di ciascun settore.
    """

    allocations = {
        sector: float(minimums[sector])
        for sector in SECTORS
    }

    remaining_water = (
        float(availability)
        - sum(allocations.values())
    )

    for sector in priority_order:

        if remaining_water <= 1e-9:
            break

        remaining_demand = (
            float(demands[sector])
            - allocations[sector]
        )

        if remaining_demand <= 0:
            continue

        amount = min(
            remaining_water,
            remaining_demand,
        )

        allocations[sector] += amount
        remaining_water -= amount

    return allocations


# ============================================================
# CALCOLO DEI RISULTATI
# ============================================================

def calculate_results(
    availability,
    demands,
    minimums,
    strategy="proportional",
    priority_order=None,
):
    """
    Calcola i risultati completi di uno scenario di allocazione.

    Restituisce un dizionario strutturato compatibile con:
    - core.impact
    - core.ai_engine
    - Impact Analysis
    - Decision Report
    """

    validate_inputs(
        availability,
        demands,
        minimums,
        priority_order,
    )

    availability = float(availability)

    normalized_demands = {
        sector: float(demands[sector])
        for sector in SECTORS
    }

    normalized_minimums = {
        sector: float(minimums[sector])
        for sector in SECTORS
    }

    # --------------------------------------------------------
    # SELEZIONE STRATEGIA
    # --------------------------------------------------------

    if strategy == "proportional":

        allocations = proportional_allocation(
            availability,
            normalized_demands,
            normalized_minimums,
        )

    elif strategy == "priority":

        if priority_order is None:
            priority_order = list(SECTORS)

        allocations = priority_allocation(
            availability,
            normalized_demands,
            normalized_minimums,
            priority_order,
        )

    else:

        raise ValueError(
            "Strategia non riconosciuta. "
            "Utilizzare 'proportional' oppure 'priority'."
        )

    # --------------------------------------------------------
    # RISULTATI SETTORIALI
    # --------------------------------------------------------

    sector_results = {}

    for sector in SECTORS:

        demand = normalized_demands[sector]
        minimum = normalized_minimums[sector]
        allocated = allocations[sector]

        shortage = max(
            demand - allocated,
            0.0,
        )

        coverage = (
            allocated / demand * 100
            if demand > 0
            else 100.0
        )

        sector_results[sector] = {
            "demand": demand,
            "minimum": minimum,
            "allocated": allocated,
            "shortage": shortage,
            "coverage": coverage,
        }

    # --------------------------------------------------------
    # INDICATORI GLOBALI
    # --------------------------------------------------------

    total_demand = sum(
        normalized_demands.values()
    )

    total_minimum = sum(
        normalized_minimums.values()
    )

    total_allocated = sum(
        allocations.values()
    )

    total_shortage = sum(
        sector_results[sector]["shortage"]
        for sector in SECTORS
    )

    unused_water = max(
        availability - total_allocated,
        0.0,
    )

    # --------------------------------------------------------
    # RISULTATO COMPLETO
    # --------------------------------------------------------

    results = {
        "strategy": strategy,

        "availability": availability,

        "total_demand": total_demand,

        "total_minimum": total_minimum,

        "total_allocated": total_allocated,

        "total_shortage": total_shortage,

        "unused_water": unused_water,

        "sectors": sector_results,
    }

    return results


# ============================================================
# CONFRONTO TRA STRATEGIE
# ============================================================

def compare_strategies(
    availability,
    demands,
    minimums,
    priority_order=None,
):
    """
    Confronta allocazione proporzionale e allocazione per priorità.
    """

    if priority_order is None:
        priority_order = list(SECTORS)

    proportional_results = calculate_results(
        availability=availability,
        demands=demands,
        minimums=minimums,
        strategy="proportional",
    )

    priority_results = calculate_results(
        availability=availability,
        demands=demands,
        minimums=minimums,
        strategy="priority",
        priority_order=priority_order,
    )

    comparison = {}

    for sector in SECTORS:

        proportional_allocation_value = (
            proportional_results["sectors"][sector]["allocated"]
        )

        priority_allocation_value = (
            priority_results["sectors"][sector]["allocated"]
        )

        comparison[sector] = {
            "proportional": proportional_allocation_value,
            "priority": priority_allocation_value,
            "difference": (
                priority_allocation_value
                - proportional_allocation_value
            ),
        }

    return {
        "proportional": proportional_results,
        "priority": priority_results,
        "comparison": comparison,
    }
