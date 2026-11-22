# ============================================================
# AQUA COMMONS AI
# IMPACT ENGINE
# Analisi degli impatti delle decisioni di allocazione
# ============================================================

from core.config import SECTORS


# ============================================================
# VALIDAZIONE DEI RISULTATI
# ============================================================

def validate_results(results):

    if not isinstance(results, dict):
        raise TypeError("I risultati devono essere un dizionario.")

    if "sectors" not in results:
        raise ValueError("Manca la sezione dei risultati settoriali.")

    sector_results = results["sectors"]

    for sector in SECTORS:

        if sector not in sector_results:
            raise ValueError(
                f"Mancano i risultati del settore: {sector}."
            )

        required_fields = [
            "demand",
            "minimum",
            "allocated",
            "shortage",
            "coverage",
        ]

        for field in required_fields:

            if field not in sector_results[sector]:
                raise ValueError(
                    f"Manca il campo {field} per {sector}."
                )


# ============================================================
# INDICATORI DI IMPATTO PER SETTORE
# ============================================================

def calculate_sector_impacts(results):

    validate_results(results)

    impacts = {}

    for sector in SECTORS:

        sector_data = results["sectors"][sector]

        demand = sector_data["demand"]
        minimum = sector_data["minimum"]
        allocated = sector_data["allocated"]
        shortage = sector_data["shortage"]

        coverage = (
            allocated / demand * 100
            if demand > 0
            else 100.0
        )

        minimum_respected = allocated >= minimum

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
        sectors[sector]["demand"]
        for sector in SECTORS
    )

    total_allocated = sum(
        sectors[sector]["allocated"]
        for sector in SECTORS
    )

    total_shortage = sum(
        sectors[sector]["shortage"]
        for sector in SECTORS
    )

    total_minimum = sum(
        sectors[sector]["minimum"]
        for sector in SECTORS
    )

    availability = results["availability"]

    overall_coverage = (
        total_allocated / total_demand * 100
        if total_demand > 0
        else 100.0
    )

    unused_water = availability - total_allocated

    sector_coverages = [
        sectors[sector]["coverage"]
        for sector in SECTORS
        if sectors[sector]["demand"] > 0
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
        sectors[sector]["allocated"]
        >= sectors[sector]["minimum"]
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
