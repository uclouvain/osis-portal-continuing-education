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
import base64
import uuid
from unittest import mock
from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, gettext
from requests import Response
from rest_framework import status

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.person import PersonFactory
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory


class AdmissionFileTestCase(TestCase):
    def setUp(self):
        current_acad_year = create_current_academic_year()
        self.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)

        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        self.request = RequestFactory()
        self.person = PersonFactory(user=self.user)
        self.person_information = ContinuingEducationPersonDictFactory(self.person.uuid)
        self.admission = AdmissionDictFactory(self.person_information)
        self.admission_file = SimpleUploadedFile(
            name='upload_test.pdf',
            content=str.encode("test_content"),
            content_type="application/pdf"
        )

        self.patcher = patch(
            "continuing_education.views.admission._get_files_list",
            return_value=Response()
        )
        self.mocked_called_api_function = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.get_patcher = patch(
            "continuing_education.views.api.get_data_from_osis",
            return_value=self.admission
        )
        self.mocked_called_api_function_get = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

    def mocked_success_post_request(self, **kwargs):
        response = Response()
        response.status_code = status.HTTP_201_CREATED
        return response

    def mocked_failed_post_request(self, **kwargs):
        response = Response()
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.json = lambda *args, **kwargs: "BAD REQUEST"
        return response

    def mocked_failed_post_request_name_too_long(self, **kwargs):
        response = Response()
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        response.json = lambda *args, **kwargs: "NAME TOO LONG"
        return response

    @mock.patch('requests.post', side_effect=mocked_success_post_request)
    def test_upload_file_success(self, mock_post):
        url = reverse('upload_file', args=[self.admission['uuid']])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        response = self.client.post(url, {'myfile': self.admission_file}, HTTP_REFERER=redirect_url)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertEquals(response.status_code, status.HTTP_302_FOUND)
        self.assertIn(
            gettext(_("The document is uploaded correctly")),
            messages_list
        )
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    @mock.patch('requests.post', side_effect=mocked_failed_post_request)
    def test_upload_file_error(self, mock_post):
        url = reverse('upload_file', args=[self.admission['uuid']])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        response = self.client.post(url, {'myfile': self.admission_file}, HTTP_REFERER=redirect_url)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertEquals(response.status_code, status.HTTP_302_FOUND)
        # an error should raise as the admission is not retrieved from test
        self.assertIn("BAD REQUEST", messages_list)
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    @mock.patch('requests.post', side_effect=mocked_failed_post_request_name_too_long)
    def test_upload_file_error_name_too_long(self, mock_fail):
        url = reverse('upload_file', args=[self.admission['uuid']])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        file = SimpleUploadedFile(
            name='upload_test_with_too_much_character_oh_no_this_will_fail_upload_test_' +
                 'with_too_much_character_oh_no_this_will_fail.pdf',
            content=str.encode("test_content"),
            content_type="application/pdf"
        )
        response = self.client.post(url, {'myfile': file}, HTTP_REFERER=redirect_url)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertEquals(response.status_code, status.HTTP_302_FOUND)
        # an error should raise as the admission is not retrieved from test
        self.assertIn("NAME TOO LONG", messages_list)

    def mocked_success_delete_request(self, **kwargs):
        response = Response()
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    def mocked_failed_delete_request(self, **kwargs):
        response = Response()
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return response

    @mock.patch('requests.delete', side_effect=mocked_success_delete_request)
    def test_delete_file_success(self, mock_delete):
        url = reverse('remove_file', args=[self.admission['uuid'], "1452"])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})
        response = self.client.delete(
            url,
            {'myfile': self.admission_file},
            HTTP_REFERER=redirect_url
        )

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEquals(response.status_code, 302)
        self.assertIn(
            gettext(_("File correctly deleted")),
            str(messages_list[0])
        )
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    @mock.patch('requests.delete', side_effect=mocked_failed_delete_request)
    def test_delete_file_error(self, mock_delete):
        url = reverse('remove_file', args=[self.admission['uuid'], "5478"])
        redirect_url = reverse('admission_detail', kwargs={'admission_uuid': self.admission['uuid']})

        response = self.client.delete(
            url,
            {'myfile': self.admission_file},
            HTTP_REFERER=redirect_url
        )
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEquals(response.status_code, 302)
        # an error should raise as the admission is not retrieved from test
        self.assertIn(
            gettext(_("A problem occured during delete")),
            str(messages_list[0])
        )
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]) + '#documents')

    def get_mocked_file_response(self, headers):
        response = HttpResponse(status=status.HTTP_200_OK)
        response.content = '{"content": "'+str(base64.b64encode(b'test'))+\
                           '", "path":"test_name.pdf", "name":"test_name.pdf"}'
        return response

    @mock.patch('requests.get', side_effect=get_mocked_file_response)
    def test_download_file_success(self, mock_get):
        url = reverse('download_file', args=[uuid.uuid4(), self.admission['uuid']])
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        for value in ['attachment', 'test_name']:
            self.assertIn(value, response['Content-Disposition'])

    @mock.patch('requests.get', return_value=HttpResponse(status=status.HTTP_404_NOT_FOUND))
    def test_download_file_error(self, mock_get):
        url = reverse('download_file', args=[uuid.uuid4(), self.admission['uuid']])
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
