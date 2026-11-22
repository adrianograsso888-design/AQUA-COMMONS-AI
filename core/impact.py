# ============================================================
# AQUA COMMONS AI
# IMPACT ENGINE
# Analisi degli impatti delle decisioni di allocazione
# ============================================================

from math import isfinite

from core.config import SECTORS


# ============================================================
# VALIDAZIONE DEI RISULTATI
# ============================================================

def validate_results(results):

    if not isinstance(results, dict):
        raise TypeError(
            "I risultati devono essere un dizionario."
        )

    required_global_fields = [
        "availability",
        "total_demand",
        "total_allocated",
        "total_shortage",
        "total_minimum",
        "sectors",
    ]

    for field in required_global_fields:

        if field not in results:
            raise ValueError(
                f"Manca il campo generale: {field}."
            )

    if not isinstance(results["sectors"], dict):
        raise TypeError(
            "I risultati settoriali devono essere un dizionario."
        )

    sector_results = results["sectors"]

    if set(sector_results.keys()) != set(SECTORS):
        raise ValueError(
            "I risultati devono contenere esattamente tutti i settori."
        )

    for field in required_global_fields[:-1]:

        try:
            value = float(results[field])
        except (TypeError, ValueError):
            raise ValueError(
                f"Il valore generale {field} non è numerico."
            )

        if not isfinite(value) or value < -1e-9:
            raise ValueError(
                f"Il valore generale {field} non è valido."
            )

    for sector in SECTORS:

        sector_data = sector_results[sector]

        required_fields = [
            "demand",
            "minimum",
            "allocated",
            "shortage",
            "coverage",
        ]

        for field in required_fields:

            if field not in sector_data:
                raise ValueError(
                    f"Manca il campo {field} per {sector}."
                )

            try:
                value = float(sector_data[field])
            except (TypeError, ValueError):
                raise ValueError(
                    f"Il campo {field} di {sector} non è numerico."
                )

            if not isfinite(value) or value < -1e-9:
                raise ValueError(
                    f"Il campo {field} di {sector} non è valido."
                )

        demand = float(sector_data["demand"])
        minimum = float(sector_data["minimum"])
        allocated = float(sector_data["allocated"])
        shortage = float(sector_data["shortage"])

        if minimum > demand + 1e-9:
            raise ValueError(
                f"Il minimo di {sector} supera la domanda."
            )

        if allocated > demand + 1e-9:
            raise ValueError(
                f"L'allocazione di {sector} supera la domanda."
            )

        if allocated < minimum - 1e-9:
            raise ValueError(
                f"L'allocazione di {sector} non rispetta il minimo."
            )

        expected_shortage = max(
            0.0,
            demand - allocated
        )

        if abs(shortage - expected_shortage) > 1e-6:
            raise ValueError(
                f"Il deficit di {sector} non è coerente con l'allocazione."
            )


# ============================================================
# INDICATORI DI IMPATTO PER SETTORE
# ============================================================

def calculate_sector_impacts(results):

    validate_results(results)

    impacts = {}

    for sector in SECTORS:

        sector_data = results["sectors"][sector]

        demand = float(sector_data["demand"])
        minimum = float(sector_data["minimum"])
        allocated = float(sector_data["allocated"])
        shortage = float(sector_data["shortage"])

        coverage = (
            allocated / demand * 100
            if demand > 0
            else 100.0
        )

        minimum_respected = (
            allocated >= minimum - 1e-9
        )

        shortage_percentage = (
            shortage / demand * 100
            if demand > 0
            else 0.0
        )

        impacts[sector] = {
            "demand": demand,
            "minimum": minimum,
            "allocated": allocated,
            "shortage": shortage,
            "coverage_percentage": coverage,
            "shortage_percentage": shortage_percentage,
            "minimum_respected": minimum_respected,
        }

    return impacts


# ============================================================
# INDICATORI GENERALI DELLO SCENARIO
# ============================================================

