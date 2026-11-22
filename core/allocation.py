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

    availability = float(availability)

    if availability < 0:
        raise ValueError(
            "La disponibilità idrica non può essere negativa."
        )

    if set(demands.keys()) != set(SECTORS):
        raise ValueError(
            "Le domande devono includere tutti i settori."
        )

    if set(minimums.keys()) != set(SECTORS):
        raise ValueError(
            "I fabbisogni minimi devono includere tutti i settori."
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
                f"Il minimo di {sector} supera la sua domanda."
            )

    total_minimum = sum(
        float(minimums[sector])
        for sector in SECTORS
    )

    if total_minimum > availability + 1e-9:
        raise ValueError(
            "Allocazione impossibile: la disponibilità è inferiore "
            "alla somma dei fabbisogni minimi."
        )


# ============================================================
# ALLOCAZIONE PROPORZIONALE
# ============================================================

def proportional_allocation(availability, demands, minimums):

    validate_inputs(availability, demands, minimums)

    allocations = {
        sector: float(minimums[sector])
        for sector in SECTORS
    }

    remaining = (
        float(availability)
        - sum(allocations.values())
    )

    capacities = {
        sector: max(
            0.0,
            float(demands[sector]) - allocations[sector]
        )
        for sector in SECTORS
    }

    tolerance = 1e-9

    while remaining > tolerance:

        active = [
            sector
            for sector in SECTORS
            if capacities[sector] > tolerance
        ]

        if not active:
            break

        total_capacity = sum(
            capacities[sector]
            for sector in active
        )

        if total_capacity <= tolerance:
            break

        amount_to_distribute = remaining
        distributed = 0.0

        for sector in active:

            share = (
                amount_to_distribute
                * capacities[sector]
                / total_capacity
            )

            additional = min(
                share,
                capacities[sector]
            )

            allocations[sector] += additional
            capacities[sector] -= additional
            distributed += additional

        remaining -= distributed

        if distributed <= tolerance:
            break

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

    if (
        len(priority_order) != len(SECTORS)
        or set(priority_order) != set(SECTORS)
    ):
        raise ValueError(
            "L'ordine di priorità deve contenere tutti i settori "
            "una sola volta."
        )

    allocations = {
        sector: float(minimums[sector])
        for sector in SECTORS
    }

    remaining = (
        float(availability)
        - sum(allocations.values())
    )

    for sector in priority_order:

        additional_need = (
            float(demands[sector]) - allocations[sector]
        )

        additional = min(
            additional_need,
            remaining
        )

        allocations[sector] += additional
        remaining -= additional

        if remaining <= 1e-9:
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

        demand = float(demands[sector])
        allocated = float(allocations[sector])

        coverage = (
            allocated / demand * 100
            if demand > 0
            else 100.0
        )

        shortage = max(
            0.0,
            demand - allocated
        )

        results[sector] = {
            "demand": demand,
            "minimum": float(minimums[sector]),
            "allocated": allocated,
            "shortage": shortage,
            "coverage": coverage,
        }

    total_allocated = sum(allocations.values())

    return {
        "strategy": strategy,
        "availability": float(availability),
        "total_demand": sum(
            float(demands[sector])
            for sector in SECTORS
        ),
        "total_minimum": sum(
            float(minimums[sector])
            for sector in SECTORS
        ),
        "total_allocated": total_allocated,
        "unused_water": max(
            0.0,
            float(availability) - total_allocated
        ),
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
