# Changelog

## 0.1.3 (2026-06-28)

**New feature**

- Added `reject_bulk` view and `reject/bulk/` URL — the moderation panel
  now has a **Reject selected** bulk action alongside **Approve selected**.

## 0.1.2 (2026-06-28)

**Bug fix**

- Fixed packaging: templates and templatetags were not included in the wheel,
  causing `TemplateDoesNotExist` errors when using the moderation panel from
  a PyPI install. Added `[tool.setuptools.package-data]` to include
  `oml/templates/**/*`.

## 0.1.1 (2026-06-27)

**Admin enhancements**

- `ModelAdminOml` now includes `list_display`, `list_filter` (`StatusListFilter`),
  `readonly_fields`, and bulk accept/reject actions out of the box.
- New `StatusListFilter` — available standalone via `from oml.admin import StatusListFilter`.
- New `ModeratedModel.get_admin_url()` — returns the Django admin change URL
  for the object, or `''` if the model is not registered.
- New `oml/admin.py` for conventional Django import style
  (`from oml.admin import ModelAdminOml`).

**Moderation panel**

- New cross-model moderation panel at `/admin/oml/moderation/` listing all
  pending items across every `ModeratedModel` subclass. Requires
  `path('admin/oml/', include('oml.urls'))` in the project `urls.py`.
- New `{% load oml_tags %}` template library with `get_content_for_approval`
  inclusion tag and `pag_url` simple tag.

**Refactor**

- Removed `oml/managers.py`; manager logic inlined in `models.py` using
  `ModeratedModelQuerySet.as_manager()`. No behavioral change.

## 0.1.0 (2026-06-27)

This release modernizes the package to support Django 4.2 through 6.1 and
drops all Python 2 / Django < 4.2 support.

**Breaking changes**

- Dropped support for Python 2, Python 3.4–3.9, and Django < 4.2.
- `LogModeratedModel.object_id` changed from `IntegerField` to `BigIntegerField`
  to handle `BigAutoField` primary keys (Django 6.0 default). Existing
  installations must run `migrate` after upgrading.
- `setup.py` replaced by `pyproject.toml` (PEP 517/518).

**Bug fixes**

- Fixed `define_status_of_object`: was referencing the non-existent `user.group`
  attribute instead of the M2M `user.groups` relation, so the group-exclusion
  feature never worked. Now uses `user.groups.filter(id__in=OML_EXCLUDED_GROUPS).exists()`.
- Added required `on_delete` argument to both `ForeignKey` fields
  (`LogModeratedModel.content_type` → `CASCADE`, `ModeratedModel.authorized_by` → `SET_NULL`).

**Compatibility fixes**

- Replaced `ugettext_lazy` (removed in Django 4.0) with `gettext_lazy`.
- Replaced `MIDDLEWARE_CLASSES` (removed in Django 2.0) with `MIDDLEWARE` in the test settings.
- Removed Python 2 `__unicode__` methods; replaced with `__str__`.
- Removed dead `try/except ImportError` fallback for `django.utils.timezone`
  (available since Django 1.4).

**Test suite**

- Migrated from `unittest.TestCase` + `nose`/`django-nose` to `pytest` + `pytest-django`.
- Added `oml/test_settings.py` for standalone pytest runs.
- Added tests for previously uncovered paths: `MultipleObjectsReturned` in `reject()`,
  group-exclusion in `define_status_of_object()`, `__str__` on both models,
  and `ModelAdminOml.save_form()`.
- `models.py` coverage raised from 90% to 100%.

**Admin enhancements** (ported from the original backoffice panel)

- `ModelAdminOml` now ships with sensible defaults: `list_display`
  (status, authorized_by, status_date), `list_filter` (StatusListFilter),
  and `readonly_fields` for all moderation fields.
- New `StatusListFilter` — a reusable `SimpleListFilter` on the `status`
  field, available standalone via `from oml.admin import StatusListFilter`.
- New bulk admin actions on `ModelAdminOml`: **Accept selected** and
  **Reject selected**. Reject emits a `messages.WARNING` with the count of
  objects deleted (those with no prior accepted state to revert to).
- New `ModeratedModel.get_admin_url()` — returns the Django admin change URL
  for the object, or `''` if the model is not registered in the admin.
- New cross-model **moderation panel** at `/admin/oml/moderation/` listing all
  pending items across every `ModeratedModel` subclass. Supports per-item
  approve/edit/reject actions, bulk approve, content-type filtering, and pagination.
  Requires `path('admin/oml/', include('oml.urls'))` in the project `urls.py`.
- New `{% load oml_tags %}` template library with `get_content_for_approval`
  inclusion tag and `pag_url` simple tag.
- New `oml/admin.py` re-exporting `ModelAdminOml` and `StatusListFilter`
  for conventional Django import style (`from oml.admin import ModelAdminOml`).

**Packaging**

- Added `oml/migrations/` with initial migration for `LogModeratedModel`.
- `tox.ini` updated to test Python 3.10–3.14 against Django 4.2, 5.1, 5.2, and 6.0.

## 0.0.3 (2015-01-01)

- Last release with Python 2 / Django 1.5–1.8 support.
