from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import EmptyPage, Paginator

from oml.models import ModeratedModel, STATUS_PENDING

register = template.Library()

ITEMS_PER_PAGE = 50


@register.inclusion_tag('admin/oml/pending_content.html')
def get_content_for_approval(request):
    subclasses = [x for x in ModeratedModel.__subclasses__() if not x._meta.abstract]

    ct_filter_menu = sorted(
        (x._meta.model_name, x._meta.verbose_name.capitalize()) for x in subclasses
    )

    ct_filter = request.GET.get('ct_filter')
    page = max(int(request.GET.get('page', 1)), 1)

    if ct_filter:
        subclasses = [x for x in subclasses if x._meta.model_name == ct_filter]

    pending_items = []
    for klass in subclasses:
        ct_id = ContentType.objects.get_for_model(klass, for_concrete_model=False).pk
        model_name = klass._meta.verbose_name.capitalize()
        for item in klass.objects.filter(status=STATUS_PENDING):
            item.content_type_id = ct_id
            item.model_name = model_name
            pending_items.append(item)

    paginator = Paginator(pending_items, ITEMS_PER_PAGE)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages) if paginator.num_pages else paginator.page(1)

    return {
        'page_obj': page_obj,
        'ct_filter': ct_filter,
        'ct_filter_menu': ct_filter_menu,
        'request': request,
    }


@register.simple_tag
def pag_url(request, page_number):
    params = request.GET.copy()
    params['page'] = page_number
    return '?' + params.urlencode()
