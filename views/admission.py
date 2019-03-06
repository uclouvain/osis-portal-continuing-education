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

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.models import person as mdl_person
from continuing_education.business import perms
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.forms.person import PersonForm
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.api import get_data_from_osis, get_data_list_from_osis, update_data_to_osis, \
    post_data_to_osis, prepare_admission_data
from continuing_education.views.common import display_errors, get_submission_errors, _find_user_admission_by_id, \
    _show_submit_warning, add_informations_message_on_submittable_file, add_contact_for_edit_message
from continuing_education.views.file import _get_files_list


@login_required
@perms.has_participant_access
def admission_detail(request, admission_uuid):
    admission = get_data_from_osis("admissions", admission_uuid)
    if admission['state'] == admission_state_choices.SUBMITTED:
        add_contact_for_edit_message(request)
    if admission['state'] == admission_state_choices.DRAFT:
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
        request,
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
@perms.has_participant_access
def admission_form(request, admission_uuid=None, **kwargs):
    base_person = mdl_person.find_by_user(user=request.user)
    admission = get_data_from_osis("admissions", admission_uuid) if admission_uuid else None

    if admission and admission['state'] != admission_state_choices.DRAFT:
        raise PermissionDenied
    person_information = get_data_list_from_osis("persons", "person", str(base_person))[0]
    adm_form = AdmissionForm(request.POST or None, initial=admission)

    person_form = ContinuingEducationPersonForm(request.POST or None, instance=person_information)

    current_address = admission['address'] if admission else None
    old_admission = get_data_list_from_osis("admissions", "person", str(base_person))[-1]
    if old_admission:
        old_admission = get_data_from_osis("admissions", old_admission['uuid'])
    address = current_address if current_address else (old_admission['address'] if old_admission else None)
    address_form = AddressForm(request.POST or None, initial=address)

    id_form = PersonForm(request.POST or None, instance=base_person)

    errors_fields = []
    if not admission and not request.POST:
        _show_save_before_submit(request)

    if admission and not request.POST:
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(admission_submission_errors, request)

    if all([adm_form.is_valid(), person_form.is_valid(), address_form.is_valid(), id_form.is_valid()]):
        prepare_admission_data(address_form, adm_form, admission, person_form)
        if admission:
            update_data_to_osis(adm_form.cleaned_data, "admissions")
            errors, errors_fields = get_submission_errors(admission)
        else:
            post_data_to_osis(adm_form.cleaned_data, "admissions")
            errors, errors_fields = get_submission_errors(adm_form.cleaned_data)
        if request.session.get('formation_id'):
            del request.session['formation_id']

        return redirect(
            reverse('admission_detail', kwargs={'admission_uuid': admission['uuid'] if 'uuid' in admission else None}),
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
            'errors_fields': errors_fields
        }
    )
