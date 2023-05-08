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
from continuing_education.forms.admission import AdmissionForm
from continuing_education.models.enums.admission_state_choices import ACCEPTED
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory


class TestAdmissionForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.iufc_person = ContinuingEducationPersonDictFactory(cls.person.uuid)

    def test_valid_form(self):
        admission = AdmissionDictFactory(self.iufc_person)
        form = AdmissionForm(admission)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_student_state(self):
        admission = AdmissionDictFactory(self.iufc_person, state=ACCEPTED)
        form = AdmissionForm(admission)
        self.assertFalse(form.is_valid(), form.errors)

    def test_valid_form_email_field(self):
        self.person.user.email = "test@osis.be"
        self.person.user.save()
        admission = AdmissionDictFactory(self.iufc_person)
        form = AdmissionForm(admission, user=self.person.user)
        self.assertEqual(
            form.fields['email'].initial,
            "test@osis.be"
        )
        self.assertTrue(
            form.fields['email'].required
        )
