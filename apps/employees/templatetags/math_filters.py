# apps/employees/templatetags/math_filters.py
from django import template

register = template.Library()

@register.filter(name='mul')
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='div')
def divide(value, arg):
    """Divide el valor por el argumento"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter(name='percentage')
def percentage(value, total):
    """Calcula el porcentaje de value respecto a total"""
    try:
        total = float(total)
        if total == 0:
            return 0
        return round((float(value) / total) * 100, 1)
    except (ValueError, TypeError):
        return 0