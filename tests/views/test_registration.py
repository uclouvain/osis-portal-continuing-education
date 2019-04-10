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
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.translation import ugettext, ugettext_lazy as _, gettext
from requests import Response

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.admission_state_choices import REGISTRATION_SUBMITTED, ACCEPTED, REJECTED
from continuing_education.tests.factories.admission import RegistrationDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory
from continuing_education.views.common import get_submission_errors, _get_managers_mails


class ViewStudentRegistrationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        self.person = PersonFactory(user=self.user)
        self.person_information = ContinuingEducationPersonDictFactory(self.person.uuid)
        self.admission_accepted = RegistrationDictFactory(self.person_information, state=ACCEPTED)
        self.admission_rejected = RegistrationDictFactory(self.person_information, state=REJECTED)
        self.registration_submitted = RegistrationDictFactory(self.person_information, state=REGISTRATION_SUBMITTED)

        self.patcher = patch(
            "continuing_education.views.registration._get_files_list",
            return_value=Response()
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
            ugettext("Your registration file has been saved. Please consider the following information :"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("You are still able to edit the form"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("You can upload documents via the 'Documents'"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("Do not forget to submit your file when it is complete"),
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.INFO)

    def test_registration_detail_not_submittable(self):
        self.admission_accepted['national_registry_number'] = ''

        url = reverse('registration_detail', args=[self.admission_accepted['uuid']])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_detail.html')

        self.assertEqual(response.context['admission'], self.admission_accepted)
        self.assertFalse(response.context['registration_is_submittable'])

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 2)

        self.assertIn(
            ugettext("Your registration file has been saved. Please consider the following information :"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("You are still able to edit the form"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("You can upload documents via the 'Documents'"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("Do not forget to submit your file when it is complete"),
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.INFO)

        self.assertIn(
            ugettext("Your file is not submittable because you did not provide the following data : "),
            str(messages_list[1])
        )
        self.assertIn(
            ugettext("National registry number"),
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
            ugettext("Your registration is submitted. Some tasks are remaining to complete the registration :"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("Print the completed registration form"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext("Sign it and send it by post to the address of the program manager"),
            str(messages_list[0])
        )
        self.assertIn(
            ugettext(
                "Accompanied by two passport photos and a copy of both sides of the identity card or residence permit."
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
        self.admission_accepted['national_registry_number'] = ''

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

    def test_pdf_content(self):
        self.mocked_called_api_function_get.return_value = self.registration_submitted
        a_superuser = SuperUserFactory()
        self.client.force_login(a_superuser)
        url = reverse('registration_pdf', args=[self.registration_submitted['uuid']])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'registration_pdf.html')


class RegistrationSubmissionErrorsTestCase(TestCase):
    def setUp(self):
        ac = AcademicYearFactory()
        AcademicYearFactory(year=ac.year+1)
        self.admission = RegistrationDictFactory(PersonFactory().uuid)

    def test_registration_is_submittable(self):
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertFalse(
            errors
        )

    def test_registration_is_not_submittable_missing_data_in_all_objects(self):
        self.admission['residence_address']['postal_code'] = ''
        self.admission['billing_address']['postal_code'] = ''
        self.admission['national_registry_number'] = ''
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
                _("Postal code"): [_("This field is required.")],
                _("National registry number"): [_("This field is required.")]
            }
        )

    def test_registration_is_not_submittable_missing_registration_data(self):
        self.admission['national_registry_number'] = ''
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("National registry number"): [_("This field is required.")]
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
