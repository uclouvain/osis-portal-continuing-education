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

import factory.fuzzy

from base.models.person import Person
from reference.tests.factories.country import CountryFactory


def ContinuingEducationPersonDictFactory(person_uuid):
    person = Person.objects.get(uuid=person_uuid)
    person = {
        'uuid': str(uuid.uuid4()),
        'person': {
            'person_uuid': str(person_uuid),
            'email': person.email,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'gender': person.gender
        },
        'birth_country': CountryFactory().name,
        'birth_location': factory.Faker('city'),
        'birth_date': factory.fuzzy.FuzzyDate(datetime.date(1950, 1, 1)).fuzz()
    }
    return person
