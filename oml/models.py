from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import ModeratedModelManager

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

OML_CONFIG = getattr(settings, 'OML_CONFIG', None)
OML_EXCLUDE_MODERATED = OML_CONFIG['OML_EXCLUDE_MODERATED']
OML_EXCLUDED_GROUPS = OML_CONFIG['OML_EXCLUDED_GROUPS']


class LogModeratedModel(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.BigIntegerField(db_index=True)
    object_dump = models.TextField()

    def __str__(self):
        return f"{self.content_type} #{self.object_id}"


class ModeratedModel(models.Model):
    authorized_by = models.ForeignKey(USER_MODEL, null=True, blank=True,
                                      editable=False, on_delete=models.SET_NULL)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default=STATUS_PENDING, editable=False,
                              db_index=True)
    status_date = models.DateTimeField(null=True, blank=True, editable=False)
    objects = ModeratedModelManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    def accept(self, user):
        """Set status accepted to the current item
        :param user: user who is approving the content
        """

        if self.status == STATUS_ACCEPTED:
            return

        # Search in moderated logs
        logs = LogModeratedModel.objects.filter(
            content_type=ContentType.objects.get_for_model(type(self)),
            object_id=self.id)
        # Delete the log if exists
        if logs:
            logs[0].delete()

        self.status = STATUS_ACCEPTED
        self.authorized_by = user
        self.status_date = timezone.now()
        self.save()

    def reject(self, user):
        """Set status rejected to the current item
        :param user: user who is approving the content
        """
        logs = []

        if not self.status == STATUS_PENDING:
            # Rejected=True & Deleted=False
            return (False, False)

        # Search in moderated logs
        try:
            logs = LogModeratedModel.objects.get(
                content_type=ContentType.objects.get_for_model(type(self)),
                object_id=self.id)
        except LogModeratedModel.MultipleObjectsReturned:
            return False
        except LogModeratedModel.DoesNotExist:
            pass

        if logs:
            # Replace with the last accepted
            # object and delete the log
            for obj_original in serializers.deserialize('json',
                                                        logs.object_dump):
                obj_original.save()
                logs.delete()
            # Rejected=True & Deleted=False
            return (True, False)
        # If there is no logs, then we
        # reject the creation of the object
        self.status = STATUS_REJECTED
        self.authorized_by = user
        self.status_date = timezone.now()
        self.save()
        self.delete()
        # Rejected=True & Deleted=True
        return (True, True)

    def save_form_log_moderated(self):
        if self.status == STATUS_ACCEPTED:
            # store the log of the moderated model
            content_type = ContentType.objects.get_for_model(
                self, for_concrete_model=False)
            # Save the original object in LogModeratedModel
            obj_data = serializers.serialize(
                'json', [content_type.get_object_for_this_type(id=self.id)])
            log = {
                'content_type': content_type,
                'object_id': self.id,
                'object_dump': obj_data,
            }
            LogModeratedModel.objects.create(**log)

    def define_status_of_object(self, user):
        self.status = STATUS_PENDING
        if OML_EXCLUDE_MODERATED and user.groups.filter(
                id__in=OML_EXCLUDED_GROUPS).exists():
            self.status = STATUS_ACCEPTED

    class Meta:
        abstract = True


class ModelAdminOml(admin.ModelAdmin):
    """
    Extension of ModelAdmin
    """

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """

        # Save the original object in LogModeratedModel

        # Store the object on the DB
        form = super(ModelAdminOml, self).save_form(request, form, change)

        # Store the log of the moderated model
        form.save_form_log_moderated()
        # Change status if necesary
        form.define_status_of_object(request.user)

        return form
