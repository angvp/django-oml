django-oml
========================

.. image:: https://travis-ci.org/angvp/django-oml.png?branch=master
    :target: https://travis-ci.org/angvp/django-oml
    

.. image:: https://coveralls.io/repos/angvp/django-oml/badge.svg?branch=master
  :target: https://coveralls.io/r/angvp/django-oml?branch=master


.. image:: https://requires.io/github/angvp/django-oml/requirements.png?branch=master
   :target: https://requires.io/github/angvp/django-oml/requirements/?branch=master
   :alt: Requirements Status

.. image:: https://codeclimate.com/github/angvp/django-oml/badges/gpa.svg
   :target: https://codeclimate.com/github/angvp/django-oml
   :alt: Code Climate
   

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
- Django 1.7
- Django 1.8

With python 2.7 and > 3.3 support.
