# ============================================================
# AQUA COMMONS AI
# ALLOCATION ENGINE
# Motore matematico di allocazione idrica
# ============================================================

from core.config import SECTORS


# ============================================================
# VALIDAZIONE DEI PARAMETRI
# ============================================================

def validate_inputs(availability, demands, minimums):

    if availability < 0:
        raise ValueError("La disponibilità idrica non può essere negativa.")

    if set(demands.keys()) != set(SECTORS):
        raise ValueError("Le domande devono includere tutti i settori.")

    if set(minimums.keys()) != set(SECTORS):
        raise ValueError("I fabbisogni minimi devono includere tutti i settori.")

    for sector in SECTORS:

        if demands[sector] < 0:
            raise ValueError(
                f"La domanda di {sector} non può essere negativa."
            )

        if minimums[sector] < 0:
            raise ValueError(
                f"Il fabbisogno minimo di {sector} non può essere negativo."
            )

        if minimums[sector] > demands[sector]:
            raise ValueError(
                f"Il minimo di {sector} supera la sua domanda."
            )

    total_minimum = sum(minimums.values())

    if total_minimum > availability:
        raise ValueError(
            "Allocazione impossibile: la disponibilità è inferiore "
            "alla somma dei fabbisogni minimi."
        )


# ============================================================
# ALLOCAZIONE PROPORZIONALE
# ============================================================

def proportional_allocation(availability, demands, minimums):

    validate_inputs(availability, demands, minimums)

    allocations = minimums.copy()

    remaining = availability - sum(minimums.values())

    unmet_demands = {
        sector: demands[sector] - minimums[sector]
        for sector in SECTORS
    }

    total_unmet = sum(unmet_demands.values())

    if total_unmet > 0:

        for sector in SECTORS:

            share = unmet_demands[sector] / total_unmet

            additional = min(
                unmet_demands[sector],
                remaining * share
            )

            allocations[sector] += additional

    return allocations


# ============================================================
# ALLOCAZIONE SECONDO PRIORITÀ
# ============================================================

def priority_allocation(
    availability,
    demands,
    minimums,
    priority_order
):

    validate_inputs(availability, demands, minimums)

    if set(priority_order) != set(SECTORS):
        raise ValueError(
            "L'ordine di priorità deve contenere tutti i settori una sola volta."
        )

    allocations = minimums.copy()

    remaining = availability - sum(minimums.values())

    for sector in priority_order:

        additional_need = (
            demands[sector] - allocations[sector]
        )

        additional = min(
            additional_need,
            remaining
        )

        allocations[sector] += additional

        remaining -= additional

        if remaining <= 0:
            break

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

    validate_inputs(availability, demands, minimums)

    if strategy == "proportional":

        allocations = proportional_allocation(
            availability,
            demands,
            minimums
        )

    elif strategy == "priority":

        if priority_order is None:
            priority_order = SECTORS

        allocations = priority_allocation(
            availability,
            demands,
            minimums,
            priority_order
        )

    else:

        raise ValueError(
            "Strategia di allocazione non riconosciuta."
        )

    results = {}

    for sector in SECTORS:

        demand = demands[sector]
        allocated = allocations[sector]

        coverage = (
            allocated / demand * 100
            if demand > 0
            else 100
        )

        shortage = demand - allocated

        results[sector] = {
            "demand": demand,
            "minimum": minimums[sector],
            "allocated": allocated,
            "shortage": shortage,
            "coverage": coverage,
        }

    total_allocated = sum(allocations.values())

    return {
        "strategy": strategy,
        "availability": availability,
        "total_demand": sum(demands.values()),
        "total_minimum": sum(minimums.values()),
        "total_allocated": total_allocated,
        "unused_water": availability - total_allocated,
        "sectors": results,
    }


# ============================================================
# CONFRONTO TRA STRATEGIE
# ============================================================

def compare_strategies(
    availability,
    demands,
    minimums,
    priority_order=None,
):

    proportional = calculate_results(
        availability,
        demands,
        minimums,
        strategy="proportional",
    )

    priority = calculate_results(
        availability,
        demands,
        minimums,
        strategy="priority",
        priority_order=priority_order,
    )

    return {
        "proportional": proportional,
        "priority": priority,
    }
