from django import template

from .permissions import is_manager

register = template.Library()

@register.filter(name='is_manager')
def is_manager_filter(user):
    return is_manager(user)
