##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import uuid
from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from rest_framework import status

from base.tests.factories.person import PersonFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonFactory


class ProspectTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        self.person = PersonFactory(user=self.user)
        self.person_information = ContinuingEducationPersonFactory(person=self.person)
        self.prospect = {
            'name': 'NameTest',
            'first_name': 'FirstNameTest',
            'postal_code': 5620,
            'city': 'CityTest',
            'phone_number': 1234567809,
            'email': 'a@b.com',
            'formation': uuid.uuid4()
        }

        self.patcher = patch(
            "continuing_education.views.api.post_prospect",
            return_value=({}, status.HTTP_201_CREATED)
        )
        self.mocked_called_api_function = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_post_prospect_with_missing_formation(self):
        prospect = self.prospect
        prospect['formation'] = None
        response = self.client.post(reverse('prospect_form'), data=prospect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prospect_form.html')

    def test_post_prospect_with_not_valid_email(self):
        prospect = self.prospect
        prospect['email'] = 'A'
        response = self.client.post(reverse('prospect_form'), data=prospect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prospect_form.html')

    def mocked_success_post_request(*args, **kwargs):
        return {}, status.HTTP_201_CREATED

    def mocked_failed_post_request(*args, **kwargs):
        return {}, status.HTTP_400_BAD_REQUEST

    @patch('continuing_education.views.api.post_data_to_osis', side_effect=mocked_success_post_request)
    def test_post_valid_prospect(self, mocked_success_post):
        response = self.client.post(reverse('prospect_form'), data=self.prospect)
        self.assertEqual(response.status_code, 302)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertIn(
            gettext(_("Your form was correctly send.")),
            messages_list
        )
        self.assertRedirects(response, reverse('continuing_education_home'))

    @patch('continuing_education.views.api.post_data_to_osis', side_effect=mocked_failed_post_request)
    def test_post_valid_prospect_but_server_error(self, mock_fail):
        response = self.client.post(reverse('prospect_form'), data=self.prospect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prospect_form.html')
