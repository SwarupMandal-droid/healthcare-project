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
        # If the item contains a comma and the key wasn't comma, split it so django can unpack it
        if ',' in item and key != ',':
            result.append(item.split(','))
        else:
            result.append(item)
    return result
