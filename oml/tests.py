# -*- coding: utf-8 -*-
"""
django-oml tests
"""

from .models import (ModeratedModel, LogModeratedModel, STATUS_ACCEPTED,
                     STATUS_PENDING, STATUS_REJECTED)
from django.contrib.auth.models import User, Group
from django.db import models
from django.test import TestCase

import ipdb


class TestModel(ModeratedModel):
    test_field = models.CharField(max_length=200)


class ModeratedModelTestCase(TestCase):

    def setUp(self):
        #ipdb.set_trace()
        self.groups = [Group.objects.create(id=1, name='non_moderated')]
        self.groups.append(Group.objects.create(id=2,  name='moderated'))
        # Create a moderated user

        # Create an unmoderated user
        self.user = User.objects.create(username="moderator",
                                        password="moderator",
                                        email="example@example.com")
        self.user.group = self.groups[1]

    def _create_test_item(self, content="basic content",
                          status=STATUS_PENDING):
        item = TestModel()
        item.test_field = content
        item.status = status
        item.save()
        return item

    def test_create_moderated_content(self):
        item = self._create_test_item(content="this must be pending")
        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEqual(TestModel.objects.accepted().count(), 0)
        self.assertEqual(TestModel.objects.pending().count(), 1)
        self.assertEqual(TestModel.objects.rejected().count(), 0)
        self.assertEquals(item.test_field, "this must be pending")

    def test_get_accepted_content(self):
        item = self._create_test_item(status=STATUS_ACCEPTED,
                                      content="this must be accepted")
        self.assertEqual(TestModel.objects.accepted().count(), 1)
        self.assertEqual(TestModel.objects.pending().count(), 0)
        self.assertEqual(TestModel.objects.rejected().count(), 0)
        self.assertEquals(item.test_field, "this must be accepted")

    def test_get_rejected_content(self):
        item = self._create_test_item(status=STATUS_REJECTED,
                                      content="this must be rejected")
        self.assertEqual(TestModel.objects.accepted().count(), 0)
        self.assertEqual(TestModel.objects.pending().count(), 0)
        self.assertEqual(TestModel.objects.rejected().count(), 1)
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

    def test_model_log_moderated_content_count(self):
        pass

    def test_model_method_accept_w_accepted(self):
        pass

    def test_model_method_accept_w_pending(self):
        item = self._create_test_item()
        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.test_field = 'changed field'
        item.save_form_log_moderated(item.status)
        item.define_status_of_object(self.user)

        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEqual(item.test_field, 'changed field')
        self.assertEquals(LogModeratedModel.objects.all().count(), 1)

        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEqual(item.test_field, 'changed field')
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_accept_w_rejected(self):
        pass

    def test_model_method_reject_w_accepted(self):
        item = self._create_test_item()
        self.assertEquals(item.status, STATUS_PENDING)
        item.reject(self.user)
        self.assertEquals(item.status, STATUS_REJECTED)

    def test_model_method_reject_w_pending(self):
        pass

    def test_model_method_reject_w_rejected(self):
        pass
