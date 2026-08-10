"""Shared pagination classes for the Saamu Tailors API.

Every primary list page uses :class:`SaamuPageNumberPagination` so record
density is consistent across the application (6 per page), independent of the
global ``PAGE_SIZE``. ``page_size`` stays overridable per request (via
``?page_size=``) so selector/dropdown consumers that reuse a list endpoint
(e.g. tailor pickers) can opt into larger pages without changing the default
list-page behaviour.
"""

from rest_framework.pagination import PageNumberPagination


class SaamuPageNumberPagination(PageNumberPagination):
    """Standard list-page pagination: 6 records per page."""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 200


class AvailableOrdersPagination(PageNumberPagination):
    """Larger pages for the Create Invoice order picker.

    The ``available-orders`` endpoint backs a search-as-you-type selector
    rather than a list page, so it keeps a bigger page size than the 6-per-page
    list standard.
    """

    page_size = 50
