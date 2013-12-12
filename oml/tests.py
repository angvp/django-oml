# -*- coding: utf-8 -*-
"""
django-oml tests
"""

from .models import (ModeratedModel, LogModeratedModel, STATUS_ACCEPTED,
                     STATUS_PENDING, STATUS_REJECTED)
from django.contrib.auth.models import User, Group
from django.db import models
from django.test import TestCase


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
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item_a = self._create_test_item(status=STATUS_ACCEPTED)
        item_p = self._create_test_item(status=STATUS_PENDING)

        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item_p.accept(self.user)
        item_p.test_field = 'change_p me 1'
        item_p.save_form_log_moderated()
        item_p.define_status_of_object(self.user)

        self.assertEquals(LogModeratedModel.objects.all().count(), 1)

        item_p.test_field = 'change_p me 2'
        item_p.save_form_log_moderated()
        item_p.define_status_of_object(self.user)

        self.assertEquals(LogModeratedModel.objects.all().count(), 1)

        item_a.test_field = 'change_a me 1'
        item_a.save_form_log_moderated()
        item_a.define_status_of_object(self.user)

        self.assertEquals(LogModeratedModel.objects.all().count(), 2)

        item_a.accept(self.user)
        self.assertEquals(LogModeratedModel.objects.all().count(), 1)

        item_p.accept(self.user)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_accept_w_accepted(self):
        item = self._create_test_item(status=STATUS_ACCEPTED)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_accept_w_pending(self):
        # Check if a new pending object can be
        # accepted
        item = self._create_test_item()
        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        # Check if an existing object can be edited
        # and accepted
        item.test_field = 'changed field'
        item.save_form_log_moderated()
        item.define_status_of_object(self.user)

        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEqual(item.test_field, 'changed field')
        self.assertEquals(LogModeratedModel.objects.all().count(), 1)

        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEqual(item.test_field, 'changed field')
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_accept_w_rejected(self):
        # Check if a new object with rejected status
        # can be accepted
        item = self._create_test_item(status=STATUS_REJECTED)
        self.assertEquals(item.status, STATUS_REJECTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_reject_w_accepted(self):
        # Rejecting a rejected object should noy
        # modify it
        item = self._create_test_item(status=STATUS_ACCEPTED)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.reject(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_reject_w_pending(self):
        # Check if a new pending object is deleted
        # when rejected
        item = self._create_test_item()
        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.reject(self.user)
        self.assertEquals(TestModel.objects.all().count(), 0)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        # Check if an pending object with a previous
        # accepted state is reverted when rejected
        item = self._create_test_item()
        item.accept(self.user)
        self.assertEquals(item.status, STATUS_ACCEPTED)

        item.test_field = 'changed field'
        item.save_form_log_moderated()
        item.define_status_of_object(self.user)

        self.assertEquals(item.status, STATUS_PENDING)
        self.assertEqual(item.test_field, 'changed field')
        self.assertEquals(LogModeratedModel.objects.all().count(), 1)

        item.reject(self.user)
        # Refresh the item
        item_updated = TestModel.objects.get(id=item.id)
        self.assertEquals(item_updated.status, STATUS_ACCEPTED)
        self.assertEqual(item_updated.test_field, 'basic content')
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

    def test_model_method_reject_w_rejected(self):
        # Rejecting a rejected object should noy
        # modify it
        item = self._create_test_item(status=STATUS_REJECTED)
        self.assertEquals(item.status, STATUS_REJECTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)

        item.reject(self.user)
        self.assertEquals(item.status, STATUS_REJECTED)
        self.assertEquals(LogModeratedModel.objects.all().count(), 0)
