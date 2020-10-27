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
import io

import pypdftk
from django.conf import settings

CHECKBOX_NOT_SELECTED = 'Off'
CHECKBOX_SELECTED = 'Yes'

REGISTRATION_TEMPLATE_PATH = '/continuing_education/business/templates/form_SIC_times.pdf'

EMPTY_VALUE = '-'

MARITAL_STATUS = ["SINGLE", "MARRIED", "WIDOWED", "DIVORCED", "SEPARATED", "LEGAL_COHABITANT"]

MANAGER_NAME_KEY = 'manager_name'
MANAGER_LOCATION_KEY = 'manager_address_location'
MANAGER_POSTAL_CODE_KEY = 'manager_address_postal_code'
MANAGER_CITY_KEY = 'manager_address_city'
MANAGER_COUNTRY_KEY = 'manager_address_country'


def get_data(admission):
    person_information = admission['person_information']
    person = person_information['person']

    residence_address = admission.get('residence_address', None)

    data_dict = {}
    if residence_address and not admission.get('use_address_for_post'):
        receive_letter_at_home = CHECKBOX_NOT_SELECTED
        receive_letter_at_residence = CHECKBOX_SELECTED
        data_dict.update(_build_address(residence_address, 'residence'))
    else:
        receive_letter_at_home = CHECKBOX_SELECTED
        receive_letter_at_residence = CHECKBOX_NOT_SELECTED

    birth_date = _format_birth_date(person_information)

    data_dict.update({
        'academic_year': admission.get('academic_yr', EMPTY_VALUE),
        'last_name': person.get('last_name', EMPTY_VALUE),
        'first_name': person.get('first_name', EMPTY_VALUE),
        'card_command_last_name': person.get('last_name', EMPTY_VALUE),
        'card_command_first_name': person.get('first_name', EMPTY_VALUE),
        'birth_date': birth_date,
        'birth_location': _capitalize(person_information.get('birth_location')),
        'birth_country': _capitalize(person_information.get('birth_country').get('name')) if person_information.get(
            'birth_country') else EMPTY_VALUE,
        'citizenship':
            _capitalize(admission.get('citizenship').get('name')) if admission.get('citizenship') else EMPTY_VALUE,
        'national_registry_number': admission.get('national_registry_number', EMPTY_VALUE),
        'id_card_number': admission.get('id_card_number', EMPTY_VALUE),
        'passport_number': admission.get('passport_number', EMPTY_VALUE),
        'gender_image_f': _checkbox_selection_status(person.get('gender'), "F"),
        'gender_image_m': _checkbox_selection_status(person.get('gender'), "M"),
        'spouse_name': admission.get('spouse_name', EMPTY_VALUE),
        'children_number': admission.get('children_number', EMPTY_VALUE),
        'previous_noma': admission.get('previous_noma', "-") if admission.get('previous_noma') and admission.get(
            'previous_noma') != '' else EMPTY_VALUE,
        'mobile': admission.get('phone_mobile', EMPTY_VALUE),
        'private_email': person.get('email', EMPTY_VALUE),
        'residence_phone': admission.get('residence_phone', EMPTY_VALUE),
        'receive_letter_at_home': receive_letter_at_home,
        'receive_letter_at_residence': receive_letter_at_residence,
        'last_degree_graduation_year': admission.get('last_degree_graduation_year', EMPTY_VALUE) or EMPTY_VALUE,
        'high_school_graduation_year': admission.get('high_school_graduation_year', EMPTY_VALUE) or EMPTY_VALUE,
        'box_faculty_training_name': _get_education_group(admission).get('title', EMPTY_VALUE),
        'box_faculty_training_code': _get_education_group(admission).get('acronym', EMPTY_VALUE),
        'box_faculty_training_manager_name': _get_one_manager(admission.get('formation').get('managers')),
        'procedure_66U': CHECKBOX_NOT_SELECTED
    })

    data_dict.update(_build_professional_status(admission.get('professional_status')))
    data_dict.update(_build_marital_status(admission.get('marital_status')))
    data_dict.update(_build_address(admission.get('address', _build_empty_address()), 'contact'))
    data_dict.update(_build_manager_data(admission.get('formation')))

    return data_dict


