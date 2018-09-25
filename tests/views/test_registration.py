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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import model_to_dict
from django.test import TestCase

from continuing_education.tests.factories.address import AddressFactory
from continuing_education.tests.factories.admission import AdmissionFactory


class ViewStudentRegistrationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)
        self.admission_accepted = AdmissionFactory(state="accepted")
        self.admission_rejected = AdmissionFactory(state="rejected")

    def test_registration_detail(self):
        url = reverse('registration_detail', args=[self.admission_accepted.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration_detail.html')

    def test_registration_detail_not_found(self):
        response = self.client.get(reverse('registration_detail', kwargs={
            'admission_id': 0,
        }))
        self.assertEqual(response.status_code, 404)

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
        address = AddressFactory()
        registration = {
            'previous_ucl_registration': False,
            'children_number': 2,
            'company_number': '1-61667-638-8',
            'head_office_name': 'Campbell-Tanner',
            'registration_type': 'PRIVATE',
            'state': 'accepted',
            'billing_address': address.pk,
            'billing-location' : address.location,
            'billing-postal_code' : address.postal_code,
            'billing-city': address.city,
            'billing-country': address.country.pk,
            'residence_address': address.pk,
            'residence-location': address.location,
            'residence-postal_code': address.postal_code,
            'residence-city': address.city,
            'residence-country': address.country.pk,
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
