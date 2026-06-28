from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

# Uses settings.LOGIN_URL so the package doesn't assume an admin namespace is mounted.
_staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)


@_staff_required
def moderation_panel(request):
    return render(request, 'admin/oml/moderation_panel.html')


@_staff_required
@require_POST
def approve(request, object_id, ctype_id):
    ctype = get_object_or_404(ContentType, pk=ctype_id)
    obj = get_object_or_404(ctype.model_class(), pk=object_id)
    obj.accept(request.user)
    return HttpResponseRedirect(reverse('oml:moderation_panel'))


@_staff_required
@require_POST
def reject_view(request, object_id, ctype_id):
    ctype = get_object_or_404(ContentType, pk=ctype_id)
    obj = get_object_or_404(ctype.model_class(), pk=object_id)
    obj.reject(request.user)
    return HttpResponseRedirect(reverse('oml:moderation_panel'))


@_staff_required
@require_POST
def approve_bulk(request):
    for entry in request.POST.getlist('items'):
        try:
            obj_id, ctype_id = entry.split('@', 1)
        except ValueError:
            continue
        try:
            ctype = ContentType.objects.get(pk=ctype_id)
        except ContentType.DoesNotExist:
            continue
        model_class = ctype.model_class()
        if model_class is None:
            continue
        try:
            obj = model_class.objects.get(pk=obj_id)
        except ObjectDoesNotExist:
            continue
        obj.accept(request.user)
    return HttpResponseRedirect(reverse('oml:moderation_panel'))
