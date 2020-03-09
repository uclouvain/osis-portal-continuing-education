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

from continuing_education.views.utils.sdk import get_token_from_osis, get_personal_token, get_admission, \
    get_registration, get_continuing_education_training, get_continuing_education_person, get_admission_list, \
    get_registration_list, get_continuing_education_training_list, post_prospect, post_admission, update_admission, \
    update_registration, get_files_list, get_file, delete_file, upload_file
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from mock import patch
from rest_framework import status

from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.person import PersonFactory
from continuing_education.models.enums.admission_state_choices import SUBMITTED
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory


class ApiMethodsTestCase(TestCase):
    def setUp(self):
        self.client.force_login(self.user)
        self.get_token_from_osis_patcher = patch(
            'continuing_education.views.utils.sdk.get_token_from_osis',
            return_value='token'
        )
        self.get_token_from_osis_patcher.start()

    @classmethod
    def setUpTestData(cls):
        current_acad_year = create_current_academic_year()
        cls.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)
        cls.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        cls.request = RequestFactory()
        cls.request.session = {}
        cls.request.user = cls.user
        cls.person = PersonFactory(user=cls.user)
        cls.person_information = ContinuingEducationPersonDictFactory(cls.person.uuid)
        cls.formation = ContinuingEducationTrainingDictFactory()
        cls.admission = AdmissionDictFactory(cls.person_information)
        cls.admission_submitted = AdmissionDictFactory(cls.person_information, SUBMITTED)

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

    def test_get_personal_token_not_in_session(self):
        response = HttpResponse(status=status.HTTP_200_OK)
        response.json = lambda: {'token': 'token'}
        token = get_personal_token(self.request)
        self.assertEqual(token, "token")
        self.assertEqual(self.request.session['personal_token'], "token")

    def test_get_personal_token_in_session(self):
        self.request.session['personal_token'] = 'token'
        token = get_personal_token(self.request)
        self.assertEqual(token, "token")
        self.assertEqual(self.request.session['personal_token'], "token")

    @mock.patch('continuing_education.views.utils.sdk.api.persons_uuid_admissions_get')
    def test_get_admission_list(self, mock_get):
        get_admission_list(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.persons_uuid_registrations_get')
    def test_get_registration_list(self, mock_get):
        get_registration_list(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.trainings_get')
    def test_get_continuing_education_training_list(self, mock_get):
        get_continuing_education_training_list()
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_uuid_get')
    def test_get_admission(self, mock_get):
        get_admission(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.registrations_uuid_get')
    def test_get_registration(self, mock_get):
        get_registration(self.request, uuid.uuid4())
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.trainings_uuid_get')
    def test_get_continuing_education_training(self, mock_get):
        get_continuing_education_training(self.request)
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.persons_details_get')
    def test_get_continuing_education_person(self, mock_get):
        get_continuing_education_person(self.request)
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.prospects_post')
    def test_post_prospect(self, mock_post):
        post_prospect({})
        self.assertTrue(mock_post.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_post')
    def test_post_admission(self, mock_post):
        post_admission(self.request, {})
        self.assertTrue(mock_post.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_uuid_patch')
    def test_update_admission(self, mock_patch):
        update_admission(self.request, {'uuid': 'uuid'})
        self.assertTrue(mock_patch.called)

    @mock.patch('continuing_education.views.utils.sdk.api.registrations_uuid_patch')
    def test_update_registration(self, mock_patch):
        update_registration(self.request, {'uuid': 'uuid'})
        self.assertTrue(mock_patch.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_uuid_files_get')
    def test_get_files_list(self, mock_get):
        get_files_list(self.request, 'adm_uuid')
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_uuid_files_file_uuid_get')
    def test_get_file(self, mock_get):
        get_file(self.request, 'adm_uuid', 'file_uuid')
        self.assertTrue(mock_get.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_uuid_files_file_uuid_delete')
    def test_delete_file(self, mock_delete):
        delete_file(self.request, 'adm_uuid', 'file_uuid')
        self.assertTrue(mock_delete.called)

    @mock.patch('continuing_education.views.utils.sdk.api.admissions_uuid_files_post')
    def test_upload_file(self, mock_post):
        upload_file(self.request, 'adm_uuid')
        self.assertTrue(mock_post.called)
