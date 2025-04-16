# linguistic_processor_app/templatetags/custom_filters.py
import re
from django import template

register = template.Library()


@register.filter
def clean_wordnet(value):
    """
    Удаляет все WordNet суффиксы (.n.01, .v.02 и т.д.) и заменяет подчеркивания на пробелы,
    затем делает первую букву заглавной.
    """
    if not isinstance(value, str):
        return value

    # Удаляем все суффиксы вида .буква.числа (например .v.05, .n.11)
    value = re.sub(r'\.[a-z]\.[0-9]+$', '', value)

    # Заменяем подчеркивания на пробелы
    value = value.replace('_', ' ')

    # Делаем первую букву заглавной (если это не аббревиатура)
    if value.isupper():
        return value
    return value.capitalize()