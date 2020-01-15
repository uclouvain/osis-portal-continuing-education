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
from unittest import mock

from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.person import PersonFactory
from continuing_education.models.enums.admission_state_choices import SUBMITTED
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory
from continuing_education.views.api import get_token_from_osis, get_personal_token, get_admission, \
    get_registration, get_continuing_education_training, get_continuing_education_person


class ApiMethodsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_acad_year = create_current_academic_year()
        cls.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)
        cls.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        cls.person = PersonFactory(user=cls.user)
        cls.person_information = ContinuingEducationPersonDictFactory(cls.person.uuid)
        cls.formation = ContinuingEducationTrainingDictFactory()
        cls.admission = AdmissionDictFactory(cls.person_information)
        cls.admission_submitted = AdmissionDictFactory(cls.person_information, SUBMITTED)

    def setUp(self):
        self.client.force_login(self.user)
        self.request = RequestFactory()
        self.request.user = self.user
        self.request.session = {}

    @mock.patch('requests.post')
    def test_get_token_from_osis(self, mock_post):
        response = HttpResponse(status=status.HTTP_200_OK)
        response.json = lambda: {'token': 'token'}
        mock_post.return_value = response
        token = get_token_from_osis(self.user.username)
        self.assertEqual(token, "token")

    @mock.patch('requests.post', return_value=HttpResponse(status=status.HTTP_404_NOT_FOUND))
    def test_get_token_from_osis_not_found(self, mock_post):
        token = get_token_from_osis(self.user.username)
        self.assertEqual(token, "")

    @mock.patch('requests.post')
    def test_get_personal_token_not_in_session(self, mock_post):
        response = HttpResponse(status=status.HTTP_200_OK)
        response.json = lambda: {'token': 'token'}
        mock_post.return_value = response
        token = get_personal_token(self.request)
        self.assertEqual(token, "token")
        self.assertEqual(self.request.session['personal_token'], "token")
        self.assertTrue(mock_post.called)

    @mock.patch('requests.post')
    def test_get_personal_token_in_session(self, mock_post):
        self.request.session['personal_token'] = 'token'
        token = get_personal_token(self.request)
        self.assertEqual(token, "token")
        self.assertEqual(self.request.session['personal_token'], "token")
        self.assertFalse(mock_post.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_404_NOT_FOUND))
    def test_get_admission_not_found(self, mock_get, mock_token):
        with self.assertRaises(Http404):
            get_admission(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_403_FORBIDDEN))
    def test_get_admission_denied(self, mock_get, mock_token):
        with self.assertRaises(PermissionDenied):
            get_admission(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_404_NOT_FOUND))
    def test_get_registration_not_found(self, mock_get, mock_token):
        with self.assertRaises(Http404):
            get_registration(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_403_FORBIDDEN))
    def test_get_registration_denied(self, mock_get, mock_token):
        with self.assertRaises(PermissionDenied):
            get_registration(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_404_NOT_FOUND))
    def test_get_continuing_education_training_not_found(self, mock_get, mock_token):
        with self.assertRaises(Http404):
            get_continuing_education_training(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_403_FORBIDDEN))
    def test_get_continuing_education_training_denied(self, mock_get, mock_token):
        with self.assertRaises(PermissionDenied):
            get_continuing_education_training(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_404_NOT_FOUND))
    def test_get_continuing_education_person_not_found(self, mock_get, mock_token):
        with self.assertRaises(Http404):
            get_continuing_education_person(self.request)
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.api.get_personal_token')
    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_403_FORBIDDEN))
    def test_get_continuing_education_person_denied(self, mock_get, mock_token):
        with self.assertRaises(PermissionDenied):
            get_continuing_education_person(self.request)
        self.assertTrue(mock_get.called)
