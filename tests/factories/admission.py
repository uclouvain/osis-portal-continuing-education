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
import datetime
import uuid

import factory

from continuing_education.models.enums.admission_state_choices import DRAFT, ACCEPTED

CONTINUING_EDUCATION_TYPE = 8


def AdmissionDictFactory(person_uuid, state=DRAFT):
    admission = {
        'uuid': str(uuid.uuid4()),
        'person_information': {
            'person': {
                'uuid': str(person_uuid),
                'email': 'a@b.de',
                'first_name': 'Ben',
                'last_name': 'Dau',
                'gender': 'M'
            },
            'birth_country': factory.Sequence(lambda n: 'Country - %d' % n),
            'birth_location': 'ABCCity',
            'birth_date': factory.fuzzy.FuzzyDate(datetime.date(1950, 1, 1)).fuzz()
        },
        'address': {
            'location': factory.Faker('street_name'),
            'postal_code': 1348,
            'country': factory.Sequence(lambda n: 'Country - %d' % n),
            'city': factory.Faker('city')
        },
        'last_degree_level': 'ACV',
        'formation': {
            'acronym': 'ABUS1FP',
        },
        'citizenship': factory.Sequence(lambda n: 'Country - %d' % n),
        'phone_mobile': 1234567890,
        'email': 'a@b.de',
        'high_school_diploma': True,
        'last_degree_field': 'BBB',
        'last_degree_institution': 'CCC',
        'last_degree_graduation_year': 2016,
        'professional_status': 'EMPLOYEE',
        'current_occupation': 'FFF',
        'current_employer': 'GGG',
        'activity_sector': 'PRIVATE',
        'motivation': 'III',
        'professional_impact': 'KKK',
        'state': state
    }
    return admission


def RegistrationDictFactory(person_uuid, state=ACCEPTED):
    registration = {
        'uuid': str(uuid.uuid4()),
        'formation': {
            'acronym': 'ABUS1FP',
        },
        'person_information': {
            'person': {
                'uuid': str(person_uuid),
                'email': 'a@b.de',
                'first_name': 'Ben',
                'last_name': 'Dau',
                'gender': 'M'
            },
            'birth_country': {
                'name': 'BElgique',
                'iso_code': 'BE'
            },
            'birth_location': 'ABCCity',
            'birth_date': factory.fuzzy.FuzzyDate(datetime.date(1950, 1, 1)).fuzz()
        },
        'address': {
            'location': factory.Faker('street_name'),
            'postal_code': 1348,
            'country': {
                'name': 'BElgique',
                'iso_code': 'BE'
            },
            'city': factory.Faker('city')
        },
        'registration_type': 'PRIVATE',
        'use_address_for_billing': True,
        'billing_address': {
            'location': factory.Faker('street_name'),
            'postal_code': 1348,
            'country': {
                'name': 'BElgique',
                'iso_code': 'BE'
            },
            'city': factory.Faker('city')
        },
        'head_office_name': 'TEST',
        'company_number': 123,
        'vat_number': 456,
        'national_registry_number': 789,
        'id_card_number': 123456,
        'passport_number': 456789,
        'marital_status': 'SINGLE',
        'spouse_name': 'Cara',
        'children_number': 2,
        'previous_ucl_registration': False,
        'previous_noma': '',
        'use_address_for_post': False,
        'residence_address': {
            'location': factory.Faker('street_name'),
            'postal_code': 1348,
            'country': {
                'name': 'BElgique',
                'iso_code': 'BE'
            },
            'city': factory.Faker('city')
        },
        'residence_phone': 145632,
        'ucl_registration_complete': False,
        'noma': 45117,
        'payment_complete': False,
        'formation_spreading': False,
        'prior_experience_validation': False,
        'assessment_presented': False,
        'assessment_succeeded': False,
        'sessions': 'Test',
        'state': state
    }
    return registration