def _get_education_group(admission):
    try:
        return admission['formation']['education_group']
    except KeyError:
        return {}


def _format_birth_date(person_information):
    if person_information.get('birth_date'):
        birth_date = datetime.datetime.strptime(person_information.get('birth_date'), '%Y-%m-%d')
        return birth_date.strftime('%d-%m-%Y')
    return EMPTY_VALUE


def _build_empty_address():
    return {'location': EMPTY_VALUE,
            'postal_code': EMPTY_VALUE,
            'city': EMPTY_VALUE,
            'country': {'name': EMPTY_VALUE}}


def write_fillable_pdf(data_dict):
    buf = io.BytesIO()
    input_pdf_path = "{}{}".format(settings.BASE_DIR, REGISTRATION_TEMPLATE_PATH)
    pdf = pypdftk.fill_form(input_pdf_path, datas=data_dict, flatten=True)
    with open(pdf, mode='rb') as f:
        buf.write(f.read())
        return buf.getvalue()


def _checkbox_selection_status(value, expected_value):
    return \
        CHECKBOX_SELECTED if value and value == expected_value else CHECKBOX_NOT_SELECTED


def _capitalize(value):
    return value.title() if value else EMPTY_VALUE


def _build_address(data_dict, type):
    if type and data_dict:
        return {
            '{}_address_location'.format(type): data_dict.get('location'),
            '{}_address_postal_code'.format(type): data_dict.get('postal_code'),
            '{}_address_city'.format(type): _capitalize(data_dict.get('city')),
            '{}_address_country'.format(type):
                _capitalize(data_dict.get('country').get('name'))
                if data_dict.get('country') else EMPTY_VALUE,
        }
    return {}


def _build_marital_status(marital_status):
    dict_marital_status = {}
    for status in MARITAL_STATUS:
        dict_marital_status.update(
            {"marital_{}_check".format(status.lower()): _checkbox_selection_status(marital_status, status)}
        )
    return dict_marital_status


def _build_professional_status(professional_status):
    seeking_job_on = CHECKBOX_NOT_SELECTED
    seeking_job_off = CHECKBOX_NOT_SELECTED

    if professional_status:
        if professional_status == 'JOB_SEEKER':
            seeking_job_on = CHECKBOX_SELECTED
        else:
            seeking_job_off = CHECKBOX_SELECTED
    return {
        'employee_check': _checkbox_selection_status(professional_status, "EMPLOYEE"),
        'self_employed_check': _checkbox_selection_status(professional_status, "SELF_EMPLOYED"),
        'job_seeker_check': _checkbox_selection_status(professional_status, "JOB_SEEKER"),
        'other_check': _checkbox_selection_status(professional_status, "OTHER"),
        'seeking_job_on': seeking_job_on,
        'seeking_job_off': seeking_job_off
    }


def _get_one_manager(managers):
    if managers and isinstance(managers, list):
        for manager in managers:
            if manager.get('first_name') and manager.get('last_name'):
                return "{} {}".format(manager.get('first_name'), manager.get('last_name'))
    return ''


def _build_manager_data(formation):
    formation_postal_address = formation.get('postal_address', {}) or {}
    formation_country = formation_postal_address.get('country', {}) or {}
    return {
        MANAGER_NAME_KEY: _get_one_manager(formation.get('managers')),
        MANAGER_LOCATION_KEY: formation_postal_address.get('location', ''),
        MANAGER_POSTAL_CODE_KEY:
            formation_postal_address.get('postal_code', ''),
        MANAGER_CITY_KEY: formation_postal_address.get('city', ''),
        MANAGER_COUNTRY_KEY: formation_country.get('name', '')
    }
