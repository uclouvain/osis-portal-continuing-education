##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from continuing_education.models import admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.enums import get_enum_keys
from continuing_education.tests.factories.admission import AdmissionFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonFactory


class TestAdmission(TestCase):
    def setUp(self):
        self.admission = AdmissionFactory()
        self.person = ContinuingEducationPersonFactory()

    def test_find_by_id(self):
        an_admission = self.admission
        persisted_admission = admission.find_by_id(an_admission.id)
        self.assertEqual(an_admission.id, persisted_admission.id)

        nonexistent_admission = admission.find_by_id(0)
        self.assertIsNone(nonexistent_admission)

    def test_search(self):
        an_admission = self.admission
        persisted_admission = admission.search(person=an_admission.person_information)
        self.assertTrue(persisted_admission.exists())

        nonexistent_admission = admission.search(person=self.person)
        self.assertFalse(nonexistent_admission.exists())

    def test_submit_ok(self):
        an_admission = self.admission
        an_admission.state = admission_state_choices.DRAFT
        an_admission.save()
        an_admission.submit()
        self.assertEqual(
            an_admission.state,
            admission_state_choices.SUBMITTED
        )

    def test_submit_nok_incorrect_origin_state(self):
        an_admission = self.admission

        all_states = get_enum_keys(admission_state_choices.STATE_CHOICES)
        permitted_origin_states_to_submit = [admission_state_choices.DRAFT]
        forbidden_origin_states_to_submit = get_differences_between_lists(all_states, permitted_origin_states_to_submit)

        for forbidden_state in forbidden_origin_states_to_submit:
            with self.subTest(forbidden_state=forbidden_state):
                an_admission.state = forbidden_state
                an_admission.save()

                with self.assertRaisesMessage(PermissionDenied, 'To submit an admission, its state must be DRAFT.'):
                    an_admission.submit()

                self.assertEqual(
                    an_admission.state,
                    forbidden_state
                )


def get_differences_between_lists(all_states, permitted_origin_states_to_submit):
    return list(set(all_states) - set(permitted_origin_states_to_submit))
