"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.db import models
#from django.contrib.auth.models import AnonymousUser

from .models import ModeratedModel, STATUS_ACCEPTED, STATUS_PENDING, STATUS_REJECTED
#from .managers import ModeratedModelManager


class TestModel(ModeratedModel):
    test_field = models.BooleanField()


class ModeratedModelTestCase(TestCase):

    def setUp(self):
        self.item = TestModel()

    def test_create_moderated_content(self):
        item = self.item
        item.test_field = True
        item.save()
        self.assertEquals(item.status, STATUS_PENDING)
