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
from unittest.mock import patch

import mock
from django.conf import settings
from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, gettext
from requests import Response
from rest_framework import status

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.admission_state_choices import REGISTRATION_SUBMITTED, ACCEPTED, REJECTED
from continuing_education.tests.factories.admission import RegistrationDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory
from continuing_education.views.common import get_submission_errors, _get_managers_mails


class ViewStudentRegistrationTestCase(TestCase):

    @staticmethod
    def mock_pdf_template_return():
        input_pdf_path = "{}{}".format(settings.BASE_DIR, '/continuing_education/tests/ressources/pdf_with_form.pdf')
        import pdfrw
        return pdfrw.PdfReader(input_pdf_path)

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)

    def setUp(self):
        self.person_information = ContinuingEducationPersonDictFactory(self.person.uuid)
        self.admission_rejected = RegistrationDictFactory(self.person_information, state=REJECTED)
        self.admission_accepted = RegistrationDictFactory(self.person_information, state=ACCEPTED)
        self.registration_submitted = RegistrationDictFactory(self.person_information, state=REGISTRATION_SUBMITTED)
        self.client.force_login(self.user)
        self.patcher = patch(
            "continuing_education.views.registration._get_files_list",
            return_value={}
        )
        self.mocked_called_api_function = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.get_patcher = patch(
            "continuing_education.views.api.get_data_from_osis",
            return_value=self.admission_accepted
        )
        self.mocked_called_api_function_get = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        self.get_list_patcher = patch(
            "continuing_education.views.api.get_admission_list",
            return_value={'results': [self.admission_accepted]}
        )
        self.get_list_person_patcher = patch(
            "continuing_education.views.api.get_continuing_education_person",
            return_value=self.person_information
        )
        self.mocked_called_api_function_get_list = self.get_list_patcher.start()
        self.mocked_called_api_function_get_persons = self.get_list_person_patcher.start()
        self.addCleanup(self.get_list_patcher.stop)
        self.addCleanup(self.get_list_person_patcher.stop)

    def test_registration_detail(self):
        url = reverse('registration_detail', args=[self.admission_accepted['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_detail.html')

        self.assertEqual(response.context['admission'], self.admission_accepted)
        self.assertTrue(response.context['registration_is_submittable'])

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn(
            gettext("Your registration file has been saved. Please consider the following information :"),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("You are still able to edit the form, via the 'Edit' button"),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("You can upload documents via the 'Documents'"),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("Do not forget to submit your file when it is complete"),
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.INFO)

    def test_registration_detail_not_submittable(self):
        self.admission_accepted['marital_status'] = ''

        url = reverse('registration_detail', args=[self.admission_accepted['uuid']])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_detail.html')

        self.assertEqual(response.context['admission'], self.admission_accepted)
        self.assertFalse(response.context['registration_is_submittable'])

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 2)

        self.assertIn(
            gettext("Your registration file has been saved. Please consider the following information :"),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("You are still able to edit the form, via the 'Edit' button"),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("You can upload documents via the 'Documents'"),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("Do not forget to submit your file when it is complete"),
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.INFO)

        self.assertIn(
            gettext("Your file is not submittable because you did not provide the following data : "),
            str(messages_list[1])
        )
        self.assertIn(
            gettext("Marital status"),
            str(messages_list[1])
        )
        self.assertEqual(messages_list[1].level, messages.WARNING)

    def test_registration_submitted_detail(self):
        self.mocked_called_api_function_get.return_value = self.registration_submitted
        url = reverse('registration_detail', args=[self.registration_submitted['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_detail.html')

        self.assertEqual(response.context['admission'], self.registration_submitted)
        self.assertFalse(response.context['registration_is_submittable'])

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 2)

        self.assertIn(
            gettext(
                "Your registration file has been saved. "
                "<b>Please consider the following remaining instructions</b> to complete submission. "
            ),
            str(messages_list[0])
        )
        mails = _get_managers_mails(self.registration_submitted['formation'])
        self.assertEqual(messages_list[0].level, messages.INFO)
        self.assertIn(
            gettext("If you want to edit again your registration, please contact the program manager : %(mail)s")
            % {'mail': mails},
            str(messages_list[1])
        )
        self.assertEqual(messages_list[1].level, messages.WARNING)

    @mock.patch('continuing_education.views.api.prepare_registration_for_submit')
    @mock.patch('continuing_education.views.api.update_data_to_osis', return_value=Response())
    def test_registration_submit(self, mock_update, mock_prepare):
        url = reverse('registration_submit')
        response = self.client.post(
            url,
            follow=True,
            data={
                "submit": True,
                "admission_uuid": self.admission_accepted['uuid']
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission']['state'], admission_state_choices.REGISTRATION_SUBMITTED)
        self.assertTemplateUsed(response, 'registration_detail.html')

    @mock.patch('continuing_education.views.api.update_data_to_osis', return_value=Response())
    def test_registration_submit_not_registration_submitted(self, mock_update):
        self.mocked_called_api_function_get.return_value = self.registration_submitted
        url = reverse('registration_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_uuid": self.registration_submitted['uuid']
            }
        )
        self.assertEqual(response.status_code, 302)

    def test_registration_submit_not_complete(self):
        self.admission_accepted['marital_status'] = ''

        url = reverse('registration_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_uuid": self.admission_accepted['uuid']
            }
        )
        self.assertEqual(response.status_code, 302)

    def test_edit_get_registration_found(self):
        url = reverse('registration_edit', args=[self.admission_accepted['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_form.html')

    def test_edit_registration_submitted_unauthorized(self):
        self.admission_accepted['state'] = REGISTRATION_SUBMITTED
        url = reverse('registration_edit', args=[self.admission_accepted['uuid']])
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 401)
        self.assertTemplateUsed(get_response, 'access_denied.html')

        post_response = self.client.post(url)
        self.assertEqual(post_response.status_code, 401)
        self.assertTemplateUsed(post_response, 'access_denied.html')

    @mock.patch('continuing_education.business.pdf_filler._get_pdf_template')
    def test_pdf_content(self, mock_pdf_template):
        mock_pdf_template = self.mock_pdf_template_return()
        self.mocked_called_api_function_get.return_value = self.registration_submitted
        self.mocked_called_api_function_get.return_value['person_information']['birth_date']="2019-10-17"
        a_superuser = SuperUserFactory()
        self.client.force_login(a_superuser)
        url = reverse('registration_pdf', args=[self.registration_submitted['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.__getitem__('content-type'), 'application/pdf;')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RegistrationSubmissionErrorsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        ac = AcademicYearFactory()
        AcademicYearFactory(year=ac.year + 1)
        cls.person = PersonFactory()

    def setUp(self):
        self.admission = RegistrationDictFactory(self.person.uuid)

    def test_registration_is_submittable(self):
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertFalse(
            errors
        )

    def test_registration_is_not_submittable_missing_data_in_all_objects(self):
        self.admission['residence_address']['postal_code'] = ''
        self.admission['billing_address']['postal_code'] = ''
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
                _("Postal code"): [_("This field is required.")]
            }
        )

    def test_registration_is_not_submittable_missing_registration_data(self):
        self.admission['marital_status'] = ''
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("Marital status"): [_("This field is required.")]
            }
        )

    def test_registration_is_not_submittable_missing_address_data(self):
        self.admission['billing_address']['postal_code'] = ''
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
            }
        )

    def test_registration_is_not_submittable_wrong_phone_format(self):
        wrong_numbers = [
            '1234567891',
            '00+32474945669',
            '0+32474123456',
            '(32)1234567891',
            '0474.12.34.56',
            '0474 123456'
        ]
        short_numbers = ['0032123', '+321234', '0123456']
        long_numbers = ['003212345678912456', '+3212345678912345', '01234567891234567']
        for number in wrong_numbers + short_numbers + long_numbers:
            self.admission['residence_phone'] = number
            errors, errors_fields = get_submission_errors(self.admission, is_registration=True)
            self.assertDictEqual(
                errors,
                {
                    _("Residence phone"): [_("Phone number must start with 0 or 00 or '+' followed by at least "
                                             "7 digits and up to 15 digits.")
                                           ],
                }
            )
