from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_attr(obj, attr):
    """Get attribute from object"""
    if obj is None:
        return None
    return getattr(obj, attr, None)