from .tags import classify_category, get_product_tag
from .filters import is_irrelevant_product
from .formatting import highlight_search_terms

__all__ = [
    "classify_category", 
    "get_product_tag", 
    "is_irrelevant_product", 
    "highlight_search_terms"
]