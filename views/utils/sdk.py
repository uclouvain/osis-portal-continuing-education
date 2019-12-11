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

import requests
from django.conf import settings
from rest_framework import status

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


def get_admission_list(request, person_uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.persons_uuid_admissions_get(person_uuid)


def get_registration_list(request, person_uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.persons_uuid_registrations_get(person_uuid)


def get_continuing_education_training_list(**kwargs):
    params = {}
    for key, value in kwargs.items():
        params.update({key: value})
    return api.trainings_get(**params)


def get_continuing_education_person(request):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.persons_details_get().to_dict()


def get_continuing_education_training(uuid):
    return api.trainings_uuid_get(uuid)


def get_admission(request, uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_uuid_get(uuid)


def get_registration(request, uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.registrations_uuid_get(uuid)


def post_prospect(object_to_post):
    return api.prospects_post(object_to_post)


def post_admission(request, object_to_post):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_post(object_to_post)


def update_admission(request, object_to_update):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_uuid_patch(object_to_update['uuid'], object_to_update)


def update_registration(request, object_to_update):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.registrations_uuid_patch(object_to_update['uuid'], object_to_update)


def get_files_list(request, admission_uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_uuid_files_get(admission_uuid)


def get_file(request, admission_uuid, file_uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_uuid_files_file_uuid_get(admission_uuid, file_uuid)


def delete_file(request, admission_uuid, file_uuid):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_uuid_files_file_uuid_delete(admission_uuid, file_uuid)


def upload_file(request, admission_uuid, **kwargs):
    token = get_personal_token(request)
    api.api_client.configuration.api_key['Authorization'] = token
    return api.admissions_uuid_files_post(admission_uuid, **kwargs)


def prepare_admission_data(admission, username, forms):
    if admission:
        forms['admission'].cleaned_data['uuid'] = admission['uuid']

    forms['admission'].cleaned_data['address'] = forms['address'].cleaned_data
    forms['id'].cleaned_data['email'] = username
    forms['person'].cleaned_data['birth_date'] = forms['person'].cleaned_data['birth_date'].__str__()
    forms['admission'].cleaned_data['person_information'] = forms['person'].cleaned_data
    forms['admission'].cleaned_data['person_information']['person'] = forms['id'].cleaned_data


def prepare_registration_data(registration, address, forms, registration_required):
    if registration:
        forms['registration'].cleaned_data['uuid'] = registration['uuid']

    address['country'] = Country.objects.get(name=address['country']).iso_code

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
    registration.pop('citizenship')
    country_name = registration['residence_address']['country']
    registration['residence_address']['country'] = Country.objects.get(
        name=country_name
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
