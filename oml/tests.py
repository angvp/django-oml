# -*- coding: utf-8 -*-
"""
django-oml tests
"""

from .models import (ModeratedModel, STATUS_ACCEPTED, STATUS_PENDING,
                     STATUS_REJECTED)
from django.db import models
from django.test import TestCase


class TestModel(ModeratedModel):
    test_field = models.CharField(max_length=200)


class ModeratedModelTestCase(TestCase):

    def setUp(self):
        self.item = TestModel()

    def _create_test_item(self, content="basic content", status=STATUS_PENDING):
        item = self.item
        item.test_field = content
        item.status = status
        item.save()
        return item

    def test_create_moderated_content(self):
        item = self._create_test_item(content="this must be pending")
        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEquals(item.test_field, "this must be pending")

    def test_get_accepted_content(self):
        item = self._create_test_item(status=STATUS_ACCEPTED, content="this must be accepted")
        self.assertIsNotNone(TestModel.objects.accepted())
        self.assertEquals(item.test_field, "this must be accepted")

    def test_get_rejected_content(self):
        item = self._create_test_item(status=STATUS_REJECTED, content="this must be rejected")
        self.assertIsNotNone(TestModel.objects.accepted())
        self.assertEquals(item.test_field, "this must be rejected")
