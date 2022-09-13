from django.core.paginator import Paginator

from .constants import LIMIT_POST


def paginator_post(request, temp):
    """Создает пагинацию страницы, на вход принимает запрос и посты."""
    paginator = Paginator(temp, LIMIT_POST)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
