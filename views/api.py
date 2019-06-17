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

from openapi_client import Configuration, ApiClient
from openapi_client.api.default_api import DefaultApi

from reference.models.country import Country

REQUEST_HEADER = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
API_URL = settings.URL_CONTINUING_EDUCATION_FILE_API + "/%(object_name)s/%(object_uuid)s"

api_config = Configuration()
api_config.api_key_prefix['Authorization'] = "Token"
api_config.api_key['Authorization'] = settings.OSIS_PORTAL_TOKEN
api_config.host = settings.URL_CONTINUING_EDUCATION_FILE_API

api = DefaultApi(
    api_client=ApiClient(
        configuration=api_config
    )
)


def transform_response_to_data(response):
    stream = io.BytesIO(response.content)
    data = JSONParser().parse(stream)
    return data


def get_data_list_from_osis(request, object_name):
    token = get_personal_token(request)
    url = API_URL % {'object_name': object_name, 'object_uuid': ''}
    response = requests.get(
        url=url,
        headers={'Authorization': 'Token ' + token}
    )
    return transform_response_to_data(response)


def get_admission_list(request, person_uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.persons_uuid_admissions_get(person_uuid)


def get_registration_list(request, person_uuid):
    token = get_personal_token(request)
    response = requests.get(
        url=API_URL % {'object_name': "persons", 'object_uuid': person_uuid} + "/registrations/",
        headers={'Authorization': 'Token ' + token}
    )
    return transform_response_to_data(response)


def get_continuing_education_training_list(**kwargs):
    params = {}
    for key, value in kwargs.items():
        params.update({key: value})
    return api.trainings_get(**params).to_dict()


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


def get_continuing_education_person():
    return api.persons_details_get()


def get_continuing_education_training(uuid):
    return api.trainings_uuid_get(uuid)


def get_admission(uuid):
    return api.admissions_uuid_get(uuid)


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
    forms['person'].cleaned_data['birth_date'] = forms['person'].cleaned_data['birth_date'].__str__()
    forms['admission'].cleaned_data.update(**forms['person'].cleaned_data)
    forms['admission'].cleaned_data.update(**forms['id'].cleaned_data)


def prepare_registration_data(registration, address, forms):
    if registration:
        forms['registration'].cleaned_data['uuid'] = registration['uuid']

    address['country'] = Country.objects.get(name=address['country']).iso_code

    if forms['registration'].cleaned_data['use_address_for_billing'] == 'True':
        forms['registration'].cleaned_data['billing_address'] = address
    else:
        forms['registration'].cleaned_data['billing_address'] = forms['billing'].cleaned_data
    if forms['registration'].cleaned_data['use_address_for_post'] == 'True':
        forms['registration'].cleaned_data['residence_address'] = address
    else:
        forms['registration'].cleaned_data['residence_address'] = forms['residence'].cleaned_data


def prepare_registration_for_submit(registration):
    registration.pop('address')
    registration.pop('citizenship')
    registration['residence_address']['country'] = Country.objects.get(
        name=registration['residence_address']['country']
    ).iso_code
    registration['billing_address']['country'] = Country.objects.get(
        name=registration['billing_address']['country']
    ).iso_code


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
