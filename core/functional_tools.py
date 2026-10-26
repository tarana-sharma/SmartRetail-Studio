"""
Analytical Utilities and Computational Filters.
"""
from functools import reduce
from typing import List
from core.models import RetailProduct

def filter_low_stock(products: List[RetailProduct], threshold: int = 5) -> List[RetailProduct]:
    return list(filter(lambda p: p.stock_qty < threshold, products))

def apply_tax_to_prices(products: List[RetailProduct], tax_rate: float = 0.18) -> List[float]:
    return list(map(lambda p: round(p.get_selling_price() * (1 + tax_rate), 2), products))

def compute_total_inventory_value(products: List[RetailProduct]) -> float:
    if not products:
        return 0.0
    return float(reduce(lambda acc, p: acc + (p.get_cost_price() * p.stock_qty), products, 0.0))

def get_product_names_by_category(products: List[RetailProduct], category: str) -> List[str]:
    return [p.name for p in products if p.category.lower() == category.lower()]
