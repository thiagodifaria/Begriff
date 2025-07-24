from decimal import Decimal
from typing import Any, Dict, List

EMISSION_FACTORS = {
    "transport": Decimal("0.35"),
    "food": Decimal("0.25"),
    "shopping": Decimal("0.20"),
    "utilities": Decimal("0.55"),
    "default": Decimal("0.15")
}

async def calculate_carbon_footprint(transactions: List[Dict[str, Any]]) -> dict:
    total_footprint = Decimal("0")
    footprint_by_category: Dict[str, Decimal] = {}

    for transaction in transactions:
        category = transaction.get("category", "default")
        amount = Decimal(transaction.get("amount", "0"))

        emission_factor = EMISSION_FACTORS.get(category, EMISSION_FACTORS["default"])
        footprint = abs(amount) * emission_factor

        total_footprint += footprint
        footprint_by_category[category] = footprint_by_category.get(category, Decimal("0")) + footprint

    return {
        "total_carbon_kg": total_footprint,
        "breakdown_by_category": footprint_by_category
    }
