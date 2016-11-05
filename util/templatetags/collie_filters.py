from django import template
from django.template.defaultfilters import stringfilter
from urllib import unquote

register = template.Library()


@register.filter(name='unquote_raw')
@stringfilter
def unquote_raw(value):
    return unquote(value)