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

import pdfrw
from django.conf import settings

CHECKBOX_NOT_SELECTED = 'Off'
CHECKBOX_SELECTED = 'Yes'
CHECK_SIZE = 3

REGISTRATION_TEMPLATE_PATH = '/continuing_education/business/templates/form_SIC_times.pdf'

ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_BUTTON_KEY = '/FT'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

EMPTY_VALUE = '-'

MARITAL_STATUS = ["SINGLE", "MARRIED", "WIDOWED", "DIVORCED", "SEPARATED", "LEGAL_COHABITANT"]


def get_data(admission):
    person_information = admission['person_information']
    person = person_information['person']

    residence_address = admission.get('residence_address', None)

    if residence_address and admission.get('use_address_for_post'):
        receive_letter_at_home = pdfrw.PdfName(CHECKBOX_NOT_SELECTED)
        receive_letter_at_residence = pdfrw.PdfName(CHECKBOX_SELECTED)
    else:
        receive_letter_at_home = pdfrw.PdfName(CHECKBOX_SELECTED)
        receive_letter_at_residence = pdfrw.PdfName(CHECKBOX_NOT_SELECTED)

    birth_date = _format_birth_date(person_information)

    data_dict = {
        'academic_year': admission.get('academic_yr', EMPTY_VALUE),
        'last_name': person.get('last_name', EMPTY_VALUE),
        'first_name': person.get('first_name', EMPTY_VALUE),
        'birth_date': birth_date,
        'birth_location': _capitalize(person_information.get('birth_location')),
        'birth_country': _capitalize(person_information.get('birth_country')) if person_information.get(
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
        'last_degree_graduation_year': admission.get('last_degree_graduation_year', EMPTY_VALUE),
        'high_school_graduation_year': admission.get('high_school_graduation_year', EMPTY_VALUE),

        'procedure_66U': pdfrw.PdfName(CHECKBOX_NOT_SELECTED)
    }
    data_dict.update(_build_professional_status(admission.get('professional_status')))
    data_dict.update(_build_marital_status(admission.get('marital_status')))
    data_dict.update(_build_address(admission.get('address', _build_empty_address()), 'contact'))
    data_dict.update(_build_address(admission.get('postal_address', _build_empty_address()), 'postal'))

    if residence_address:
        data_dict.update(_build_address(residence_address, 'residence'))
    return data_dict


def _format_birth_date(person_information):
    if person_information.get('birth_date'):
        birth_date = datetime.datetime.strptime(person_information.get('birth_date'), '%Y-%m-%d')
        return birth_date.strftime('%d-%m-%Y')
    return EMPTY_VALUE


def _build_empty_address():
    return {
        'location': EMPTY_VALUE,
        'postal_code': EMPTY_VALUE,
        'city': EMPTY_VALUE,
        'country': EMPTY_VALUE
    }


def write_fillable_pdf(data_dict):
    buf = io.BytesIO()
    template_pdf = _get_pdf_template()
    if template_pdf:
        _update_pdf_fields(data_dict, template_pdf)
        pdfrw.PdfWriter().write(buf, template_pdf)
        return buf.getvalue()
    return None


def _get_pdf_template():
    input_pdf_path = "{}{}".format(settings.BASE_DIR, REGISTRATION_TEMPLATE_PATH)
    try:
        template_pdf = pdfrw.PdfReader(input_pdf_path)
    except pdfrw.errors.PdfParseError:
        return None
    return template_pdf


def _update_pdf_fields(data_dict, template_pdf):
    for page in template_pdf.pages:
        annotations = page[ANNOT_KEY]
        _check_pdf_annotations(annotations, data_dict)


def _check_pdf_annotations(annotations, data_dict):
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY and annotation[ANNOT_FIELD_KEY]:
            key = annotation[ANNOT_FIELD_KEY][1:-1]
            if key in data_dict.keys():
                _update_form_field(annotation, data_dict, key)


def _update_form_field(annotation, data_dict, key):
    if annotation[ANNOT_BUTTON_KEY][1:-1] == "Bt":
        annotation.update(pdfrw.PdfDict(AS=data_dict[key]))
    else:
        annotation.update(
            pdfrw.PdfDict(V='{}'.format(data_dict[key]))
        )


def _checkbox_selection_status(value, expected_value):
    return \
        pdfrw.PdfName(CHECKBOX_SELECTED) if value and value == expected_value else pdfrw.PdfName(CHECKBOX_NOT_SELECTED)


def _capitalize(value):
    return value.title() if value else EMPTY_VALUE


def _build_address(data_dict, type):
    if type and data_dict:
        return{
            '{}_address_location'.format(type): data_dict.get('location'),
            '{}_address_postal_code'.format(type): data_dict.get('postal_code'),
            '{}_address_city'.format(type): _capitalize(data_dict.get('city')),
            '{}_address_country'.format(type):
                _capitalize(data_dict.get('country'))
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
    seeking_job_on = pdfrw.PdfName(CHECKBOX_NOT_SELECTED)
    seeking_job_off = pdfrw.PdfName(CHECKBOX_NOT_SELECTED)

    if professional_status:
        if professional_status == 'JOB_SEEKER':
            seeking_job_on = pdfrw.PdfName(CHECKBOX_SELECTED)
        else:
            seeking_job_off = pdfrw.PdfName(CHECKBOX_SELECTED)
    return {
        'employee_check': _checkbox_selection_status(professional_status, "EMPLOYEE"),
        'self_employed_check': _checkbox_selection_status(professional_status, "SELF_EMPLOYED"),
        'job_seeker_check': pdfrw.PdfName(CHECKBOX_NOT_SELECTED),
        'other_check': _checkbox_selection_status(professional_status, "OTHER"),
        'seeking_job_on': seeking_job_on,
        'seeking_job_off': seeking_job_off
    }
