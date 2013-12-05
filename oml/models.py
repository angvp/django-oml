from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from managers import ModeratedModelManager

try:
    from django.utils import timezone
except ImportError:
    from datetime import datetime as timezone

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

    def accept(self, user):
        """Set status accepted to the current item
        :param user: user who is approving the content
        """
        self.status = STATUS_ACCEPTED
        self.authorized_by = user
        self.status_date = timezone.now()
        self.save()

    def reject(self, user):
        """Set status rejected to the current item
        :param user: user who is approving the content
        """
        self.status = STATUS_REJECTED
        self.authorized_by = user
        self.status_date = timezone.now()
        self.save()

    class Meta:
        abstract = True


class ModelAdminOml(admin.ModelAdmin):
    """
    Extension of ModelAdmin
    """
    
    def save_form(self, request, form, change, **kwargs):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        form = super(ModelAdminOml, self).save_form(request, form, change)

        if not request.user.group.id == 1:
            form.status = STATUS_PENDING
        form.authorized_by = request.user
        form.status_date = timezone.now()    
                
        return form