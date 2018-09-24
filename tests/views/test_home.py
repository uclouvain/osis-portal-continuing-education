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
from random import choice
from string import ascii_lowercase
from unittest import mock

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

class ViewHomeTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        self.client.force_login(self.user)

    def test_main_view(self):
        url = reverse('continuing_education_home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'continuing_education/home.html')

class FormationsListTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')

    @mock.patch('continuing_education.views.home._fetch_example_data')
    def test_sorted_formations_list(self, mock_fetch_example_data):
        mock_fetch_example_data.return_value = [{
            'acronym': ''.join([choice(ascii_lowercase) for _ in range(4)]),
            'title': 'title-{}'.format(i)
        } for i in range(11)]
        sorted_formations = sorted(mock_fetch_example_data.return_value, key=lambda k: k['acronym'])
        url = reverse('formations_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['formations'].paginator.num_pages, 2)
        self.assertEqual(response.context['formations'].object_list, sorted_formations[:10])
        self.assertTemplateUsed(response, 'continuing_education/formations.html')

    def test_bypass_formations_list_when_logged_in(self):
        self.client.force_login(self.user)
        url = reverse('formations_list')
        response = self.client.get(url)
        self.assertTrue(self.user.is_authenticated)
        self.assertRedirects(response, "/continuing_education/home/")