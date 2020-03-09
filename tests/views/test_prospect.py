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

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from mock import patch

from base.tests.factories.person import PersonFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from base.tests.factories.user import UserFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory
from continuing_education.tests.utils.api_patcher import api_create_patcher, api_start_patcher, api_add_cleanup_patcher
from openapi_client.rest import ApiException


class ProspectTestCase(TestCase):
    def setUp(self):
        self.client.force_login(self.user)
        self.prospect = {
            'name': 'NameTest',
            'first_name': 'FirstNameTest',
            'postal_code': 5620,
            'city': 'CityTest',
            'phone_number': 1234567809,
            'email': 'a@b.com',
            'formation': self.formation['uuid']
        }
        api_start_patcher(self)
        api_add_cleanup_patcher(self)

    @classmethod
    def setUpTestData(cls):
        cls.user =  UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.person_information = ContinuingEducationPersonDictFactory(cls.person.uuid)
        cls.formation = ContinuingEducationTrainingDictFactory()
        api_create_patcher(cls)

    def test_post_prospect_with_missing_information(self):
        self.prospect['name'] = ''
        response = self.client.post(reverse('prospect_form'), data=self.prospect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prospect_form.html')

    def test_post_prospect_with_not_valid_email(self):
        self.prospect['email'] = 'A'
        response = self.client.post(reverse('prospect_form'), data=self.prospect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prospect_form.html')

    def test_post_valid_prospect(self):
        self.mocked_post_prospect.return_value = self.prospect
        response = self.client.post(reverse('prospect_form', args=[self.formation['uuid']]), data=self.prospect)
        self.assertEqual(response.status_code, 302)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertIn(
            gettext(_("Your form was correctly send.")),
            messages_list
        )
        self.assertRedirects(response, reverse('continuing_education_home'))

    @patch('json.loads')
    def test_post_valid_prospect_but_server_error(self, mock_json):
        self.mocked_post_prospect.side_effect = mocked_failed_post_request
        response = self.client.post(reverse('prospect_form', args=[self.formation['uuid']]), data=self.prospect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prospect_form.html')


def mocked_failed_post_request(*args, **kwargs):
    raise ApiException()
