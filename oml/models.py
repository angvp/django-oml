from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from managers import ModeratedModelManager

USER_MODEL = getattr(settings, 'USER_MODEL', None) or \
             getattr(settings, 'AUTH_USER_MODEL', None) or \
             'auth.User'

STATUS_ACCEPTED = 'a'
STATUS_PENDING = 'p'
STATUS_REJECTED = 'r'
STATUS_CHOICES = (
    (STATUS_PENDING, _('Pending')),
    (STATUS_ACCEPTED, _('Accepted')),
    (STATUS_REJECTED, _('Rejected')),
)


class ModeratedModel(models.Model):
    authorized_by = models.ForeignKey(USER_MODEL, null=True, blank=True,
            editable=False)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_PENDING, editable=False)
    status_date = models.DateTimeField(null=True, blank=True, editable=False)
    objects = ModeratedModelManager()

    class Meta:
        abstract = True
