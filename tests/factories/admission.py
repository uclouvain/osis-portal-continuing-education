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
import random
import uuid

import factory
import factory.fuzzy

from continuing_education.models.enums import enums
from continuing_education.models.enums.admission_state_choices import DRAFT, ACCEPTED
from continuing_education.models.enums.enums import get_enum_keys
from continuing_education.tests.factories.address import AddressDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory

factory.Faker._DEFAULT_LOCALE = 'nl_BE'
CONTINUING_EDUCATION_TYPE = 8


def AdmissionDictFactory(person_information, state=DRAFT):
    admission = {
        'uuid': str(uuid.uuid4()),
        'person_information': person_information,
        'address': AddressDictFactory(),
        'last_degree_level': "level",
        'formation': ContinuingEducationTrainingDictFactory(),
        'citizenship': {
            'name': str(factory.Sequence(lambda n: 'Country - %d' % n)),
            'iso_code': factory.Sequence(lambda n: str(n)[-2:])
        },
        'phone_mobile': _get_fake_phone_number(),
        'email': person_information['person']['email'],
        'high_school_diploma': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'last_degree_field': 'field',
        'last_degree_institution': 'institution',
        'last_degree_graduation_year': factory.fuzzy.FuzzyInteger(1991, 2018).fuzz(),
        'professional_status': factory.fuzzy.FuzzyChoice(get_enum_keys(enums.STATUS_CHOICES)).fuzz(),
        'current_occupation': factory.Faker('text', max_nb_chars=50),
        'current_employer': factory.Faker('company'),
        'activity_sector': factory.fuzzy.FuzzyChoice(get_enum_keys(enums.SECTOR_CHOICES)).fuzz(),
        'motivation': 'motivation',
        'professional_personal_interests': 'professional impact',
        'state': state,
        'registration_type': factory.fuzzy.FuzzyChoice(get_enum_keys(enums.REGISTRATION_TITLE_CHOICES)).fuzz(),
        'use_address_for_billing': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'billing_address': AddressDictFactory(),
        'head_office_name': factory.Faker('company'),
        'company_number': factory.Faker('isbn10'),
        'vat_number': factory.Faker('ssn'),
    }
    return admission


def _get_fake_phone_number():
    fake = factory.Faker('phone_number').generate(extra_kwargs={})
    for c in [" ", "(", ")", "-"]:
        fake = fake.replace(c, "")
    return fake


def RegistrationDictFactory(person_information, state=ACCEPTED, formation=None):
    registration = {
        'uuid': str(uuid.uuid4()),
        'formation': formation if formation else ContinuingEducationTrainingDictFactory(),
        'person_information': person_information,
        'address': AddressDictFactory(),
        'registration_type': factory.fuzzy.FuzzyChoice(get_enum_keys(enums.REGISTRATION_TITLE_CHOICES)).fuzz(),
        'use_address_for_billing': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'billing_address': AddressDictFactory(),
        'head_office_name': factory.Faker('company'),
        'company_number': factory.Faker('isbn10'),
        'vat_number': factory.Faker('ssn'),
        'national_registry_number': factory.Faker('ssn'),
        'id_card_number': factory.Faker('ssn'),
        'passport_number': factory.Faker('isbn13'),
        'marital_status': factory.fuzzy.FuzzyChoice(get_enum_keys(enums.MARITAL_STATUS_CHOICES)).fuzz(),
        'spouse_name': factory.Faker('name'),
        'children_number': random.randint(0, 10),
        'previous_ucl_registration': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'previous_noma': factory.Faker('isbn10'),
        'use_address_for_post': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'residence_address': AddressDictFactory(),
        'residence_phone': _get_fake_phone_number(),
        'ucl_registration_complete': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'noma': factory.Faker('isbn10'),
        'payment_complete': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'formation_spreading': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'prior_experience_validation': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'assessment_presented': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'assessment_succeeded': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
        'sessions': 'Test',
        'state': state,
        'reduced_rates': False,
        'spreading_payments': False,
        'citizenship': {
            'name': str(factory.Sequence(lambda n: 'Country - %d' % n)),
            'iso_code': factory.Sequence(lambda n: str(n)[-2:])
        },
    }
    return registration
