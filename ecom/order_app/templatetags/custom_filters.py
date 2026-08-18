from django import template

register = template.Library()


@register.filter
def subtotal(item):
    return item.price * item.quantity
