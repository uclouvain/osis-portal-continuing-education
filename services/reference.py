###############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
###############################################################################
import logging
from typing import List

import urllib3
from django.conf import settings
from osis_reference_sdk import ApiClient
from osis_reference_sdk.api import cities_api

from base.models.person import Person
from frontoffice.settings.osis_sdk import reference as reference_sdk

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class CitiesService:
    @staticmethod
    def get_cities(person: Person, **kwargs) -> List:
        configuration = reference_sdk.build_configuration_for_continuing_education(person)
        api_instance = cities_api.CitiesApi(ApiClient(configuration=configuration))
        try:
            cities = api_instance.cities_list(**kwargs)
        except (reference_sdk.ApiException, urllib3.exceptions.HTTPError,) as e:
            logger.error(e)
            cities = {'results': [], 'count': 0}
        return cities
