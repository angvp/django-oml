from django.db import models
from django.utils.translation import ugettext_lazy as _

from .managers import ModeratedModelManager

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User

STATUS_ACCEPTED = 'a'
STATUS_PENDING = 'p'
STATUS_REJECTED = 'r'
STATUS_CHOICES = (
    (STATUS_PENDING, _('Pending')),
    (STATUS_ACCEPTED, _('Accepted')),
    (STATUS_REJECTED, _('Rejected')),
)


class ModeratedModel(models.Model):
    authorized_by = models.ForeignKey(User, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approval_date = models.DateTimeField(null=True, blank=True)
    objects = ModeratedModelManager()
