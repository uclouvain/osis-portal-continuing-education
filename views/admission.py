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
import base64
import io
import itertools
from mimetypes import MimeTypes
from pprint import pprint

import requests
from dateutil import parser
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.renderers import MultiPartRenderer

from base.models import person as mdl_person
from base.models.person import Person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.forms.person import PersonForm
from continuing_education.models.address import Address
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.common import display_errors, display_success_messages, display_error_messages, \
    get_submission_errors, _find_user_admission_by_id, _show_submit_warning, _build_warning_from_errors_dict, \
    get_data_from_osis, get_data_list_from_osis


@login_required
def admission_detail(request, admission_uuid):
    admission = get_data_from_osis("admissions", admission_uuid)
    if admission["state"] == admission_state_choices.DRAFT:
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(admission_submission_errors, request)
    else:
        admission_is_submittable = False

    list_files = _get_files_list(
        admission,
        settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission_uuid) + "/files/"
    )

    return render(
        request,
        "admission_detail.html",
        {
            'admission': admission,
            'admission_is_submittable': admission_is_submittable,
            'list_files': list_files
        }
    )


MAX_ADMISSION_FILE_NAME_LENGTH = 100


@login_required
def upload_file(request, admission_uuid):
    admission_file = request.FILES['myfile'] if 'myfile' in request.FILES else None
    admission = get_data_from_osis("admissions", admission_uuid)
    person = admission['person_information']['person']
    data = {
        'uploaded_by': person['uuid'],
    }
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission_uuid) + "/files/"
    headers_to_upload = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN,
    }

    request_to_upload = requests.post(
        url,
        headers=headers_to_upload,
        files={'path': admission_file},
        data=data
    )

    if request_to_upload.status_code == status.HTTP_201_CREATED:
        display_success_messages(request, _("The document is uploaded correctly"))
    elif request_to_upload.status_code == status.HTTP_406_NOT_ACCEPTABLE:
        display_error_messages(
            request,
            _("The name of the file is too long : maximum %(length)s characters.") % {
                    'length': MAX_ADMISSION_FILE_NAME_LENGTH
                }
        )
    else:
        display_error_messages(request, _("A problem occured : the document is not uploaded"))

    return redirect(request.META.get('HTTP_REFERER')+'#documents')


def _show_submit_warning(admission_submission_errors, request):
    if request.method == 'GET':
        messages.add_message(
            request=request,
            level=messages.WARNING,
            message=_build_warning_from_errors_dict(admission_submission_errors),
        )


def _show_save_before_submit(request):
    messages.add_message(
        request=request,
        level=messages.INFO,
        message=_("You can save an application form and access it later until it is submitted"),
    )


def _show_admission_saved(request, admission_uuid):
    messages.add_message(
        request=request,
        level=messages.INFO,
        message=mark_safe(
            _('Your admission file has been saved. '
              'You are still able to edit the form. '
              'Do not forget to submit it when it is complete via '
              '<a href="%(url)s"><b>the admission file page</b></a> !'
              ) % {'url': reverse('admission_detail', kwargs={'admission_uuid': admission_uuid})}
        ))


def _get_files_list(admission, url_continuing_education_file_api):
    files_list = []
    if admission:
        response = requests.get(
            url=url_continuing_education_file_api,
            headers=_prepare_headers('GET'),
        )
        if response.status_code == status.HTTP_200_OK:
            stream = io.BytesIO(response.content)
            files_list = JSONParser().parse(stream)['results']
            for admission_file in files_list:
                admission_file['created_date'] = parser.parse(
                    admission_file['created_date']
                )
                admission_file['is_deletable'] = _file_uploaded_by_admission_person(admission, admission_file)
    return files_list


def _file_uploaded_by_admission_person(admission, file):
    return _get_uploadedby_uuid(file) == str(admission['person_information']['person']['uuid'])


def _get_uploadedby_uuid(file):
    uploaded_by = file.get('uploaded_by', None)
    return uploaded_by.get('uuid', None) if uploaded_by else None


