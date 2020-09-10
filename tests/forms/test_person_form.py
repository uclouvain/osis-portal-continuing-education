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

from base.tests.factories.person import PersonFactory
from continuing_education.forms.person import PersonForm
from continuing_education.tests.factories.person import PersonDictFactory


class TestPersonForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory(gender='F')

    def test_valid_form(self):
        person = PersonDictFactory(self.person)
        form = PersonForm(data=person, no_first_name_checked=False)
        self.assertTrue(form.is_valid(), form.errors)

    def test_no_first_name_form(self):
        person = PersonDictFactory(self.person)
        person.pop('first_name')
        form = PersonForm(data=person, no_first_name_checked=True)
        self.assertTrue(form.is_valid(), form.errors)
