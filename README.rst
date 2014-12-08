django-oml
========================

.. image:: https://travis-ci.org/RouteAtlas/django-oml.png?branch=master
    :target: https://travis-ci.org/RouteAtlas/django-oml
    
.. image:: https://coveralls.io/repos/RouteAtlas/django-oml/badge.png?branch=master
  :target: https://coveralls.io/r/RouteAtlas/django-oml?branch=master

.. image:: https://requires.io/github/RouteAtlas/django-oml/requirements.png?branch=master
   :target: https://requires.io/github/RouteAtlas/django-oml/requirements/?branch=master
   :alt: Requirements Status
   
.. image:: https://d2weczhvl823v0.cloudfront.net/RouteAtlas/django-oml/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free


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


This project plays well with the following Django versions:

- Django 1.5
- Django 1.6
- Django 1.7 (not with python 2.6)

With python 2.7 and python 2.6 (except for Django 1.7).
