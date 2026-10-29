from django import template
# Импортируем функцию проверки из нашего mixins.py
from .mixins import is_manager as check_is_manager

register = template.Library()

@register.filter(name='is_manager')
def is_manager(user):
    """
    Фильтр для использования в шаблонах: {% if user|is_manager %}
    """
    if not user.is_authenticated:
        return False
    return check_is_manager(user)
