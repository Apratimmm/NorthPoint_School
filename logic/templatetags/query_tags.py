from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def set_query(context, key, value):
    request = context.get("request")
    if request is None:
        return ""
    query = request.GET.copy()
    query[key] = value
    return query.urlencode()
