from rest_framework.pagination import PageNumberPagination

from backend.settings import PAGE_SIZE


class CustomPageNumberPagination(PageNumberPagination):
    """Костомный класс пагинации"""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
