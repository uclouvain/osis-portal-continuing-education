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
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django_registration.forms import RegistrationForm

from continuing_education.tests.factories.person import ContinuingEducationPersonFactory
from continuing_education.views.account_activation import ContinuingEducationRegistrationView


class ViewAccountActivationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)

    def test_register(self):
        self.request = RequestFactory().post(reverse('django_registration_register'))
        self.registration_view = ContinuingEducationRegistrationView(request=self.request)
        form = RegistrationForm(data={
            'email': 'efef@efef.com',
            'password1': 'efef',
            'password2': 'efef',
            'username': 'efef'
        })
        user_registered = ContinuingEducationRegistrationView.register(self.registration_view, form)
        self.assertIsInstance(user_registered, User)
        self.assertEqual(user_registered.is_active, False)

    def test_complete_account_registration_get(self):
        url = reverse('complete_account_registration')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_registration/complete_account_registration.html')

    def test_complete_account_registration_post_successful(self):
        url = reverse('complete_account_registration')
        person = ContinuingEducationPersonFactory()
        response = self.client.post(url, data ={
            'first_name': 'ghy',
            'gender': 'M',
            'activity_sector': 'PRIVATE',
            'address': person.address_id,
            'birth_country': person.birth_country_id,
            'citizenship': person.citizenship_id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('continuing_education_home'))

    def test_complete_account_registration_post_failed(self):
        url = reverse('complete_account_registration')
        person = ContinuingEducationPersonFactory()
        response = self.client.post(url, data={
            'first_name': 'ghy',
            'gender': 'M',
            'activity_sector': 'PRIVATE',
            'birth_country': person.birth_country_id,
            'citizenship': person.citizenship_id,
            'address': 'no_valid_address'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_registration/complete_account_registration.html')
