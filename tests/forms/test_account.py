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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from continuing_education.forms.account import ContinuingEducationRegistrationForm


class TestContinuingEducationRegistrationForm(TestCase):
    def test_valid_form(self):
        form = ContinuingEducationRegistrationForm(data={
            'password1': 'eheqneqrnherqner',
            'email': 'aaaa@bbbb.be',
            'username': 'aaaa@bbbb.be',
            'password2': 'eheqneqrnherqner'
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_with_uclouvain_mail_is_not_valid(self):
        form = ContinuingEducationRegistrationForm(data={
            'password1': 'eheqneqrnherqner',
            'email': 'aaaa@uclouvain.be',
            'username': 'aaaa@bbbb.be',
            'password2': 'eheqneqrnherqner'
        })
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(
            {'email': [_("Your email cannot end with uclouvain.be")]},
            form.errors
        )
