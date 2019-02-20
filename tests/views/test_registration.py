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

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import model_to_dict
from django.test import TestCase
from django.utils.translation import ugettext, ugettext_lazy as _
from requests import Response

from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.admission_state_choices import REGISTRATION_SUBMITTED
from continuing_education.tests.factories.admission import AdmissionFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonFactory
from continuing_education.views.common import get_submission_errors


class ViewStudentRegistrationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        self.person = PersonFactory(user=self.user)
        self.person_information = ContinuingEducationPersonFactory(person=self.person)
        self.admission_accepted = AdmissionFactory(
            state="Accepted",
            person_information=self.person_information
        )
        self.admission_rejected = AdmissionFactory(
            state="Rejected",
            person_information=self.person_information
        )
        self.registration_submitted = AdmissionFactory(
            state="Registration submitted",
            person_information=self.person_information
        )

        self.patcher = patch(
            "continuing_education.views.registration._get_files_list",
            return_value=Response()
        )
        self.mocked_called_api_function = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_registration_detail(self):
        url = reverse('registration_detail', args=[self.admission_accepted.id])
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
        self.admission_accepted.national_registry_number = ''
        self.admission_accepted.save()

        url = reverse('registration_detail', args=[self.admission_accepted.pk])
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
        url = reverse('registration_detail', args=[self.registration_submitted.pk])
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
        self.assertEqual(messages_list[0].level, messages.INFO)
        self.assertIn(
            ugettext("If you want to edit again your registration, please contact the program manager."),
            str(messages_list[1])
        )
        self.assertEqual(messages_list[1].level, messages.WARNING)

    def test_registration_detail_not_found(self):
        response = self.client.get(reverse('registration_detail', kwargs={
            'admission_id': 0,
        }))
        self.assertEqual(response.status_code, 404)

    def test_registration_submit(self):
        url = reverse('registration_submit')
        response = self.client.post(
            url,
            follow=True,
            data={
                "submit": True,
                "admission_id": self.admission_accepted.pk
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].state, admission_state_choices.REGISTRATION_SUBMITTED)
        self.assertTemplateUsed(response, 'registration_detail.html')

    def test_registration_submit_not_registration_submitted(self):
        url = reverse('registration_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_id": self.registration_submitted.pk
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_registration_submit_not_complete(self):
        self.admission_accepted.national_registry_number = ''
        self.admission_accepted.save()

        url = reverse('registration_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_id": self.admission_accepted.pk
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_registration_edit_not_found(self):
        response = self.client.get(reverse('registration_edit', kwargs={
            'admission_id': 0,
        }))
        self.assertEqual(response.status_code, 404)

    def test_edit_get_registration_found(self):
        url = reverse('registration_edit', args=[self.admission_accepted.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_form.html')

    def test_edit_post_registration_with_error(self):
        registration = model_to_dict(self.admission_accepted)
        registration['billing_address'] = "no valid pk"
        response = self.client.post(reverse('registration_edit', args=[self.admission_accepted.pk]),
                                    data=registration)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_form.html')

    def test_edit_post_registration_found(self):
        registration = {
            'previous_ucl_registration': False,
            'children_number': 2,
            'company_number': '1-61667-638-8',
            'head_office_name': 'Campbell-Tanner',
            'registration_type': 'PRIVATE',
            'state': 'Accepted',
            'use_address_for_billing': True,
        }
        url = reverse('registration_edit', args=[self.admission_accepted.pk])
        response = self.client.post(url, data=registration)
        self.assertRedirects(response, reverse('registration_detail', args=[self.admission_accepted.id]))
        self.admission_accepted.refresh_from_db()

        # verifying that fields are correctly updated
        for key in registration:
            if key in model_to_dict(self.admission_accepted):
                field_value = self.admission_accepted.__getattribute__(key)
                if isinstance(field_value, models.Model):
                    field_value = field_value.pk
                self.assertEqual(field_value, registration[key], key)

    def test_edit_post_registration_found_with_other_address(self):
        registration = {
            'previous_ucl_registration': False,
            'use_address_for_billing': False,
            'billing-city': 'Brux-city'
        }
        url = reverse('registration_edit', args=[self.admission_accepted.pk])
        response = self.client.post(url, data=registration)
        self.assertRedirects(response, reverse('registration_detail', args=[self.admission_accepted.id]))
        self.admission_accepted.refresh_from_db()
        self.admission_accepted.billing_address.refresh_from_db()

        field_value = self.admission_accepted.billing_address.__getattribute__('city')
        self.assertEqual(field_value, registration['billing-city'])

    def test_edit_registration_submitted_error(self):
        self.admission_accepted.state = REGISTRATION_SUBMITTED
        self.admission_accepted.save()
        url = reverse('registration_edit', args=[self.admission_accepted.id])
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 404)
        self.assertTemplateUsed(get_response, 'page_not_found.html')

        post_response = self.client.post(url)
        self.assertEqual(post_response.status_code, 404)
        self.assertTemplateUsed(post_response, 'page_not_found.html')


class RegistrationSubmissionErrorsTestCase(TestCase):
    def setUp(self):
        ac = AcademicYearFactory()
        AcademicYearFactory(year=ac.year+1)
        self.admission = AdmissionFactory(
            formation=EducationGroupYearFactory(
                academic_year=ac,
                education_group_type__category=education_group_categories.TRAINING
            )
        )

    def test_registration_is_submittable(self):
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertFalse(
            errors
        )

    def test_registration_is_not_submittable_missing_data_in_all_objects(self):
        self.admission.residence_address.postal_code = ''
        self.admission.residence_address.save()
        self.admission.billing_address.postal_code = ''
        self.admission.billing_address.save()
        self.admission.national_registry_number = ''
        self.admission.save()
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
        self.admission.national_registry_number = ''
        self.admission.save()
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("National registry number"): [_("This field is required.")]
            }
        )

    def test_registration_is_not_submittable_missing_address_data(self):
        self.admission.billing_address.postal_code = ''
        self.admission.billing_address.save()
        errors, errors_fields = get_submission_errors(self.admission, is_registration=True)

        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
            }
        )
