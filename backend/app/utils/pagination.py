"""
Pagination utility for list API endpoints.

Provides a helper to paginate in-memory lists and build
a standardized response envelope with pagination metadata.
"""

import math
from flask import request


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def paginate(items, page=None, per_page=None):
    """
    Paginate a list of items using query-string defaults from Flask request.

    Args:
        items: Full list of items to paginate.
        page: Page number (1-indexed). Falls back to ?page= query param.
        per_page: Items per page. Falls back to ?per_page= query param.

    Returns:
        dict with keys: items, page, per_page, total, total_pages
    """
    if page is None:
        page = request.args.get('page', DEFAULT_PAGE, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)

    page = max(1, page)
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    total = len(items)
    total_pages = max(1, math.ceil(total / per_page))

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }
