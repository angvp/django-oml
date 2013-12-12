django-oml
========================

.. image:: https://travis-ci.org/RouteAtlas/django-oml.png?branch=master
    :target: https://travis-ci.org/RouteAtlas/django-oml

Welcome to the documentation for django-oml!

OML means Object Moderation Layer, the idea is to have a mixin model that
allows you to moderate several kinds of content.

On config set up a dictionary ::

	OML_CONFIG = {

		# True if some groups wont be moderated
		'OML_EXCLUDE_MODERATED': True/False,

                # List of groups id that will be omitted
		'OML_EXCLUDED_GROUPS': []

	}

This is still a project in development

Running the Tests
------------------------------------

You can run the tests with via::

    python setup.py test

or::

    python runtests.py
