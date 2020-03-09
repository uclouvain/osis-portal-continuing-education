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
from collections import namedtuple

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, gettext
from mock import Mock
from rest_framework import status

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.person import PersonFactory
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory
from continuing_education.tests.utils.api_patcher import api_create_patcher, api_start_patcher, api_add_cleanup_patcher
from openapi_client.rest import ApiException


class AdmissionFileTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_acad_year = create_current_academic_year()
        cls.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)
        cls.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        cls.request = RequestFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.person_information = ContinuingEducationPersonDictFactory(cls.person.uuid)
        cls.admission = AdmissionDictFactory(cls.person_information)
        cls.admission_file = SimpleUploadedFile(
            name='upload_test.pdf',
            content=str.encode("test_content"),
            content_type="application/pdf"
        )
        api_create_patcher(cls)

    def setUp(self):
        self.client.force_login(self.user)
        api_start_patcher(self)
        api_add_cleanup_patcher(self)

    def mocked_api_exception(self, *args, **kwargs):
        raise ApiException(
            http_resp=namedtuple('Response', 'status, reason, data, getheaders')('', '', '', Mock()))

    def test_upload_file_success(self):
        url = reverse('upload_file', args=[self.admission['uuid']])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        response = self.client.post(url, {'myfile': self.admission_file}, HTTP_REFERER=redirect_url)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn(
            gettext(_("The document is uploaded correctly")),
            messages_list
        )
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    def test_upload_file_error(self):
        self.mocked_upload_file.side_effect = self.mocked_api_exception
        url = reverse('upload_file', args=[self.admission['uuid']])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        response = self.client.post(url, {'myfile': self.admission_file}, HTTP_REFERER=redirect_url)
        self.assertRedirects(response, redirect_url + '#documents')

    def test_delete_file_success(self):
        url = reverse('remove_file', args=[self.admission['uuid'], "1452"])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        response = self.client.delete(
            url,
            {'myfile': self.admission_file},
            HTTP_REFERER=redirect_url
        )
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            gettext(_("File correctly deleted")),
            str(messages_list[0])
        )
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    def test_delete_file_error(self):
        self.mocked_delete_file.side_effect = self.mocked_api_exception
        url = reverse('remove_file', args=[self.admission['uuid'], "5478"])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})

        response = self.client.delete(
            url,
            {'myfile': self.admission_file},
            HTTP_REFERER=redirect_url
        )
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)
        # an error should raise as the admission is not retrieved from test
        self.assertIn(
            gettext(_("A problem occured during delete")),
            str(messages_list[0])
        )
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    def test_download_file_success(self):
        self.mocked_get_file.return_value = {
            'name': self.admission_file.name,
            'content': "bW9jaw==",
            'content_type': "application/pdf"
        }
        url = reverse('download_file', args=[uuid.uuid4(), self.admission['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for value in ['attachment', self.admission_file.name]:
            self.assertIn(value, response['Content-Disposition'])

    def test_download_file_error(self):
        self.mocked_get_file.side_effect = self.mocked_api_exception
        url = reverse('download_file', args=[uuid.uuid4(), self.admission['uuid']])
        redirect_url = reverse('admission_detail', args=[self.admission['uuid']]) + '#documents'
        response = self.client.get(url, HTTP_REFERER=redirect_url)
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertIn(
            gettext(('An unexpected error occurred during download')),
            str(messages_list[0])
        )
