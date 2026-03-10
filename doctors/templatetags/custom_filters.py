from django import template

register = template.Library()

@register.filter(name='split')
def split(value, key):
    """
    Returns the value turned into a list.
    If the split items contain commas, it further splits them to allow unpacking.
    """
    if not isinstance(value, str):
        return value

    items = value.split(key)
    result = []
    for item in items:
        if ',' in item and key != ',':
            result.append(item.split(','))
        else:
            result.append(item)
    return result


@register.filter(name='star_range')
def star_range(rating):
    """
    Given a numeric rating (0-5), returns a list of 5 booleans:
    True = filled star, False = empty star.
    Usage: {% for is_filled in doctor.rating|star_range %}
    """
    try:
        filled = round(float(rating))
    except (TypeError, ValueError):
        filled = 0
    filled = max(0, min(5, filled))
    return [i < filled for i in range(5)]


@register.filter(name='to_int')
def to_int(value):
    """Convert a value to int safely."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