def _prepare_headers(method):
    if method in ['GET', 'DELETE']:
        return {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
    elif method == 'POST':
        return {
            'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN,
            'Content-Disposition': 'attachment; filename=name.jpeg',
            'Content-Type': MultiPartRenderer.media_type
        }


@login_required
@require_http_methods(["POST"])
def admission_submit(request):
    admission = _find_user_admission_by_id(request.POST.get('admission_id'), user=request.user)

    if admission.state == admission_state_choices.DRAFT:
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        if request.POST.get("submit") and not admission_submission_errors:
            admission.submit()
            return redirect('admission_detail', admission.pk)

    raise PermissionDenied


@login_required
def download_file(request, file_uuid, admission_uuid):
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + \
          "admissions/" + str(admission_uuid) + "/files/" + str(file_uuid)
    headers_to_get = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    request_to_get = requests.get(
        url,
        headers=headers_to_get
    )
    if request_to_get.status_code == status.HTTP_200_OK:
        stream = io.BytesIO(request_to_get.content)
        admission_file = JSONParser().parse(stream)
        name = get_valid_filename(admission_file['name'])
        mime_type = MimeTypes().guess_type(admission_file['name'])
        response_file = base64.b64decode(admission_file['content'])
        response = HttpResponse(response_file, mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % name
        return response
    else:
        return HttpResponse(status=404)


@login_required
def remove_file(request, file_uuid, admission_uuid):
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + \
          "admissions/" + str(admission_uuid) + "/files/" + str(file_uuid)
    headers_to_delete = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    request_to_delete = requests.delete(
        url,
        headers=headers_to_delete
    )

    if request_to_delete.status_code == status.HTTP_204_NO_CONTENT:
        display_success_messages(request, _("File correctly deleted"))
    else:
        display_error_messages(request, _("A problem occured during delete"))
    return redirect(request.META.get('HTTP_REFERER')+'#documents')


@login_required
def admission_form(request, admission_uuid=None, **kwargs):
    base_person = mdl_person.find_by_user(user=request.user)
    admission = get_data_from_osis("admissions", admission_uuid) if admission_uuid else None
    if admission and admission['state'] != admission_state_choices.DRAFT:
        raise PermissionDenied
    person_information = get_data_list_from_osis("persons", "person", str(base_person))[0]
    adm_form = AdmissionForm(admission)
    pprint(adm_form)
    person_form = ContinuingEducationPersonForm(initial=person_information)

    current_address = admission['main_address'] if admission else None
    # old_admission = Admission.objects.filter(person_information=person_information).last()
    old_admission = get_data_list_from_osis("admissions", "person_information__uuid", str(person_information['uuid']))
    address = current_address if current_address else (old_admission.address if old_admission else None)

    address_form = AddressForm(initial=address)

    id_form = PersonForm(request.POST or None, instance=base_person)

    landing_tab = request.POST.get("tab") or kwargs.get('landing_tab')
    landing_tab_anchor = "#{}".format(landing_tab) if landing_tab else ""

    errors_fields = []

    if not admission and not request.POST:
        _show_save_before_submit(request)

    if admission and not request.POST:
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(admission_submission_errors, request)
    if admission:
        list_files = _get_files_list(
            admission,
            settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission['uuid']) + "/files/"
        )
    else:
        list_files = []

    if all([adm_form.is_valid(), person_form.is_valid(), address_form.is_valid(), id_form.is_valid()]):
        if current_address:
            address = address_form.save()
        else:
            address = Address(**address_form.cleaned_data)
            address.save()

        identity = Person.objects.filter(user=request.user)

        if not identity:
            identity, id_created = Person.objects.get_or_create(**id_form.cleaned_data)
            identity.user = request.user
            identity.save()
        else:
            identity.update(**id_form.cleaned_data)
            identity = identity.first()

        person = person_form.save(commit=False)
        person.person_id = identity.pk
        person.save()

        admission = adm_form.save(commit=False)
        admission.person_information = person
        admission.address = address
        admission.billing_address = address
        admission.residence_address = address
        admission.save()
        if request.session.get('formation_id'):
            del request.session['formation_id']
        _show_admission_saved(request, admission.id)
        errors, errors_fields = get_submission_errors(admission)
        return redirect(
            reverse('admission_edit', kwargs={'admission_id': admission.id}) + landing_tab_anchor,
        )
    else:
        errors = list(itertools.product(adm_form.errors, person_form.errors, address_form.errors, id_form.errors))
        display_errors(request, errors)

    return render(
        request,
        'admission_form.html',
        {
            'admission_form': adm_form,
            'person_form': person_form,
            'address_form': address_form,
            'id_form': id_form,
            'admission': admission,
            'list_files': list_files,
            'errors_fields': errors_fields
        }
    )
