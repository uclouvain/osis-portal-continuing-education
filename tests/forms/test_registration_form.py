##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from continuing_education.forms.registration import RegistrationForm
from continuing_education.tests.factories.admission import AdmissionDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory


class TestRegistrationForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        base_person = PersonFactory()
        cls.person = ContinuingEducationPersonDictFactory(person_uuid=base_person.uuid)
        cls.formation = ContinuingEducationTrainingDictFactory()

    def test_previous_ucl_registration_not_required_if_only_billing(self):
        registration = AdmissionDictFactory(person_information=self.person, formation=self.formation)
        form = RegistrationForm(data=registration, only_billing=True)
        self.assertFalse(form.fields['previous_ucl_registration'].required)
