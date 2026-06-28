Changelog
=========

0.1.0 (2026-06-27)
-------------------

This release modernizes the package to support Django 4.2 through 6.1 and
drops all Python 2 / Django < 4.2 support.

**Breaking changes**

- Dropped support for Python 2, Python 3.4–3.9, and Django < 4.2.
- ``LogModeratedModel.object_id`` changed from ``IntegerField`` to
  ``BigIntegerField`` to handle ``BigAutoField`` primary keys (Django 6.0
  default). Existing installations must run ``migrate`` after upgrading.
- ``setup.py`` replaced by ``pyproject.toml`` (PEP 517/518).

**Bug fixes**

- Fixed ``define_status_of_object``: was referencing the non-existent
  ``user.group`` attribute instead of the M2M ``user.groups`` relation, so
  the group-exclusion feature never worked. Now uses
  ``user.groups.filter(id__in=OML_EXCLUDED_GROUPS).exists()``.
- Added required ``on_delete`` argument to both ``ForeignKey`` fields
  (``LogModeratedModel.content_type`` → ``CASCADE``,
  ``ModeratedModel.authorized_by`` → ``SET_NULL``).

**Compatibility fixes**

- Replaced ``ugettext_lazy`` (removed in Django 4.0) with ``gettext_lazy``.
- Replaced ``MIDDLEWARE_CLASSES`` (removed in Django 2.0) with ``MIDDLEWARE``
  in the test settings.
- Removed Python 2 ``__unicode__`` methods; replaced with ``__str__``.
- Removed dead ``try/except ImportError`` fallback for ``django.utils.timezone``
  (available since Django 1.4).

**Test suite**

- Migrated from ``unittest.TestCase`` + ``nose``/``django-nose`` to
  ``pytest`` + ``pytest-django``.
- Added ``oml/test_settings.py`` for standalone pytest runs.
- Added tests for previously uncovered paths: ``MultipleObjectsReturned``
  in ``reject()``, group-exclusion in ``define_status_of_object()``,
  ``__str__`` on both models, and ``ModelAdminOml.save_form()``.
- ``models.py`` coverage raised from 90 % to 100 %.

**Packaging**

- Added ``oml/migrations/`` with initial migration for ``LogModeratedModel``.
- ``tox.ini`` updated to test Python 3.10–3.12 against Django 4.2, 5.1,
  5.2, 6.0, and 6.1.


0.0.3 (2015-01-01)
-------------------

- Last release with Python 2 / Django 1.5–1.8 support.
