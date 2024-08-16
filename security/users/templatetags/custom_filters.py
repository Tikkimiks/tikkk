from django import template

register = template.Library()

@register.filter(name='reverse')
def reverse_list(value):
    return value[::-1]
