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

import pdfrw
import random
from django.test import TestCase

from continuing_education.business import pdf_filler
from continuing_education.tests.factories.admission import RegistrationDictFactory
from continuing_education.models.enums.admission_state_choices import REGISTRATION_SUBMITTED
from base.tests.factories.person import PersonFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory

FORMATION_COUNTRY_NAME = 'Bangladesh'

FORMATION_CITY = 'Lisogne'

FORMATION_POSTAL_CODE = '5501'

FORMATION_LOCATION = 'rue dadada'

FIRST_MANAGER_LAST_NAME = 'De Grove'

FIRST_MANAGER_FIRST_NAME = 'Marc'


class PdfFillerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.data_dict_for_address = {
            'location': 'Rue de Bruxelles 22',
            'postal_code': '5000',
            'city': 'Namur',
            'country':
                {'name': 'Belgium'}
        }
        cls.data_dict_for_empty_address = {
            'location': pdf_filler.EMPTY_VALUE,
            'postal_code': pdf_filler.EMPTY_VALUE,
            'city': pdf_filler.EMPTY_VALUE,
            'country':
                {'name': pdf_filler.EMPTY_VALUE}
        }

        cls.default_keys_for_address = ['_address_location',
                                        '_address_postal_code',
                                        '_address_city',
                                        '_address_country'
                                        ]
        cls.formation_data_dict = {
            'managers': [
                {'first_name': FIRST_MANAGER_FIRST_NAME, 'last_name': FIRST_MANAGER_LAST_NAME},
                {'first_name': 'Ophélie', 'last_name': 'Goossens'},
                ],
            'postal_address': {'location': FORMATION_LOCATION,
                               'postal_code': FORMATION_POSTAL_CODE,
                               'city': FORMATION_CITY, 'country': {'name': FORMATION_COUNTRY_NAME}},
            }

    def test_checkbox_selection_status_is_selected(self):
        checkbox_status = pdf_filler._checkbox_selection_status("juste", "juste")
        self.assertIsInstance(checkbox_status, pdfrw.objects.pdfname.BasePdfName)
        self.assertEqual(checkbox_status, '/Yes')

    def test_checkbox_selection_status_not_selected(self):
        checkbox_status = pdf_filler._checkbox_selection_status("juste", "pas juste")
        self.assertIsInstance(checkbox_status, pdfrw.objects.pdfname.BasePdfName)
        self.assertEqual(checkbox_status, '/Off')

    def test_checkbox_selection_status_default(self):
        checkbox_status = pdf_filler._checkbox_selection_status(None, "juste?")
        self.assertIsInstance(checkbox_status, pdfrw.objects.pdfname.BasePdfName)
        self.assertEqual(checkbox_status, '/Off')

    def test_capitalize(self):
        self.assertEqual(pdf_filler._capitalize(None), pdf_filler.EMPTY_VALUE)
        self.assertEqual(pdf_filler._capitalize("coucou"), "Coucou")
        self.assertEqual(pdf_filler._capitalize("COUCOU"), "Coucou")
        self.assertEqual(pdf_filler._capitalize("Coucou"), "Coucou")

    def test_build_address_no_type(self):
        self.assertCountEqual(pdf_filler._build_address({}, None), {})

    def test_build_address_not_existing(self):
        type = 'contact'
        result = pdf_filler._build_address(self.data_dict_for_empty_address, type)
        for key in self.default_keys_for_address:
            self.assertEqual(result.get('{}{}'.format(type, key)), pdf_filler.EMPTY_VALUE)

    def test_build_address(self):
        type = 'contact'
        result = pdf_filler._build_address(self.data_dict_for_address, type)
        result.get('{}{}'.format(type, self.default_keys_for_address[0]), self.data_dict_for_address.get('location'))
        result.get('{}{}'.format(type, self.default_keys_for_address[1]), self.data_dict_for_address.get('postal_code'))
        result.get('{}{}'.format(type, self.default_keys_for_address[2]), self.data_dict_for_address.get('city'))
        result.get('{}{}'.format(type, self.default_keys_for_address[3]), self.data_dict_for_address.get('country'))

    def test_marital_status_dict_complete(self):
        results = pdf_filler._build_marital_status(random.choices(pdf_filler.MARITAL_STATUS))
        for status in pdf_filler.MARITAL_STATUS:
            self.assertIsNotNone(results["marital_{}_check".format(status.lower())])

    def test_build_professional_status_dict_complete(self):
        professional_status_available = ['JOB_SEEKER', 'EMPLOYEE', 'SELF_EMPLOYED', 'OTHER']
        results = pdf_filler._build_professional_status(random.choices(professional_status_available))
        keys_expected = [
                'employee_check',
                'self_employed_check',
                'job_seeker_check',
                'other_check',
                'seeking_job_on',
                'seeking_job_off']
        for key in keys_expected:
            self.assertIsNotNone(results[key])

    def test_build_manager_data_mandatory_keys(self):
        result_dict = pdf_filler._build_manager_data(self.formation_data_dict)

        keys_expected = [pdf_filler.MANAGER_NAME_KEY, pdf_filler.MANAGER_LOCATION_KEY,
                         pdf_filler.MANAGER_POSTAL_CODE_KEY, pdf_filler.MANAGER_CITY_KEY,
                         pdf_filler.MANAGER_COUNTRY_KEY]
        for key in keys_expected:
            self.assertTrue(key in result_dict)

    def test_build_manager_data(self):
        result_dict = pdf_filler._build_manager_data(self.formation_data_dict)
        self.assertEqual(result_dict[pdf_filler.MANAGER_NAME_KEY],
                         "{} {}".format(FIRST_MANAGER_FIRST_NAME, FIRST_MANAGER_LAST_NAME))
        self.assertEqual(result_dict[pdf_filler.MANAGER_LOCATION_KEY], FORMATION_LOCATION)
        self.assertEqual(result_dict[pdf_filler.MANAGER_POSTAL_CODE_KEY], FORMATION_POSTAL_CODE)
        self.assertEqual(result_dict[pdf_filler.MANAGER_COUNTRY_KEY], FORMATION_COUNTRY_NAME)

    def test_build_manager_no_postal_address(self):
        formation_input_data = self.formation_data_dict.copy()
        formation_input_data.pop('postal_address')

        result_dict = pdf_filler._build_manager_data(formation_input_data)

        self.assertEqual(result_dict[pdf_filler.MANAGER_LOCATION_KEY], '')
        self.assertEqual(result_dict[pdf_filler.MANAGER_POSTAL_CODE_KEY], '')
        self.assertEqual(result_dict[pdf_filler.MANAGER_COUNTRY_KEY], '')

    def test_build_manager_no_managers(self):
        formation_input_data = self.formation_data_dict.copy()
        formation_input_data.pop('managers')

        result_dict = pdf_filler._build_manager_data(formation_input_data)

        self.assertEqual(result_dict[pdf_filler.MANAGER_NAME_KEY], '')


