from django import template


register = template.Library()


@register.filter
def format_size_label(value):
    """Format ranking size keys such as 24_28 as '24 + 28'."""
    return " + ".join(str(value).split("_"))