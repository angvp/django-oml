# -*- coding: utf-8 -*-
"""
django-oml tests
"""

from .models import (ModeratedModel, STATUS_ACCEPTED, STATUS_PENDING,
                     STATUS_REJECTED)
from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase


class TestModel(ModeratedModel):
    test_field = models.CharField(max_length=200)


class ModeratedModelTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="moderator", password="moderator",
                                        email="example@example.com")

    def _create_test_item(self, content="basic content", status=STATUS_PENDING):
        item = TestModel()
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

    def test_count(self):
        """
        Let's create some items with different status to figure out if count
        is working fine
        """
        self._create_test_item(status=STATUS_REJECTED, content="item rejected")
        self._create_test_item(status=STATUS_REJECTED, content="item rejected")
        self._create_test_item(status=STATUS_REJECTED, content="item rejected")
        self._create_test_item(status=STATUS_PENDING, content="item pending")
        self._create_test_item(status=STATUS_PENDING, content="item pending")
        self._create_test_item(status=STATUS_ACCEPTED, content="item accepted")
        self.assertEquals(TestModel.objects.accepted().count(), 1)
        self.assertEquals(TestModel.objects.pending().count(), 2)
        self.assertEquals(TestModel.objects.rejected().count(), 3)
        self.assertEquals(TestModel.objects.count(), 6)

    def test_model_method_accept(self):
        item = self._create_test_item()
        self.assertEquals(item.status, STATUS_PENDING)
        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)

    def test_model_method_reject(self):
        item = self._create_test_item()
        self.assertEquals(item.status, STATUS_PENDING)
        item.reject(self.user)
        self.assertEquals(item.status, STATUS_REJECTED)