class PdfFillerFieldsValuesTestCase(TestCase):

        @classmethod
        def setUpTestData(cls):
            cls.person = PersonFactory()
            cls.person_information = ContinuingEducationPersonDictFactory(cls.person.uuid)
            cls.registration = RegistrationDictFactory(person_information=cls.person_information,
                                                       state=REGISTRATION_SUBMITTED)
            cls.data = pdf_filler.get_data(cls.registration)


        def test_get_data_dict_complete(self):
            keys_expected = [
                'last_name', 'first_name', 'birth_date','birth_location', 'birth_country', 'citizenship',
                'national_registry_number', 'id_card_number', 'passport_number', 'gender_image_f', 'gender_image_m',
                'marital_single_check', 'marital_married_check', 'marital_widowed_check', 'marital_divorced_check',
                'marital_separated_check', 'marital_legal_cohabitant_check', 'spouse_name', 'children_number',
                'previous_noma', 'mobile', 'private_email', 'contact_address_location', 'contact_address_postal_code',
                'contact_address_city', 'contact_address_country', 'residence_address_location',
                'residence_address_postal_code', 'residence_address_city', 'residence_address_country',
                'residence_phone', 'receive_letter_at_home', 'receive_letter_at_residence', 'employee_check',
                'self_employed_check', 'job_seeker_check', 'other_check', 'seeking_job_on', 'seeking_job_off'
            ]
            for key in keys_expected:
                self.assertIsNotNone(self.data[key])
#

#
#
#
#
#
# def _build_manager_data(formation):
#     formation_postal_address = formation.get('postal_address')
#     return {
#         'manager_name': _get_one_manager(formation.get('managers')),
#         'manager_address_location': formation_postal_address.get('location', '') if formation_postal_address else '',
#         'manager_address_postal_code':
#             formation_postal_address.get('postal_code', '') if formation_postal_address else '',
#         'manager_address_city': formation_postal_address.get('city', '') if formation_postal_address else '',
#         'manager_address_country':
#             formation_postal_address.get('country', '').get('name', '') if formation_postal_address else ''
#     }