def calculate_global_impacts(results):

    validate_results(results)

    sectors = results["sectors"]

    total_demand = sum(
        float(sectors[sector]["demand"])
        for sector in SECTORS
    )

    total_allocated = sum(
        float(sectors[sector]["allocated"])
        for sector in SECTORS
    )

    total_shortage = sum(
        float(sectors[sector]["shortage"])
        for sector in SECTORS
    )

    total_minimum = sum(
        float(sectors[sector]["minimum"])
        for sector in SECTORS
    )

    availability = float(results["availability"])

    overall_coverage = (
        total_allocated / total_demand * 100
        if total_demand > 0
        else 100.0
    )

    unused_water = max(
        0.0,
        availability - total_allocated
    )

    sector_coverages = [
        float(sectors[sector]["coverage"])
        for sector in SECTORS
        if float(sectors[sector]["demand"]) > 0
    ]

    average_sector_coverage = (
        sum(sector_coverages) / len(sector_coverages)
        if sector_coverages
        else 100.0
    )

    coverage_gap = (
        max(sector_coverages) - min(sector_coverages)
        if sector_coverages
        else 0.0
    )

    minimums_respected = all(
        float(sectors[sector]["allocated"])
        >= float(sectors[sector]["minimum"]) - 1e-9
        for sector in SECTORS
    )

    return {
        "total_demand": total_demand,
        "total_allocated": total_allocated,
        "total_shortage": total_shortage,
        "total_minimum": total_minimum,
        "availability": availability,
        "unused_water": unused_water,
        "overall_coverage": overall_coverage,
        "average_sector_coverage": average_sector_coverage,
        "coverage_gap": coverage_gap,
        "minimums_respected": minimums_respected,
    }


# ============================================================
# CONFRONTO DEGLI IMPATTI TRA DUE SCENARI
# ============================================================

def compare_impacts(first_results, second_results):

    validate_results(first_results)
    validate_results(second_results)

    first_global = calculate_global_impacts(first_results)
    second_global = calculate_global_impacts(second_results)

    comparison = {}

    global_indicators = [
        "total_allocated",
        "total_shortage",
        "overall_coverage",
        "average_sector_coverage",
        "coverage_gap",
        "unused_water",
    ]

    for indicator in global_indicators:

        first_value = first_global[indicator]
        second_value = second_global[indicator]

        comparison[indicator] = {
            "first": first_value,
            "second": second_value,
            "difference": second_value - first_value,
        }

    sector_comparison = {}

    for sector in SECTORS:

        first_sector = first_results["sectors"][sector]
        second_sector = second_results["sectors"][sector]

        sector_comparison[sector] = {
            "first_allocation": first_sector["allocated"],
            "second_allocation": second_sector["allocated"],
            "allocation_difference": (
                second_sector["allocated"]
                - first_sector["allocated"]
            ),
            "first_shortage": first_sector["shortage"],
            "second_shortage": second_sector["shortage"],
            "shortage_difference": (
                second_sector["shortage"]
                - first_sector["shortage"]
            ),
            "first_coverage": first_sector["coverage"],
            "second_coverage": second_sector["coverage"],
            "coverage_difference": (
                second_sector["coverage"]
                - first_sector["coverage"]
            ),
        }

    return {
        "global": comparison,
        "sectors": sector_comparison,
    }


# ============================================================
# GENERAZIONE DI UNA SINTESI INTERPRETATIVA
# ============================================================

def generate_impact_summary(results):

    global_impacts = calculate_global_impacts(results)
    sector_impacts = calculate_sector_impacts(results)

    most_affected_sector = max(
        sector_impacts,
        key=lambda sector: sector_impacts[sector]["shortage"]
    )

    best_covered_sector = max(
        sector_impacts,
        key=lambda sector: sector_impacts[sector]["coverage_percentage"]
    )

    summary = {
        "overall_coverage": global_impacts["overall_coverage"],
        "total_shortage": global_impacts["total_shortage"],
        "most_affected_sector": most_affected_sector,
        "most_affected_shortage": (
            sector_impacts[most_affected_sector]["shortage"]
        ),
        "best_covered_sector": best_covered_sector,
        "best_covered_percentage": (
            sector_impacts[best_covered_sector]["coverage_percentage"]
        ),
        "minimums_respected": global_impacts["minimums_respected"],
        "coverage_gap": global_impacts["coverage_gap"],
    }

    return summary
