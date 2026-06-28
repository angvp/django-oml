from unittest.mock import MagicMock, patch

import pytest
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import RequestFactory

from .models import (
    STATUS_ACCEPTED,
    STATUS_PENDING,
    STATUS_REJECTED,
    LogModeratedModel,
    ModelAdminOml,
    ModeratedModel,
    StatusListFilter,
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
def staff_user(db, groups):
    return User.objects.create(username="staff", password="staff",
                               email="staff@example.com", is_staff=True,
                               is_active=True)


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
        LogModeratedModel.objects.create(
            content_type=ct, object_id=item.id, object_dump="[]")
        LogModeratedModel.objects.create(
            content_type=ct, object_id=item.id, object_dump="[]")
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
@pytest.mark.urls('oml.test_urls')
class TestModerationViews:
    def _post(self, staff_user, data=None):
        request = RequestFactory().post('/', data or {})
        request.user = staff_user
        return request

    def _get(self, user):
        request = RequestFactory().get('/')
        request.user = user
        return request

    def test_approve_accepts_item_and_redirects(self, make_item, staff_user):
        from oml.views import approve
        item = make_item()
        ct = ContentType.objects.get_for_model(ItemModel)
        response = approve(self._post(staff_user), item.pk, ct.pk)
        assert response.status_code == 302
        item.refresh_from_db()
        assert item.status == STATUS_ACCEPTED

    def test_approve_redirects_to_panel(self, make_item, staff_user):
        from oml.views import approve
        item = make_item()
        ct = ContentType.objects.get_for_model(ItemModel)
        response = approve(self._post(staff_user), item.pk, ct.pk)
        assert '/oml/moderation/' in response['Location']

    def test_reject_view_rejects_pending_no_log(self, make_item, staff_user):
        from oml.views import reject_view
        item = make_item()
        ct = ContentType.objects.get_for_model(ItemModel)
        response = reject_view(self._post(staff_user), item.pk, ct.pk)
        assert response.status_code == 302
        assert ItemModel.objects.count() == 0

    def test_reject_view_redirects_to_panel(self, make_item, staff_user):
        from oml.views import reject_view
        item = make_item()
        ct = ContentType.objects.get_for_model(ItemModel)
        response = reject_view(self._post(staff_user), item.pk, ct.pk)
        assert '/oml/moderation/' in response['Location']

    def test_approve_bulk_accepts_multiple_items(self, make_item, staff_user):
        from oml.views import approve_bulk
        items = [make_item() for _ in range(3)]
        ct = ContentType.objects.get_for_model(ItemModel)
        data = {'items': [f'{item.pk}@{ct.pk}' for item in items]}
        response = approve_bulk(self._post(staff_user, data), )
        assert response.status_code == 302
        assert ItemModel.objects.accepted().count() == 3

    def test_approve_bulk_skips_malformed_entries(self, make_item, staff_user):
        from oml.views import approve_bulk
        data = {'items': ['bad-entry', 'also-bad']}
        response = approve_bulk(self._post(staff_user, data))
        assert response.status_code == 302

    def test_approve_bulk_skips_nonexistent_ctype(self, make_item, staff_user):
        from oml.views import approve_bulk
        data = {'items': ['1@99999']}
        response = approve_bulk(self._post(staff_user, data))
        assert response.status_code == 302

    def test_moderation_panel_renders_correct_template(self, staff_user):
        from django.http import HttpResponse

        from oml.views import moderation_panel
        with patch('oml.views.render', return_value=HttpResponse()) as mock_render:
            moderation_panel(self._get(staff_user))
        mock_render.assert_called_once_with(
            mock_render.call_args[0][0], 'admin/oml/moderation_panel.html'
        )

    def test_non_staff_redirected_to_login(self, user):
        from oml.views import moderation_panel
        response = moderation_panel(self._get(user))
        assert response.status_code == 302
        assert 'login' in response['Location']


@pytest.mark.django_db
class TestOmlTemplateTags:
    def test_returns_only_pending_items(self, make_item):
        from oml.templatetags.oml_tags import get_content_for_approval
        make_item(status=STATUS_PENDING)
        make_item(status=STATUS_PENDING)
        make_item(status=STATUS_ACCEPTED)
        result = get_content_for_approval(RequestFactory().get('/'))
        assert result['page_obj'].paginator.count == 2

    def test_ct_filter_narrows_to_matching_model(self, make_item):
        from oml.templatetags.oml_tags import get_content_for_approval
        make_item(status=STATUS_PENDING)
        result = get_content_for_approval(
            RequestFactory().get('/', {'ct_filter': 'itemmodel'})
        )
        assert result['page_obj'].paginator.count == 1

    def test_unknown_ct_filter_returns_empty(self, make_item):
        from oml.templatetags.oml_tags import get_content_for_approval
        make_item(status=STATUS_PENDING)
        result = get_content_for_approval(
            RequestFactory().get('/', {'ct_filter': 'nonexistent'})
        )
        assert result['page_obj'].paginator.count == 0

    def test_items_have_content_type_id_set(self, make_item):
        from oml.templatetags.oml_tags import get_content_for_approval
        make_item(status=STATUS_PENDING)
        result = get_content_for_approval(RequestFactory().get('/'))
        item = result['page_obj'].object_list[0]
        assert hasattr(item, 'content_type_id')
        assert item.content_type_id is not None

    def test_items_have_model_name_set(self, make_item):
        from oml.templatetags.oml_tags import get_content_for_approval
        make_item(status=STATUS_PENDING)
        result = get_content_for_approval(RequestFactory().get('/'))
        item = result['page_obj'].object_list[0]
        assert item.model_name == 'Item model'

    def test_ct_filter_menu_includes_registered_models(self, db):
        from oml.templatetags.oml_tags import get_content_for_approval
        result = get_content_for_approval(RequestFactory().get('/'))
        menu_names = [name for name, _ in result['ct_filter_menu']]
        assert 'itemmodel' in menu_names

    def test_pag_url_appends_page_and_preserves_params(self, db):
        from oml.templatetags.oml_tags import pag_url
        request = RequestFactory().get('/', {'ct_filter': 'itemmodel'})
        url = pag_url(request, 3)
        assert 'page=3' in url
        assert 'ct_filter=itemmodel' in url

    def test_no_pending_returns_empty_page(self, db):
        from oml.templatetags.oml_tags import get_content_for_approval
        result = get_content_for_approval(RequestFactory().get('/'))
        assert result['page_obj'].paginator.count == 0


@pytest.mark.django_db
class TestStatusListFilter:
    def _make_filter(self, value=None):
        site = AdminSite()
        model_admin = ModelAdminOml(ItemModel, site)
        request = RequestFactory().get('/', {'status': value} if value else {})
        params = {'status': value} if value else {}
        f = StatusListFilter(request, params, ItemModel, model_admin)
        return f

    def test_lookups_returns_all_statuses(self):
        f = self._make_filter()
        lookups = f.lookups(None, None)
        values = [v for v, _ in lookups]
        assert STATUS_PENDING in values
        assert STATUS_ACCEPTED in values
        assert STATUS_REJECTED in values

    def test_filter_by_pending(self, make_item):
        make_item(status=STATUS_PENDING)
        make_item(status=STATUS_ACCEPTED)
        f = self._make_filter(STATUS_PENDING)
        qs = f.queryset(None, ItemModel.objects.all())
        assert qs.count() == 1
        assert qs.first().status == STATUS_PENDING

    def test_filter_by_accepted(self, make_item):
        make_item(status=STATUS_PENDING)
        make_item(status=STATUS_ACCEPTED)
        f = self._make_filter(STATUS_ACCEPTED)
        qs = f.queryset(None, ItemModel.objects.all())
        assert qs.count() == 1
        assert qs.first().status == STATUS_ACCEPTED

    def test_filter_by_rejected(self, make_item):
        make_item(status=STATUS_REJECTED)
        make_item(status=STATUS_PENDING)
        f = self._make_filter(STATUS_REJECTED)
        qs = f.queryset(None, ItemModel.objects.all())
        assert qs.count() == 1
        assert qs.first().status == STATUS_REJECTED

    def test_no_filter_returns_full_queryset(self, make_item):
        make_item(status=STATUS_PENDING)
        make_item(status=STATUS_ACCEPTED)
        make_item(status=STATUS_REJECTED)
        f = self._make_filter()
        qs = f.queryset(None, ItemModel.objects.all())
        assert qs.count() == 3


@pytest.mark.django_db
class TestGetAdminUrl:
    def test_returns_url_when_model_registered(self, make_item):
        import sys

        from django.test.utils import override_settings

        site = AdminSite()
        site.register(ItemModel, ModelAdminOml)
        item = make_item()

        mod_name = 'oml._test_urls'
        mod = type(sys)('oml._test_urls')
        from django.urls import path
        mod.urlpatterns = [path('admin/', site.urls)]
        sys.modules[mod_name] = mod

        with override_settings(ROOT_URLCONF=mod_name):
            url = item.get_admin_url()

        del sys.modules[mod_name]
        assert url == f'/admin/oml/itemmodel/{item.pk}/change/'

    def test_returns_empty_string_when_no_reverse_match(self, make_item):
        from django.urls import NoReverseMatch
        item = make_item()
        with patch('django.urls.reverse', side_effect=NoReverseMatch):
            url = item.get_admin_url()
        assert url == ''


@pytest.mark.django_db
class TestBulkActions:
    def _make_admin(self):
        return ModelAdminOml(ItemModel, AdminSite())

    def _request(self, user):
        request = RequestFactory().post('/')
        request.user = user
        return request

    def test_accept_selected_transitions_pending_to_accepted(self, make_item, user):
        items = [make_item() for _ in range(3)]
        qs = ItemModel.objects.filter(pk__in=[i.pk for i in items])
        self._make_admin().accept_selected(self._request(user), qs)
        assert ItemModel.objects.accepted().count() == 3

    def test_accept_selected_skips_already_accepted(self, make_item, user):
        make_item(status=STATUS_ACCEPTED)
        make_item(status=STATUS_ACCEPTED)
        qs = ItemModel.objects.all()
        self._make_admin().accept_selected(self._request(user), qs)
        assert ItemModel.objects.accepted().count() == 2
        assert ItemModel.objects.count() == 2

    def test_reject_selected_no_log_deletes_objects(self, make_item, user):
        items = [make_item() for _ in range(2)]
        qs = ItemModel.objects.filter(pk__in=[i.pk for i in items])
        model_admin = self._make_admin()
        with patch.object(model_admin, 'message_user') as mock_msg:
            model_admin.reject_selected(self._request(user), qs)
        assert ItemModel.objects.count() == 0
        mock_msg.assert_called_once()
        _, kwargs = mock_msg.call_args
        assert kwargs['level'] == messages.WARNING

    def test_reject_selected_warning_count_matches_deleted(self, make_item, user):
        items = [make_item() for _ in range(3)]
        qs = ItemModel.objects.filter(pk__in=[i.pk for i in items])
        model_admin = self._make_admin()
        with patch.object(model_admin, 'message_user') as mock_msg:
            model_admin.reject_selected(self._request(user), qs)
        msg_text = mock_msg.call_args[0][1]
        assert '3' in msg_text

    def test_reject_selected_with_log_reverts_object(self, make_item, user):
        item = make_item()
        item.accept(user)
        item.test_field = 'changed'
        item.save_form_log_moderated()
        item.define_status_of_object(user)
        item.save()

        qs = ItemModel.objects.filter(pk=item.pk)
        model_admin = self._make_admin()
        with patch.object(model_admin, 'message_user') as mock_msg:
            model_admin.reject_selected(self._request(user), qs)

        mock_msg.assert_not_called()
        reverted = ItemModel.objects.get(pk=item.pk)
        assert reverted.test_field == 'basic content'
        assert reverted.status == STATUS_ACCEPTED

    def test_reject_selected_already_accepted_no_warning(self, make_item, user):
        make_item(status=STATUS_ACCEPTED)
        qs = ItemModel.objects.all()
        model_admin = self._make_admin()
        with patch.object(model_admin, 'message_user') as mock_msg:
            model_admin.reject_selected(self._request(user), qs)
        mock_msg.assert_not_called()
        assert ItemModel.objects.count() == 1

    def test_actions_registered_on_model_admin(self):
        model_admin = self._make_admin()
        assert 'accept_selected' in model_admin.actions
        assert 'reject_selected' in model_admin.actions


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

    def test_list_display_includes_status_fields(self):
        site = AdminSite()
        model_admin = ModelAdminOml(ItemModel, site)
        assert 'status' in model_admin.list_display
        assert 'authorized_by' in model_admin.list_display
        assert 'status_date' in model_admin.list_display

    def test_list_filter_includes_status_filter(self):
        site = AdminSite()
        model_admin = ModelAdminOml(ItemModel, site)
        assert StatusListFilter in model_admin.list_filter

    def test_readonly_fields_includes_status_fields(self):
        site = AdminSite()
        model_admin = ModelAdminOml(ItemModel, site)
        assert 'status' in model_admin.readonly_fields
        assert 'authorized_by' in model_admin.readonly_fields
        assert 'status_date' in model_admin.readonly_fields

    def test_conventional_import_from_oml_admin(self):
        from oml.admin import ModelAdminOml as AdminOml
        from oml.admin import StatusListFilter as AdminFilter
        assert AdminOml is ModelAdminOml
        assert AdminFilter is StatusListFilter
