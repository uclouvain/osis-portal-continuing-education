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
from django.http import Http404
from rest_framework import status
from rest_framework.parsers import JSONParser

REQUEST_HEADER = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
API_URL = settings.URL_CONTINUING_EDUCATION_FILE_API + "%(object_name)s/%(object_uuid)s"
NOT_FOUND = 'Pas trouvé.'


def transform_response_to_data(response, results_only=True):
    stream = io.BytesIO(response.content)
    data = JSONParser().parse(stream)
    if 'results' in data and results_only:
        data = data['results']
    return data


def get_data_list_from_osis(object_name, filter_field=None, filter_value=None, **kwargs):
    url = API_URL % {'object_name': object_name, 'object_uuid': ''}
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


def get_admission_list(filter_field=None, filter_value=None, **kwargs):
    return get_data_list_from_osis('admissions', filter_field, filter_value, **kwargs)


def get_persons_list(filter_field=None, filter_value=None, **kwargs):
    return get_data_list_from_osis('persons', filter_field, filter_value, **kwargs)


def get_continuing_education_training_list(filter_field=None, filter_value=None, **kwargs):
    return get_data_list_from_osis('training', filter_field, filter_value, **kwargs)


def get_data_from_osis(object_name, uuid):
    response = requests.get(
        url=API_URL % {'object_name': object_name, 'object_uuid': str(uuid)},
        headers=REQUEST_HEADER
    )
    return transform_response_to_data(response)


def get_admission(uuid):
    data = get_data_from_osis("admissions", uuid)
    if 'detail' in data and data['detail'] == NOT_FOUND:
        raise Http404
    return data


def get_registration(uuid):
    data = get_data_from_osis("registrations", uuid)
    if 'detail' in data and data['detail'] == NOT_FOUND:
        raise Http404
    return data


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


def update_registration(object_to_post):
    return update_data_to_osis("registrations", object_to_post)


def prepare_admission_data(admission, forms):
    if admission:
        forms['admission'].cleaned_data['uuid'] = admission['uuid']

    forms['admission'].cleaned_data['address'] = forms['address'].cleaned_data
    forms['person'].cleaned_data['person'] = forms['id'].cleaned_data
    forms['person'].cleaned_data['birth_date'] = forms['person'].cleaned_data['birth_date'].__str__()
    forms['admission'].cleaned_data['person_information'] = forms['person'].cleaned_data


def prepare_registration_data(registration, forms):
    if registration:
        forms['registration'].cleaned_data['uuid'] = registration['uuid']
    forms['registration'].cleaned_data['residence_address'] = forms['residence'].cleaned_data
    forms['registration'].cleaned_data['billing_address'] = forms['billing'].cleaned_data


def prepare_registration_for_submit(registration):
    registration.pop('person_information')
    registration.pop('formation')
    registration.pop('address')
    registration['residence_address']['country'] = registration['residence_address']['country']['iso_code']
    registration['billing_address']['country'] = registration['billing_address']['country']['iso_code']
