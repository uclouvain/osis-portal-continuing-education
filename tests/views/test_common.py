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

from collections import OrderedDict

from django.test import TestCase
from django.test.utils import override_settings
from continuing_education.views.common import _build_error_data, ONE_OF_THE_NEEDED_FIELD_BEFORE_SUBMISSION


A_FORM_FIELD = 'anything_else'
OTHER_FORM_FIELD = 'other_field'

A_FORM_FIELD_LABEL = "Anything else"
OTHER_FIELD_LABEL = 'Other field'


class CommonViewTestCase(TestCase):

    def test_build_warning_from_errors_dict(self):

        errors_dict = OrderedDict([(A_FORM_FIELD_LABEL, [A_FORM_FIELD]),
                                   (OTHER_FIELD_LABEL, [OTHER_FORM_FIELD])]
                                  )

        self.assertCountEqual(
            _build_error_data(errors_dict),
                              ['Anything else', OTHER_FIELD_LABEL]
        )

    @override_settings(LANGUAGES=[('en', 'English'), ], LANGUAGE_CODE='en')
    def test_build_warning_from_errors_dict_special_at_least_one_of_three_field_needed(self):
        errors_dict = OrderedDict([('National registry number', [ONE_OF_THE_NEEDED_FIELD_BEFORE_SUBMISSION]),
                                   (OTHER_FIELD_LABEL, [OTHER_FORM_FIELD])]
                                  )
        self.assertCountEqual(
            _build_error_data(errors_dict),
            [
                OTHER_FIELD_LABEL,
                'At least one of the 3 following fields must be filled-in : national registry, id card number or '
                'passport number'
            ]
        )
