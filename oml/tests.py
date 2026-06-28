import pytest
from unittest.mock import MagicMock, patch
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import RequestFactory

from .models import (
    LogModeratedModel,
    ModelAdminOml,
    ModeratedModel,
    STATUS_ACCEPTED,
    STATUS_PENDING,
    STATUS_REJECTED,
)


class ItemModel(ModeratedModel):
    test_field = models.CharField(max_length=200)

    class Meta:
        app_label = 'oml'

    def __str__(self):
        return f"{self.id} - {self.test_field}"


@pytest.fixture
def groups(db):
    non_moderated = Group.objects.create(id=1, name='non_moderated')
    moderated = Group.objects.create(id=2, name='moderated')
    return [non_moderated, moderated]


@pytest.fixture
def user(db, groups):
    return User.objects.create(username="moderator", password="moderator",
                               email="moderator@example.com")


@pytest.fixture
def excluded_user(db, groups):
    u = User.objects.create(username="exempt", password="exempt",
                            email="exempt@example.com")
    u.groups.add(groups[0])  # group id=1 is in OML_EXCLUDED_GROUPS
    return u


@pytest.fixture
def make_item(db):
    def _create(content="basic content", status=STATUS_PENDING):
        return ItemModel.objects.create(test_field=content, status=status)
    return _create


@pytest.mark.django_db
class TestManagerQuerysets:
    def test_pending(self, make_item):
        item = make_item(content="pending item")
        assert item.status == STATUS_PENDING
        assert ItemModel.objects.pending().count() == 1
        assert ItemModel.objects.accepted().count() == 0
        assert ItemModel.objects.rejected().count() == 0

    def test_accepted(self, make_item):
        make_item(status=STATUS_ACCEPTED, content="accepted item")
        assert ItemModel.objects.accepted().count() == 1
        assert ItemModel.objects.pending().count() == 0
        assert ItemModel.objects.rejected().count() == 0

    def test_rejected(self, make_item):
        make_item(status=STATUS_REJECTED, content="rejected item")
        assert ItemModel.objects.rejected().count() == 1
        assert ItemModel.objects.accepted().count() == 0
        assert ItemModel.objects.pending().count() == 0

    def test_mixed_counts(self, make_item):
        for _ in range(3):
            make_item(status=STATUS_REJECTED)
        for _ in range(2):
            make_item(status=STATUS_PENDING)
        make_item(status=STATUS_ACCEPTED)
        assert ItemModel.objects.rejected().count() == 3
        assert ItemModel.objects.pending().count() == 2
        assert ItemModel.objects.accepted().count() == 1
        assert ItemModel.objects.count() == 6


@pytest.mark.django_db
class TestAccept:
    def test_accept_already_accepted_is_noop(self, make_item, user):
        item = make_item(status=STATUS_ACCEPTED)
        item.accept(user)
        assert item.status == STATUS_ACCEPTED
        assert LogModeratedModel.objects.count() == 0

    def test_accept_pending(self, make_item, user):
        item = make_item()
        item.accept(user)
        assert item.status == STATUS_ACCEPTED
        assert LogModeratedModel.objects.count() == 0

    def test_accept_clears_log(self, make_item, user):
        item = make_item()
        item.accept(user)
        item.test_field = 'changed'
        item.save_form_log_moderated()
        item.define_status_of_object(user)
        assert item.status == STATUS_PENDING
        assert LogModeratedModel.objects.count() == 1

        item.accept(user)
        assert item.status == STATUS_ACCEPTED
        assert LogModeratedModel.objects.count() == 0

    def test_accept_rejected(self, make_item, user):
        item = make_item(status=STATUS_REJECTED)
        item.accept(user)
        assert item.status == STATUS_ACCEPTED


