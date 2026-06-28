django-oml
==========

|ci| |coverage|

.. |ci| image:: https://github.com/angvp/django-oml/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/angvp/django-oml/actions/workflows/ci.yml
   :alt: CI

.. |coverage| image:: https://codecov.io/gh/angvp/django-oml/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/angvp/django-oml
   :alt: Coverage

OML means Object Moderation Layer — a mixin model that lets you add content
moderation (pending / accepted / rejected states) to any Django model.

Installation
------------

::

    pip install django-oml

Add ``'oml'`` to ``INSTALLED_APPS`` and run ``migrate``.

Configuration
-------------

Add an ``OML_CONFIG`` dictionary to your Django settings::

    OML_CONFIG = {
        # Set True to let certain groups bypass moderation
        'OML_EXCLUDE_MODERATED': True,

        # List of group IDs that skip the moderation queue
        'OML_EXCLUDED_GROUPS': [],
    }

Usage
-----

Inherit from ``ModeratedModel``::

    from oml.models import ModeratedModel

    class Article(ModeratedModel):
        title = models.CharField(max_length=200)

The model gains:

- ``status`` field (``'p'`` pending / ``'a'`` accepted / ``'r'`` rejected)
- ``authorized_by`` FK to the user who last moderated the object
- ``status_date`` DateTimeField of the last moderation action
- ``.objects.accepted()``, ``.pending()``, ``.rejected()`` queryset shortcuts
- ``.accept(user)`` and ``.reject(user)`` methods

Admin integration
-----------------

Use ``ModelAdminOml`` to get moderation features out of the box::

    from oml.models import ModelAdminOml

    @admin.register(Article)
    class ArticleAdmin(ModelAdminOml):
        pass

This gives you automatically:

- ``status``, ``authorized_by``, and ``status_date`` columns in the changelist
- A **Status** filter in the sidebar
- **Accept selected** and **Reject selected** bulk actions

.. note::
   ``reject`` on a pending object with no prior accepted state will delete the
   object. The bulk action shows a warning with the count of deleted objects.

Moderation panel
----------------

A cross-model panel that lists all pending items across every ``ModeratedModel``
subclass in your project.

1. Include the OML URLs in your project's ``urls.py``::

       from django.urls import include, path

       urlpatterns = [
           ...
           path('admin/oml/', include('oml.urls')),
       ]

2. Visit ``/admin/oml/moderation/``. The panel is restricted to staff users.

The panel supports:

- Filtering by content type via ``?ct_filter=<model_name>``
- Per-item **Approve** / **Edit** / **Reject** actions
- Bulk approve via checkbox selection
- Pagination (50 items per page)

Template tag
~~~~~~~~~~~~

The panel is rendered via an inclusion tag you can embed in your own templates::

    {% load oml_tags %}
    {% get_content_for_approval request %}

This renders ``admin/oml/pending_content.html``, which you can override in your
project's template directory.

Running the tests
-----------------

::

    pip install pytest pytest-django
    pytest

Compatibility
-------------

- Python 3.10, 3.11, 3.12, 3.13, 3.14
- Django 4.2 (LTS), 5.1, 5.2 (LTS), 6.0

Why did we revamp this?
-----------------------

The original django-oml was written in 2013 and last released in 2015.
It was archived on GitHub in 2023 with no forks and no active successors.

The codebase still worked conceptually, but it had accumulated a decade of
bit-rot: Python 2-only idioms (``ugettext_lazy``, ``__unicode__``,
``MIDDLEWARE_CLASSES``), missing ``on_delete`` arguments that Django 2.0
made mandatory, a silent bug in the group-exclusion logic that made the
feature completely non-functional, and a test suite built on abandoned tools
(``nose``, ``django-nose``). None of it would import cleanly on a modern
Django project.

Rather than throw it away and start over — or accept that content moderation
simply has no maintained, lightweight option in the Django ecosystem — we
chose to modernize it in place. The logic was sound; it just needed to catch
up with ten years of Django evolution.

Alternatives
------------

These are the other packages that cover similar ground.
We looked at all of them before deciding to revamp django-oml.

+----------------------------------+----------------------+------------------+
| Package                          | Last release         | Status           |
+==================================+======================+==================+
| ``django-moderation``            | April 2022           | Unmaintained.    |
|                                  |                      | Supports up to   |
|                                  |                      | Django 3.2.      |
+----------------------------------+----------------------+------------------+
| ``django-moderation-model-mixin``| November 2021        | Unmaintained.    |
|                                  |                      | No Django 4+     |
|                                  |                      | support.         |
+----------------------------------+----------------------+------------------+
| ``django-gatekeeper``            | 2009                 | Abandoned.       |
+----------------------------------+----------------------+------------------+

As of June 2026, no actively maintained package provides a simple mixin-based
moderation layer compatible with Django 4.2+. django-oml 0.1.0 fills that gap.
Django 6.1 support will be added once it reaches a stable release.
