##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import io

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.parsers import JSONParser

REQUEST_HEADER = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
API_URL = settings.URL_CONTINUING_EDUCATION_FILE_API + "%(object_name)s/%(object_uuid)s"


def transform_response_to_data(response, results_only=True):
    stream = io.BytesIO(response.content)
    data = JSONParser().parse(stream)
    if 'results' in data and results_only:
        data = data['results']
    return data


def get_data_list_from_osis(object_name, filter_field=None, filter_value=None, **kwargs):
    url = API_URL % {'object_name': object_name, 'object_uuid': ''}
    print(url)
    results_only = 'limit' not in kwargs or 'offset' not in kwargs
    if filter_field and filter_value:
        url = url + "?" + filter_field + "=" + filter_value
    if not results_only:
        url = url + "?limit="+str(kwargs['limit'])+"&offset="+str(kwargs['offset'])

    response = requests.get(
        url=url,
        headers=REQUEST_HEADER
    )
    return transform_response_to_data(response, results_only)


def get_continuing_education_training_list(filter_field=None, filter_value=None, **kwargs):
    return get_data_list_from_osis('training', filter_field, filter_value, **kwargs)


def get_data_from_osis(object_name, uuid):
    response = requests.get(
        url=API_URL % {'object_name': object_name, 'object_uuid': str(uuid)},
        headers=REQUEST_HEADER
    )
    return transform_response_to_data(response)


def get_admission(uuid):
    return get_data_from_osis("admissions", uuid)


def post_data_to_osis(object_name, object):
    response = requests.post(
        url=API_URL % {'object_name': object_name, 'object_uuid': ''},
        headers=REQUEST_HEADER,
        json=object
    )
    if response.status_code != status.HTTP_201_CREATED:
        data = {}
    else:
        data = transform_response_to_data(response)

    return data, response.status_code


def update_data_to_osis(object_name, object):
    response = requests.patch(
        url=API_URL % {'object_name': object_name, 'object_uuid': object['uuid']},
        headers=REQUEST_HEADER,
        json=object,
    )
    return response


def post_prospect(object_to_post):
    return post_data_to_osis("prospects", object_to_post)


def post_admission(object_to_post):
    return post_data_to_osis("admissions", object_to_post)


def update_admission(object_to_post):
    return update_data_to_osis("admissions", object_to_post)


def prepare_admission_data(address_form, adm_form, admission, person_form):
    if admission:
        adm_form.cleaned_data['uuid'] = admission['uuid']
    if adm_form.instance:
        if adm_form.cleaned_data['formation']:
            if adm_form.instance['formation'] == adm_form.cleaned_data['formation']:
                adm_form.cleaned_data['formation'] = adm_form.instance['formation_uuid']
        if adm_form.cleaned_data['citizenship']:
            if adm_form.instance['citizenship'] == adm_form.cleaned_data['citizenship']:
                adm_form.cleaned_data['citizenship'] = adm_form.instance['citizenship_iso']
    if address_form.instance:
        if address_form.cleaned_data['country']:
            if address_form.instance['country'] == address_form.cleaned_data['country']:
                address_form.cleaned_data['country'] = address_form.instance['country_iso']
    adm_form.cleaned_data['address'] = address_form.cleaned_data
    if person_form.instance:
        if person_form.cleaned_data['birth_country']:
            if person_form.instance['birth_country'] == person_form.cleaned_data['birth_country']:
                person_form.cleaned_data['birth_country'] = person_form.instance['iso']
    person_form.cleaned_data['birth_date'] = person_form.cleaned_data['birth_date'].__str__()
    adm_form.cleaned_data['person_information'] = person_form.cleaned_data