@pytest.mark.django_db
class TestReject:
    def test_reject_accepted_returns_false_tuple(self, make_item, user):
        item = make_item(status=STATUS_ACCEPTED)
        result = item.reject(user)
        assert result == (False, False)
        assert item.status == STATUS_ACCEPTED

    def test_reject_rejected_returns_false_tuple(self, make_item, user):
        item = make_item(status=STATUS_REJECTED)
        result = item.reject(user)
        assert result == (False, False)

    def test_reject_pending_no_log_deletes_object(self, make_item, user):
        item = make_item()
        result = item.reject(user)
        assert result == (True, True)
        assert ItemModel.objects.count() == 0

    def test_reject_pending_with_log_reverts_object(self, make_item, user):
        item = make_item()
        item.accept(user)
        item.test_field = 'changed field'
        item.save_form_log_moderated()
        item.define_status_of_object(user)
        assert LogModeratedModel.objects.count() == 1

        result = item.reject(user)
        assert result == (True, False)
        item_refreshed = ItemModel.objects.get(id=item.id)
        assert item_refreshed.status == STATUS_ACCEPTED
        assert item_refreshed.test_field == 'basic content'
        assert LogModeratedModel.objects.count() == 0

    def test_reject_multiple_logs_returns_false(self, make_item, user):
        item = make_item()
        item.accept(user)
        ct = ContentType.objects.get_for_model(ItemModel)
        LogModeratedModel.objects.create(content_type=ct, object_id=item.id, object_dump='[]')
        LogModeratedModel.objects.create(content_type=ct, object_id=item.id, object_dump='[]')
        item.status = STATUS_PENDING
        result = item.reject(user)
        assert result is False


@pytest.mark.django_db
class TestDefineStatus:
    def test_regular_user_stays_pending(self, make_item, user):
        item = make_item(status=STATUS_ACCEPTED)
        item.define_status_of_object(user)
        assert item.status == STATUS_PENDING

    def test_excluded_group_user_becomes_accepted(self, make_item, excluded_user):
        item = make_item()
        item.define_status_of_object(excluded_user)
        assert item.status == STATUS_ACCEPTED


@pytest.mark.django_db
class TestLogTracking:
    def test_log_count_across_operations(self, make_item, user):
        item_a = make_item(status=STATUS_ACCEPTED)
        item_p = make_item(status=STATUS_PENDING)
        assert LogModeratedModel.objects.count() == 0

        item_p.accept(user)
        item_p.test_field = 'edit 1'
        item_p.save_form_log_moderated()
        item_p.define_status_of_object(user)
        assert LogModeratedModel.objects.count() == 1

        # Second edit replaces the existing log
        item_p.test_field = 'edit 2'
        item_p.save_form_log_moderated()
        item_p.define_status_of_object(user)
        assert LogModeratedModel.objects.count() == 1

        item_a.test_field = 'edit a'
        item_a.save_form_log_moderated()
        item_a.define_status_of_object(user)
        assert LogModeratedModel.objects.count() == 2

        item_a.accept(user)
        assert LogModeratedModel.objects.count() == 1

        item_p.accept(user)
        assert LogModeratedModel.objects.count() == 0


@pytest.mark.django_db
class TestStrMethods:
    def test_log_moderated_model_str(self, make_item):
        item = make_item(status=STATUS_ACCEPTED)
        ct = ContentType.objects.get_for_model(ItemModel)
        log = LogModeratedModel.objects.create(
            content_type=ct, object_id=item.id, object_dump='[]'
        )
        assert str(log) == f"{ct} #{item.id}"

    def test_moderated_model_str(self, make_item):
        item = make_item()
        assert ModeratedModel.__str__(item) == f"ItemModel #{item.pk}"


@pytest.mark.django_db
class TestModelAdminOml:
    def test_save_form_calls_log_and_define_status(self, user):
        site = AdminSite()
        model_admin = ModelAdminOml(ItemModel, site)
        request = RequestFactory().get('/')
        request.user = user

        mock_form = MagicMock()
        mock_form.save_form_log_moderated = MagicMock()
        mock_form.define_status_of_object = MagicMock()

        with patch('django.contrib.admin.ModelAdmin.save_form', return_value=mock_form):
            result = model_admin.save_form(request, mock_form, change=False)

        mock_form.save_form_log_moderated.assert_called_once()
        mock_form.define_status_of_object.assert_called_once_with(user)
        assert result is mock_form
