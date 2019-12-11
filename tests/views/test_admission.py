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
import datetime
import json
import uuid
from unittest import mock
from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, gettext

from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.person import PersonFactory
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.admission_state_choices import SUBMITTED, ACCEPTED_NO_REGISTRATION_REQUIRED, \
    ACCEPTED
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory
from continuing_education.tests.utils.api_patcher import api_create_patcher, api_start_patcher, api_add_cleanup_patcher
from continuing_education.views.admission import admission_form
from continuing_education.views.common import get_submission_errors, _get_managers_mails


class ViewStudentAdmissionTestCase(TestCase):
    def setUp(self):
        self.client.force_login(self.user)
        self.files_list_patcher = patch(
            "continuing_education.views.admission._get_files_list",
            return_value={}
        )
        self.mocked_called_api_function = self.files_list_patcher.start()
        self.admission = AdmissionDictFactory(self.person_information)
        self.addCleanup(self.files_list_patcher.stop)
        api_start_patcher(self)
        api_add_cleanup_patcher(self)

    @classmethod
    def setUpTestData(cls):
        current_acad_year = create_current_academic_year()
        cls.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)
        cls.request = RequestFactory()
        cls.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        cls.person = PersonFactory(user=cls.user)
        cls.person_information = ContinuingEducationPersonDictFactory(cls.person.uuid)
        cls.formation = ContinuingEducationTrainingDictFactory()
        cls.admission_submitted = AdmissionDictFactory(cls.person_information, SUBMITTED)
        api_create_patcher(cls)

    def test_admission_detail(self):
        self.mocked_get_admission.return_value = self.admission
        url = reverse('admission_detail', args=[self.admission['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')
        self.assertEqual(response.context['admission'], self.admission)
        self.assertTrue(response.context['admission_is_submittable'])

    def test_admission_detail_not_submittable(self):
        self.mocked_get_admission.return_value = self.admission
        self.admission['last_degree_level'] = ''

        url = reverse('admission_detail', args=[self.admission['uuid']])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

        self.assertEqual(response.context['admission'], self.admission)
        self.assertFalse(response.context['admission_is_submittable'])
        self.assertEqual(list(messages.get_messages(response.wsgi_request))[1].level, messages.WARNING)
        messages_list = [item.message for item in messages.get_messages(response.wsgi_request)]
        self.assertEqual(len(messages_list), 2)
        self.assertIn(
            gettext("Your file is not submittable because you did not provide the following data : "),
            str(messages_list)
        )
        self.assertIn(
            gettext("Last degree level"),
            str(messages_list)
        )

    def test_admission_submitted_detail(self):
        self.mocked_get_admission.return_value = self.admission_submitted
        url = reverse('admission_detail', args=[self.admission_submitted['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

        self.assertEqual(response.context['admission'], self.admission_submitted)
        self.assertFalse(response.context['admission_is_submittable'])

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        mails = _get_managers_mails(self.admission_submitted['formation'])
        self.assertIn(
            gettext("If you want to edit again your admission, please contact the program manager : %(mail)s")
            % {'mail': mails},
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.WARNING)

    def test_admission_submit(self):
        self.admission['state'] = admission_state_choices.DRAFT
        url = reverse('admission_submit')
        response = self.client.post(
            url,
            follow=True,
            data={
                "submit": True,
                "admission_uuid": self.admission['uuid']
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

    def test_admission_submit_not_draft(self):
        self.mocked_get_admission.return_value = self.admission_submitted
        url = reverse('admission_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_id": self.admission_submitted['uuid']
            }
        )
        self.assertEqual(response.status_code, 302)

    def test_admission_submit_not_complete(self):
        self.admission['last_degree_level'] = ''

        url = reverse('admission_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_uuid": self.admission['uuid']
            }
        )
        self.assertEqual(response.status_code, 302)

    def test_admission_new(self):
        url = reverse('admission_new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

        # info message should be displayed
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)

    def test_admission_new_save(self):
        admission = {
            'birth_country': 'BE',
            'birth_date_day': '18',
            'birth_date_month': '4',
            'birth_date_year': '1992',
            'birth_location': 'Bruxelles',
            'email': 'firstname@lastname.be',
            'first_name': 'Firstname',
            'formation': self.formation['uuid'],
            'gender': 'M',
            'last_name': 'Lastname',
            'state': 'Draft'
        }
        mocked_admission_uuid = self.mocked_get_admission.return_value['uuid']
        self.mocked_post_admission.return_value['uuid'] = mocked_admission_uuid
        response = self.client.post(reverse('admission_new'), data=admission)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admission_detail', args=[mocked_admission_uuid]))

    def test_admission_save_with_error(self):
        admission = AdmissionDictFactory(self.person_information)
        admission['person_information'] = "no valid pk"
        response = self.client.post(reverse('admission_new'), data=admission)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

    def test_edit_get_admission_found_complete(self):
        self.mocked_get_admission.return_value = self.admission
        url = reverse('admission_edit', args=[self.admission['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')
        # No warning message should be displayed
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 0)

    def test_edit_get_admission_found_incomplete(self):
        self.admission['last_degree_level'] = ''
        self.mocked_get_admission.return_value = self.admission
        url = reverse('admission_edit', args=[self.admission['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

        # A warning message should be displayed
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn(
            gettext("Your file is not submittable because you did not provide the following data : "),
            str(messages_list[0])
        )
        self.assertIn(
            gettext("Last degree level"),
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.WARNING)

    def test_admission_edit_permission_denied_invalid_state(self):
        self.mocked_get_admission.return_value = self.admission_submitted
        url = reverse('admission_edit', args=[self.admission_submitted['uuid']])
        request = self.request.get(url)
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            admission_form(request, self.admission_submitted['uuid'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_edit_post_admission_found(self):
        self.mocked_get_admission.return_value = self.admission
        person_information = self.admission['person_information']
        person = {
            'first_name': self.person.first_name,
            'last_name': self.person.last_name,
            'gender': self.person.gender,
            'birth_country': person_information['birth_country'],
            'birth_location': person_information['birth_location'],
            'birth_date': person_information['birth_date'],
        }
        admission = {
            'formation': self.formation['uuid'],
        }
        url = reverse('admission_edit', args=[self.admission['uuid']])
        response = self.client.post(url, data={**person, **admission})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission['uuid']]))

    def test_edit_post_admission_found_no_reg(self):
        admission_no_reg = AdmissionDictFactory(
            person_information=self.person_information,
            state=admission_state_choices.DRAFT,
            formation=ContinuingEducationTrainingDictFactory(active=True, registration_required=False)
        )
        self.mocked_get_admission.return_value = admission_no_reg
        self.mocked_get_continuing_education_training.return_value = admission_no_reg['formation']
        person_information = self.admission['person_information']
        person = {
            'first_name': self.person.first_name,
            'last_name': self.person.last_name,
            'gender': self.person.gender,
            'birth_country': person_information['birth_country'],
            'birth_location': person_information['birth_location'],
            'birth_date': person_information['birth_date'],
        }
        admission = {
            'formation': admission_no_reg['formation']['uuid'],
        }
        url = reverse('admission_edit', args=[admission_no_reg['uuid']])
        response = self.client.post(url, data={**person, **admission})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admission_detail', args=[admission_no_reg['uuid']]))

    @mock.patch('continuing_education.views.admission._get_files_list')
    def test_admission_detail_files_list(self, mock_get_files_list):
        self.mocked_get_admission.return_value = self.admission
        file = {
            'name': 'file.txt',
            'size': 123000,
            'created_date': datetime.date.today(),
            'uploaded_by': {
                'first_name': 'Test',
                'last_name': 'Test',
                'username': 'Test',
                'is_deletable': True
            },
            'uuid': str(uuid.uuid4()),
        }
        mock_get_files_list.return_value = [file]
        url = reverse('admission_detail', args=[self.admission['uuid']])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

        self.assertEqual(response.context['admission'], self.admission)
        self.assertEqual(response.context['list_files'], [file])

    @mock.patch('continuing_education.views.admission.get_continuing_education_training')
    def test_ajax_get_formation_information(self, mock_get_training):
        mock_get_training.return_value = {
            'additional_information_label': 'additional_information',
            'registration_required': True
        }
        response = self.client.get(reverse('get_formation_information'), data={
            'formation_uuid': self.formation['uuid']
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                'additional_information_label': '<p>additional_information</p>',
                'registration_required': True
            }
        )

    def test_accepted_admission_detail_no_registration_required(self):
        self.mocked_get_admission.return_value['state'] = ACCEPTED_NO_REGISTRATION_REQUIRED
        url = reverse('admission_detail', args=[self.admission['uuid']])
        response = self.client.get(url)
        self.assertEqual(response.context['admission']['state'], ACCEPTED)


class AdmissionSubmissionErrorsTestCase(TestCase):
    def setUp(self):
        person_iufc = ContinuingEducationPersonDictFactory(PersonFactory().uuid)
        self.admission = AdmissionDictFactory(person_iufc, SUBMITTED)

    @classmethod
    def setUpTestData(cls):
        current_acad_year = create_current_academic_year()
        cls.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)
        cls.person_iufc = ContinuingEducationPersonDictFactory(PersonFactory().uuid)

    def test_admission_is_submittable(self):
        errors, errors_fields = get_submission_errors(self.admission)
        self.assertFalse(
            errors
        )

    def test_admission_is_not_submittable_missing_data_in_all_objects(self):
        self.admission['person_information']['person']['email'] = ''
        self.admission['address']['postal_code'] = ''
        self.admission['last_degree_level'] = ''
        errors, errors_fields = get_submission_errors(self.admission)
        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
                _("Last degree level"): [_("This field is required.")]
            }
        )

    def test_admission_is_not_submittable_missing_admission_data(self):
        self.admission['last_degree_level'] = ''
        errors, errors_fields = get_submission_errors(self.admission)
        self.assertDictEqual(
            errors,
            {
                _("Last degree level"): [_("This field is required.")]
            }
        )

    def test_admission_is_not_submittable_missing_address_data(self):
        self.admission['address']['postal_code'] = ''
        errors, errors_fields = get_submission_errors(self.admission)
        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
            }
        )

    def test_admission_is_not_submittable_wrong_phone_format(self):
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
            self.admission['phone_mobile'] = number
            errors, errors_fields = get_submission_errors(self.admission)
            self.assertDictEqual(
                errors,
                {
                    _("Phone mobile"): [
                        _("Phone number must start with 0 or 00 or '+' followed by at least "
                          "7 digits and up to 15 digits.")
                    ],
                }
            )
