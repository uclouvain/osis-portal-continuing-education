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

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.parsers import JSONParser

from base.models import person as mdl_person
from base.models.person import Person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.forms.person import PersonForm
from continuing_education.models import continuing_education_person
from continuing_education.models.address import Address
from continuing_education.models.admission import Admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.common import display_errors, display_success_messages, display_error_messages, \
    get_submission_errors, _find_user_admission_by_id, _show_submit_warning, _get_files_list, _upload_file, \
    add_informations_message_on_submittable_file


@login_required
def admission_detail(request, admission_id):
    admission = _find_user_admission_by_id(admission_id, user=request.user)
    if admission.state == admission_state_choices.DRAFT:
        add_informations_message_on_submittable_file(
            request=request,
            title=_("Your admission file has been saved. Please consider the following information :")
        )
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(admission_submission_errors, request)
    else:
        admission_is_submittable = False

    list_files = _get_files_list(
        admission,
        settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission.uuid) + "/files/"
    )
    if request.method == 'POST' and 'file_submit' in request.POST:
        file = request.FILES['myfile'] if 'myfile' in request.FILES else None
        if file:
            return _upload_file(
                request,
                file,
                admission,
                list_files=list_files,
                admission_is_submittable=admission_is_submittable,
                registration=False,
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


def _show_save_before_submit(request):
    messages.add_message(
        request=request,
        level=messages.INFO,
        message=_("You can save an application form and access it later until it is submitted"),
    )


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
        file = JSONParser().parse(stream)
        name = get_valid_filename(file['name'])
        mime_type = MimeTypes().guess_type(file['name'])
        response_file = base64.b64decode(file['content'])
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
        url + "/delete",
        headers=headers_to_delete
    )

    if request_to_delete.status_code == status.HTTP_204_NO_CONTENT:
        display_success_messages(request, _("File correctly deleted"))
    else:
        display_error_messages(request, _("A problem occured during delete"))
    return redirect(request.META.get('HTTP_REFERER')+'#documents')


@login_required
def admission_form(request, admission_id=None, **kwargs):
    base_person = mdl_person.find_by_user(user=request.user)
    admission = _find_user_admission_by_id(admission_id, user=request.user) if admission_id else None
    if admission and admission.state != admission_state_choices.DRAFT:
        raise PermissionDenied
    person_information = continuing_education_person.find_by_person(person=base_person)
    adm_form = AdmissionForm(request.POST or None, instance=admission)
    person_form = ContinuingEducationPersonForm(request.POST or None, instance=person_information)

    current_address = admission.address if admission else None
    old_admission = Admission.objects.filter(person_information=person_information).last()
    address = current_address if current_address else (old_admission.address if old_admission else None)
    address_form = AddressForm(request.POST or None, instance=address)

    id_form = PersonForm(request.POST or None, instance=base_person)

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
            settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission.uuid) + "/files/"
        )
    else:
        list_files = []

    if adm_form.is_valid() and person_form.is_valid() and address_form.is_valid() and id_form.is_valid():
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
        errors, errors_fields = get_submission_errors(admission)
        return redirect(
            reverse('admission_detail', kwargs={'admission_id': admission.id}),
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
