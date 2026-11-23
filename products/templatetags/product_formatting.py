from django import template


register = template.Library()


@register.filter
def dict_value(value, key):
    """Read an optional content key without invoking dictionary methods."""
    return value.get(key) if isinstance(value, dict) else None


@register.filter
def format_size_label(value):
    """Format ranking size keys such as 24_28 as '24 + 28'."""
    return " + ".join(str(value).split("_"))