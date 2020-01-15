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
from django.test import TestCase

from continuing_education.business import pdf_filler


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

    def test_build_address_inexisting(self):
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
