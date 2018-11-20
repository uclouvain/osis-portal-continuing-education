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
import itertools
import json
from datetime import datetime
from json import JSONDecodeError
from mimetypes import MimeTypes

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.renderers import MultiPartRenderer
from django.views.decorators.http import require_http_methods

from base.models import person as mdl_person
from base.models.person import Person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm, StrictAddressForm
from continuing_education.forms.admission import AdmissionForm, StrictAdmissionForm
from continuing_education.forms.person import PersonForm, StrictPersonForm
from continuing_education.models import continuing_education_person
from continuing_education.models.address import Address
from continuing_education.models.admission import Admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.common import display_errors, display_success_messages, display_error_messages


@login_required
def admission_detail(request, admission_id):
    admission = _find_user_admission_by_id(admission_id, user=request.user)
    if admission.state == admission_state_choices.DRAFT:
        admission_submission_errors = get_admission_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors

        if not admission_is_submittable:
            messages.add_message(
                request=request,
                level=messages.WARNING,
                message=_build_warning_from_errors_dict(admission_submission_errors),
            )
    else:
        admission_is_submittable = False
    headers_to_get = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    url_continuing_education_file_api = settings.URL_CONTINUING_EDUCATION_FILE_API

    request_to_get_list = _get_files_list(
        admission,
        headers_to_get,
        url_continuing_education_file_api
    )
    list_files = _make_list_files(request_to_get_list)
    if request.method == 'POST' and 'file_submit' in request.POST:
        if 'myfile' in request.FILES:
            file = request.FILES['myfile']
        else:
            file = None
        if file:
            return _upload_file(request, file, admission, kwargs={
                'list_files': list_files,
                'admission_is_submittable': admission_is_submittable
            })

    return render(
        request,
        "admission_detail.html",
        {
            'admission': admission,
            'admission_is_submittable': admission_is_submittable,
            'list_files': list_files
        }
    )


def _upload_file(request, file, admission, **kwargs):
    url_continuing_education_file_api = settings.URL_CONTINUING_EDUCATION_FILE_API
    data = {
        'file': file,
        'admission_id': str(admission.uuid)
    }
    renderer = MultiPartRenderer()
    headers_put = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN,
        'Content-Disposition': 'attachment; filename=name.jpeg',
        'Content-Type': renderer.media_type
    }
    request_to_put_file = requests.put(
        url_continuing_education_file_api,
        data=renderer.render(data),
        headers=headers_put
    )
    if request_to_put_file.status_code == status.HTTP_201_CREATED:
        display_success_messages(request, _("The document is uploaded correctly"))
    else:
        display_error_messages(request, _("A problem occured : the document is not uploaded"))
    kwargs.update({'admission': admission})
    return redirect(
        reverse('admission_detail', kwargs={'admission_id': admission.id}) + '#documents',
        args=kwargs
    )


def _get_files_list(admission, headers_to_get, url_continuing_education_file_api):
    request_to_get_list = requests.get(
        url=url_continuing_education_file_api,
        headers=headers_to_get,
        params={'admission_id': admission.uuid}
    )
    return request_to_get_list


@login_required
@require_http_methods(["POST"])
def admission_submit(request):
    admission = _find_user_admission_by_id(request.POST.get('admission_id'), user=request.user)

    if admission.state == admission_state_choices.DRAFT:
        admission_submission_errors = get_admission_submission_errors(admission)
        if request.POST.get("submit") and not admission_submission_errors:
            admission.submit()
            return redirect('admission_detail', admission.pk)

    raise PermissionDenied


def get_admission_submission_errors(admission):
    errors = {}

    person_form = StrictPersonForm(
        data=model_to_dict(admission.person_information.person)
    )
    for field in person_form.errors:
        errors.update({person_form[field].label: person_form.errors[field]})

    person_information_form = ContinuingEducationPersonForm(
        data=model_to_dict(admission.person_information)
    )
    for field in person_information_form.errors:
        errors.update({person_information_form[field].label: person_information_form.errors[field]})

    address_form = StrictAddressForm(
        data=model_to_dict(admission.address)
    )
    for field in address_form.errors:
        errors.update({address_form[field].label: address_form.errors[field]})

    adm_form = StrictAdmissionForm(
        data=model_to_dict(admission)
    )
    for field in adm_form.errors:
        errors.update({adm_form[field].label: adm_form.errors[field]})
    return errors


def _build_warning_from_errors_dict(errors):
    warning_message = ugettext(
        "Your admission file is not submittable because you did not provide the following data : "
    )

    warning_message = \
        "<strong>" + \
        warning_message + \
        "</strong><br>" + \
        " · ".join([ugettext(key) for key in errors.keys()])

    return mark_safe(warning_message)


def _make_list_files(response):
    try:
        list_temp = response.content.decode('utf8')
        list_json = json.loads(list_temp)
    except (JSONDecodeError, AttributeError):
        list_json = []
    list_files = [
        {
            'path': file['fields']['path'],
            'name': file['fields']['name'],
            'created_date': datetime.strptime(file['fields']['created_date'], "%Y-%m-%dT%H:%M:%S.%f"),
            'size': file['fields']['size']
        }
        for file in list_json
    ]
    return list_files


@login_required
def download_file(request, path):
    url = settings.URL_CONTINUING_EDUCATION_FILE_API
    headers_to_get = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    request_to_get = requests.get(
        url,
        params={'file_path': path},
        headers=headers_to_get
    )
    name = path.rsplit('/', 1)[-1]
    response = HttpResponse()
    mime_type = MimeTypes().guess_type(path)
    response['Content-Type'] = mime_type
    response['Content-Disposition'] = 'attachment; filename=%s' % name
    response.write(request_to_get.content)
    return response


@login_required
def remove_file(request, path):
    url = settings.URL_CONTINUING_EDUCATION_FILE_API
    headers_to_delete = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    request_to_delete = requests.delete(
        url,
        params={'file_path': path},
        headers=headers_to_delete
    )
    if request_to_delete.status_code == status.HTTP_204_NO_CONTENT:
        display_success_messages(request, _("File correctly deleted"))
    else:
        display_error_messages(request, _("A problem occured during delete"))
    return redirect(request.META.get('HTTP_REFERER')+'#documents')


@login_required
def admission_form(request, admission_id=None):
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
        admission.save()
        if request.session.get('formation_id'):
            del request.session['formation_id']
        messages.add_message(
            request=request,
            level=messages.INFO,
            message=_('Your admission file has been saved. Do not forget to submit it when it is complete !'),
        )
        return redirect(reverse('admission_detail', kwargs={'admission_id': admission.pk}))
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
        }
    )


def _find_user_admission_by_id(admission_id, user):
    return get_object_or_404(
        Admission,
        pk=admission_id,
        person_information__person__user=user
    )
