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
from unittest import mock
from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import model_to_dict
from django.test import TestCase, RequestFactory
from django.utils.translation import ugettext_lazy as _, gettext
from requests import Response

from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from continuing_education.models.admission import Admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.tests.factories.admission import AdmissionFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonFactory
from continuing_education.views.admission import admission_form
from continuing_education.views.common import get_submission_errors


class ViewStudentAdmissionTestCase(TestCase):
    def setUp(self):
        current_acad_year = create_current_academic_year()
        self.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)

        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        self.request = RequestFactory()
        self.person = PersonFactory(user=self.user)
        self.person_information = ContinuingEducationPersonFactory(person=self.person)
        self.formation = EducationGroupYearFactory(academic_year=self.next_acad_year)
        self.admission = AdmissionFactory(
            person_information=self.person_information,
            state=admission_state_choices.DRAFT,
            formation=self.formation
        )
        self.admission_submitted = AdmissionFactory(
            person_information=self.person_information,
            state=admission_state_choices.SUBMITTED,
            formation=self.formation
        )
        self.patcher = patch(
            "continuing_education.views.admission._get_files_list",
            return_value=Response()
        )
        self.mocked_called_api_function = self.patcher.start()

        self.addCleanup(self.patcher.stop)

    def test_admission_detail(self):
        url = reverse('admission_detail', args=[self.admission.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

        self.assertEqual(response.context['admission'], self.admission)
        self.assertTrue(response.context['admission_is_submittable'])

    def test_admission_detail_not_submittable(self):
        self.admission.last_degree_level = ''
        self.admission.save()

        url = reverse('admission_detail', args=[self.admission.pk])
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
        url = reverse('admission_detail', args=[self.admission_submitted.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

        self.assertEqual(response.context['admission'], self.admission_submitted)
        self.assertFalse(response.context['admission_is_submittable'])

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)

        self.assertIn(
            gettext("If you want to edit again your admission, please contact the program manager."),
            str(messages_list[0])
        )
        self.assertEqual(messages_list[0].level, messages.WARNING)

    def test_admission_detail_not_found(self):
        response = self.client.get(reverse('admission_detail', kwargs={
            'admission_id': 0,
        }))
        self.assertEqual(response.status_code, 404)

    def test_admission_submit(self):
        self.admission.state = admission_state_choices.DRAFT
        self.admission.save()
        url = reverse('admission_submit')
        response = self.client.post(
            url,
            follow=True,
            data={
                "submit": True,
                "admission_id": self.admission.pk
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].state, admission_state_choices.SUBMITTED)
        self.assertTemplateUsed(response, 'admission_detail.html')

    def test_admission_submit_not_draft(self):
        url = reverse('admission_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_id": self.admission_submitted.pk
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_admission_submit_not_complete(self):
        self.admission.last_degree_level = ''
        self.admission.save()

        url = reverse('admission_submit')
        response = self.client.post(
            url,
            data={
                "submit": True,
                "admission_id": self.admission.pk
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_admission_detail_unauthorized(self):
        admission = AdmissionFactory()
        url = reverse('admission_detail', args=[admission.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_admission_new(self):
        url = reverse('admission_new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

        #info message should be displayed
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)

    def test_admission_new_save(self):
        admission = model_to_dict(self.admission)
        person = {
            'first_name': self.person.first_name,
            'last_name': self.person.last_name,
            'gender': self.person.gender,
            'birth_country': self.admission.person_information.birth_country.pk,
            'birth_location': self.admission.person_information.birth_location,
            'birth_date': self.admission.person_information.birth_date,
        }
        admission.update(person)
        response = self.client.post(reverse('admission_new'), data=admission)
        created_admission = Admission.objects.last()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admission_detail', args=[created_admission.pk]))

    def test_admission_save_with_error(self):
        admission = model_to_dict(AdmissionFactory(
            formation__academic_year=self.next_acad_year
        ))
        admission['person_information'] = "no valid pk"
        response = self.client.post(reverse('admission_new'), data=admission)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

    def test_admission_edit_not_found(self):
        response = self.client.get(reverse('admission_edit', kwargs={
            'admission_id': 0,
        }))
        self.assertEqual(response.status_code, 404)

    def test_admission_edit_unauthorized(self):
        admission = AdmissionFactory()
        url = reverse('admission_detail', args=[admission.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_get_admission_found_incomplete(self):
        self.admission.last_degree_level = ''
        self.admission.save()
        url = reverse('admission_edit', args=[self.admission.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

        #A warning message should be displayed
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

    def test_edit_get_admission_found_complete(self):
        url = reverse('admission_edit', args=[self.admission.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_form.html')

        # No warning message should be displayed
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 0)

    def test_admission_edit_permission_denied_invalid_state(self):
        url = reverse('admission_edit', args=[self.admission_submitted.pk])
        request = self.request.get(url)
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            admission_form(request, self.admission_submitted.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_edit_post_admission_found(self):
        person_information = self.admission.person_information
        person = {
            'first_name': self.person.first_name,
            'last_name': self.person.last_name,
            'gender': self.person.gender,
            'birth_country': person_information.birth_country.pk,
            'birth_location': person_information.birth_location,
            'birth_date': person_information.birth_date,
        }
        admission = {
            'person_information': person_information.pk,
            'motivation': 'abcd',
            'professional_impact': 'abcd',
            'formation': self.formation.pk,
            'awareness_ucl_website': True,
            'state': admission_state_choices.DRAFT
        }
        url = reverse('admission_edit', args=[self.admission.pk])
        data = person.copy()
        data.update(admission)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admission_detail', args=[self.admission.id]))
        self.admission.refresh_from_db()

        # verifying that fields are correctly updated
        for key in admission:
            field_value = self.admission.__getattribute__(key)
            if isinstance(field_value, datetime.date):
                field_value = field_value.strftime('%Y-%m-%d')
            if isinstance(field_value, models.Model):
                field_value = field_value.pk
            self.assertEqual(field_value, admission[key], key)

    @mock.patch('continuing_education.views.admission._get_files_list')
    def test_admission_detail_files_list(self, mock_get_files_list):
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
        }
        mock_get_files_list.return_value = [file]
        url = reverse('admission_detail', args=[self.admission.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admission_detail.html')

        self.assertEqual(response.context['admission'], self.admission)
        self.assertEqual(response.context['list_files'], [file])


class AdmissionSubmissionErrorsTestCase(TestCase):
    def setUp(self):
        current_acad_year = create_current_academic_year()
        self.next_acad_year = AcademicYearFactory(year=current_acad_year.year + 1)
        self.admission = AdmissionFactory(
            formation=EducationGroupYearFactory(academic_year=self.next_acad_year)
        )

    def test_admission_is_submittable(self):
        errors, errors_fields = get_submission_errors(self.admission)

        self.assertFalse(
            errors
        )

    def test_admission_is_not_submittable_missing_data_in_all_objects(self):
        self.admission.person_information.person.email = ''
        self.admission.person_information.person.save()
        self.admission.person_information.birth_country = None
        self.admission.person_information.save()
        self.admission.address.postal_code = ''
        self.admission.address.save()
        self.admission.last_degree_level = ''
        self.admission.save()
        errors, errors_fields = get_submission_errors(self.admission)

        self.assertDictEqual(
            errors,
            {
                _("Email"): [_("This field is required.")],
                _("Birth country"): [_("This field is required.")],
                _("Postal code"): [_("This field is required.")],
                _("Last degree level"): [_("This field is required.")]
            }
        )

    def test_admission_is_not_submittable_missing_admission_data(self):
        self.admission.last_degree_level = ''
        self.admission.save()
        errors, errors_fields = get_submission_errors(self.admission)

        self.assertDictEqual(
            errors,
            {
                _("Last degree level"): [_("This field is required.")]
            }
        )

    def test_admission_is_not_submittable_missing_person_information_data(self):
        self.admission.person_information.birth_country = None
        self.admission.person_information.save()
        errors, errors_fields = get_submission_errors(self.admission)

        self.assertDictEqual(
            errors,
            {
                _("Birth country"): [_("This field is required.")],
            }
        )

    def test_admission_is_not_submittable_missing_address_data(self):
        self.admission.address.postal_code = ''
        self.admission.address.save()
        errors, errors_fields = get_submission_errors(self.admission)

        self.assertDictEqual(
            errors,
            {
                _("Postal code"): [_("This field is required.")],
            }
        )

    def test_admission_is_not_submittable_missing_person_data(self):
        self.admission.person_information.person.gender = None
        self.admission.person_information.person.save()
        errors, errors_fields = get_submission_errors(self.admission)

        self.assertDictEqual(
            errors,
            {
                _("Gender"): [_("This field is required.")],
            }
        )
