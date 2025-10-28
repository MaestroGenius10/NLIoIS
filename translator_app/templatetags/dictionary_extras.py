from django.template import Library

register = Library()


@register.filter(name='get')
def get(dictionary, key):
    """
    Позволяет получить значение из словаря по ключу-переменной.
    Использование в шаблоне: {{ my_dictionary|get:my_key }}
    """
    return dictionary.get(key)