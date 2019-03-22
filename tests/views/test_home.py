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
from random import choice
from string import ascii_lowercase
from unittest import mock

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory


class ViewHomeTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        PersonFactory(user=self.user)
        self.cet = ContinuingEducationTrainingDictFactory(
            active=False
        )
        self.patcher = patch(
            "continuing_education.views.api.get_data_from_osis",
            return_value=self.cet
        )
        self.mocked_called_api_function = self.patcher.start()

        self.addCleanup(self.patcher.stop)

    @mock.patch('continuing_education.views.api.get_data_list_from_osis')
    @mock.patch('continuing_education.views.api.get_admission_list')
    @mock.patch('continuing_education.views.api.get_registration_list')
    def test_main_view(self, mock_list, mock_get_admission, mock_get_registration):
        url = reverse('continuing_education_home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'continuing_education/home.html')

    def test_redirect_to_prospect_form_if_formation_not_activated_in_url(self):
        self.client.logout()

        url = reverse('continuing_education_home', kwargs={'formation_id': self.cet['uuid']})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('prospect_form', kwargs={'formation_uuid': self.cet['uuid']}))


class FormationsListTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.person = PersonFactory(user=self.user)
        self.person_iufc = ContinuingEducationPersonDictFactory(self.person.uuid)
        self.an_academic_year = AcademicYearFactory(current=True)

    @mock.patch('continuing_education.views.api.get_data_list_from_osis')
    def test_formations_list(self, mock_get_training_list):
        mock_get_training_list.return_value = {
            'count': 11,
            'results': [
                {
                    'acronym': ''.join([choice(ascii_lowercase) for _ in range(4)]),
                    'title': 'title-{}'.format(i)
                }
                for i in range(11)
            ]
        }
        formations = mock_get_training_list.return_value
        url = reverse('formations_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pages_count'], range(1,2))
        self.assertEqual(response.context['formations'], formations['results'])
        self.assertTemplateUsed(response, 'continuing_education/formations.html')

    @mock.patch('continuing_education.views.api.get_admission_list')
    @mock.patch('continuing_education.views.api.get_registration_list')
    @mock.patch('continuing_education.views.api.get_data_list_from_osis')
    def test_bypass_formations_list_when_logged_in(self, mock_get_admissions, mock_get_registrations, mock_get_list):
        self.client.force_login(self.user)
        url = reverse('formations_list')
        mock_get_admissions.return_value = [AdmissionDictFactory(self.person_iufc)]
        response = self.client.get(url)
        self.assertTrue(self.user.is_authenticated)
        self.assertRedirects(response, "/continuing_education/home/")
