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
import ast
import io
import json

import requests
from django.conf import settings
from rest_framework.parsers import JSONParser
from rest_framework.renderers import MultiPartRenderer


def transform_response_to_data(response):
    stream = io.BytesIO(response.content)
    data = JSONParser().parse(stream)
    if 'results' in data:
        data = data['results']
    return data


def get_data_list_from_osis(object_name, filter_field=None, filter_value=None):
    header_to_get = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + object_name + "/"
    if filter_field and filter_value:
        url = url + "?" + filter_field + "=" + filter_value
    response = requests.get(
        url=url,
        headers=header_to_get
    )
    return transform_response_to_data(response)


def get_data_from_osis(object_name, uuid):
    header_to_get = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + object_name + "/" + str(uuid)
    response = requests.get(
        url=url,
        headers=header_to_get
    )
    return transform_response_to_data(response)


def _prepare_headers_for_files(method):
    if method in ['GET', 'DELETE']:
        return {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
    elif method == 'POST':
        return {
            'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN,
            'Content-Disposition': 'attachment; filename=name.jpeg',
            'Content-Type': MultiPartRenderer.media_type
        }


def post_data_to_osis(object, object_name):
    header_to_post = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + object_name + "/"
    response = requests.post(
        url=url,
        headers=header_to_post,
        data=object
    )
    return response


def update_data_to_osis(object, object_name):
    header_to_put = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + object_name + "/" + object['uuid']
    response = requests.patch(
        url=url,
        headers=header_to_put,
        json=object,
    )
    return response


def prepare_admission_data(address_form, adm_form, admission, person_form):
    if admission:
        adm_form.cleaned_data['uuid'] = admission['uuid']

    if adm_form.cleaned_data['citizenship']:
        adm_form.cleaned_data['citizenship'] = json.loads(adm_form.cleaned_data['citizenship'].replace("\'", '"'))[
            'iso_code']

    if address_form.cleaned_data['country']:
        address_form.cleaned_data['country'] = json.loads(address_form.cleaned_data['country'].replace("\'", '"'))[
            'iso_code']
    adm_form.cleaned_data['address'] = address_form.cleaned_data

    if person_form.cleaned_data['birth_country']:
        person_form.cleaned_data['birth_country'] = json.loads(
            person_form.cleaned_data['birth_country'].replace("\'", '"')
        )['iso_code']

    person_form.cleaned_data['birth_date'] = person_form.cleaned_data['birth_date'].__str__()
    adm_form.cleaned_data['person_information'] = person_form.cleaned_data
    if adm_form.cleaned_data['formation']:
        adm_form.cleaned_data['formation'] = ast.literal_eval(adm_form.cleaned_data['formation'])['uuid']
