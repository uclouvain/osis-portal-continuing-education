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
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser

REQUEST_HEADER = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
API_URL = settings.URL_CONTINUING_EDUCATION_FILE_API + "%(object_name)s/%(object_uuid)s"


def transform_response_to_data(response):
    stream = io.BytesIO(response.content)
    data = JSONParser().parse(stream)
    return data


def get_admission_list(request, person_uuid):
    token = get_personal_token(request)
    response = requests.get(
        url=API_URL % {'object_name': "persons", 'object_uuid': person_uuid} + "/admissions/",
        headers={'Authorization': 'Token ' + token}
    )
    return transform_response_to_data(response)


def get_registration_list(request, person_uuid):
    token = get_personal_token(request)
    response = requests.get(
        url=API_URL % {'object_name': "persons", 'object_uuid': person_uuid} + "/registrations/",
        headers={'Authorization': 'Token ' + token}
    )
    return transform_response_to_data(response)


def get_continuing_education_training_list(**kwargs):
    params = {}
    url = API_URL % {'object_name': "training", 'object_uuid': ''}
    for key, value in kwargs.items():
        params.update({key: value})
    response = requests.get(
        url=url,
        headers=REQUEST_HEADER,
        params=params
    )
    return transform_response_to_data(response)


def get_data_from_osis(request, object_name, uuid):

    response = requests.get(
        url=API_URL % {'object_name': object_name, 'object_uuid': str(uuid)},
        headers={'Authorization': 'Token ' + get_personal_token(request)} if request.user.is_authenticated
        else REQUEST_HEADER
    )
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise Http404
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        raise PermissionDenied(response.json()['detail'] if response.content else '')
    return transform_response_to_data(response)


def get_continuing_education_person(request):
    return get_data_from_osis(request, "persons", "details")


def get_continuing_education_training(request, uuid):
    return get_data_from_osis(request, "training", uuid)


def get_admission(request, uuid):
    return get_data_from_osis(request, "admissions", uuid)


def get_registration(request, uuid):
    return get_data_from_osis(request, "registrations", uuid)


def post_data_to_osis(request, object_name, object_to_post):
    token = get_personal_token(request)
    response = requests.post(
        url=API_URL % {'object_name': object_name, 'object_uuid': ''},
        headers=REQUEST_HEADER if object_name == 'prospects' else {'Authorization': 'Token ' + token},
        json=object_to_post
    )
    if response.status_code != status.HTTP_201_CREATED:
        data = {}
    else:
        data = transform_response_to_data(response)

    return data, response.status_code


def post_prospect(request, object_to_post):
    return post_data_to_osis(request, "prospects", object_to_post)


def post_admission(request, object_to_post):
    return post_data_to_osis(request, "admissions", object_to_post)


def update_data_to_osis(request, object_name, object_to_update):
    token = get_personal_token(request)
    response = requests.patch(
        url=API_URL % {'object_name': object_name, 'object_uuid': object_to_update['uuid']},
        headers={'Authorization': 'Token ' + token},
        json=object_to_update,
    )
    if response.status_code == status.HTTP_403_FORBIDDEN:
        raise PermissionDenied(response.json()['detail'] if response.content else '')
    return response


def update_admission(request, object_to_update):
    return update_data_to_osis(request, "admissions", object_to_update)


def update_registration(request, object_to_update):
    return update_data_to_osis(request, "registrations", object_to_update)


def prepare_admission_data(admission, username, forms):
    if admission:
        forms['admission'].cleaned_data['uuid'] = admission['uuid']

    forms['admission'].cleaned_data['address'] = forms['address'].cleaned_data
    forms['id'].cleaned_data['email'] = username
    forms['person'].cleaned_data['person'] = forms['id'].cleaned_data
    forms['person'].cleaned_data['birth_date'] = forms['person'].cleaned_data['birth_date'].__str__()
    forms['admission'].cleaned_data['person_information'] = forms['person'].cleaned_data


def prepare_registration_data(registration, address, forms, registration_required):
    if registration:
        forms['registration'].cleaned_data['uuid'] = registration['uuid']

    if address['country']:
        address['country'] = address['country']['iso_code'] \
            if 'iso_code' in address['country'] else address['country'][0]

    _prepare_address(address, forms, 'billing', 'billing')
    if registration_required:
        _prepare_address(address, forms, 'post', 'residence')
    else:
        keys = ['children_number', 'previous_ucl_registration', 'use_address_for_post', 'residence_address']
        for key_field in keys:
            forms['registration'].cleaned_data.pop(key_field)


def _prepare_address(address, forms, utility, address_type):
    if forms['registration'].cleaned_data['use_address_for_' + utility] == "True":
        forms['registration'].cleaned_data[address_type + '_address'] = address
    else:
        forms['registration'].cleaned_data[address_type + '_address'] = forms[address_type].cleaned_data


def prepare_registration_for_submit(registration):
    registration.pop('address')
    registration.pop('person_information')
    registration.pop('formation')
    registration.pop('citizenship')
    registration['residence_address']['country'] = registration['residence_address']['country']['iso_code']
    registration['billing_address']['country'] = registration['billing_address']['country']['iso_code']


def get_token_from_osis(username, force_user_creation=False):
    response = requests.post(
        url=settings.URL_AUTH_API,
        headers=REQUEST_HEADER,
        data={
            'username': username,
            'force_user_creation': force_user_creation
        }
    )
    if response.status_code == status.HTTP_200_OK:
        return response.json()['token']
    else:
        return ""


def get_personal_token(request):
    if not request.session.get('personal_token'):
        request.session['personal_token'] = get_token_from_osis(request.user.username, force_user_creation=True)
    return request.session['personal_token']
