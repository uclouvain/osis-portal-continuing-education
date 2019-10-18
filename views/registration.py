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
import itertools

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.models import person as mdl_person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.person import PersonForm
from continuing_education.forms.registration import RegistrationForm
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.admission_state_choices import REGISTRATION_SUBMITTED
from continuing_education.views import api
from continuing_education.views.common import display_errors, get_submission_errors, _show_submit_warning, \
    add_informations_message_on_submittable_file, add_contact_for_edit_message, \
    add_remaining_tasks_message
from continuing_education.views.file import _get_files_list, FILES_URL
from continuing_education.business.pdf_filler import write_fillable_pdf, get_data
from base.views import common


@login_required
def registration_detail(request, admission_uuid):
    admission = api.get_registration(request, admission_uuid)
    if admission['state'] == admission_state_choices.REGISTRATION_SUBMITTED:
        add_remaining_tasks_message(request, admission['formation'])
        add_contact_for_edit_message(request, formation=admission['formation'], is_registration=True)
    if admission['state'] == admission_state_choices.ACCEPTED:
        add_informations_message_on_submittable_file(
            request=request,
            title=_("Your registration file has been saved. Please consider the following information :")
        )
        registration_submission_errors, errors_fields = get_submission_errors(admission, is_registration=True)
        registration_is_submittable = not registration_submission_errors
        if not registration_is_submittable:
            _show_submit_warning(registration_submission_errors, request)
    else:
        registration_is_submittable = False
    list_files = _get_files_list(
        request,
        admission,
        FILES_URL % {'admission_uuid': str(admission_uuid)}
    )
    is_accepted = admission['state'] == admission_state_choices.ACCEPTED
    is_registration_submitted = admission['state'] == admission_state_choices.REGISTRATION_SUBMITTED
    return render(request, "registration_detail.html", locals())


@login_required
@require_http_methods(["POST"])
def registration_submit(request):
    registration = api.get_registration(request, request.POST.get('registration_uuid'))
    api.prepare_registration_for_submit(registration)
    registration_submission_errors, errors_fields = get_submission_errors(registration, is_registration=True)
    if request.POST.get("submit") and not registration_submission_errors:
        registration['state'] = admission_state_choices.REGISTRATION_SUBMITTED
        api.update_registration(request, registration)
    return redirect('registration_detail', registration['uuid'])


@login_required
def registration_edit(request, admission_uuid):
    registration = api.get_registration(request, admission_uuid)
    if registration and registration['state'] != admission_state_choices.ACCEPTED:
        raise PermissionDenied

    form = RegistrationForm(request.POST or None, initial=registration)
    billing_address_form = AddressForm(request.POST or None, initial=registration['billing_address'], prefix="billing")
    residence_address_form = AddressForm(
        request.POST or None,
        initial=registration['residence_address'],
        prefix="residence"
    )
    base_person = mdl_person.find_by_user(user=request.user)
    id_form = PersonForm(request.POST or None, instance=base_person)
    person_information = api.get_continuing_education_person(request)
    person_form = ContinuingEducationPersonForm(request.POST or None, initial=person_information)
    address = registration['address']

    errors = []
    errors_fields = []
    if registration and not request.POST:
        registration_submission_errors, errors_fields = get_submission_errors(registration, is_registration=True)
        admission_is_submittable = not registration_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(registration_submission_errors, request)

    if all([form.is_valid(), billing_address_form.is_valid(), residence_address_form.is_valid()]):
        api.prepare_registration_data(
            registration,
            address,
            forms={
                'registration': form,
                'residence': residence_address_form,
                'billing': billing_address_form,
            },
        )
        api.update_registration(request, form.cleaned_data)
        return redirect(
            reverse('registration_detail', kwargs={'admission_uuid': admission_uuid})
        )
    else:
        errors = list(itertools.product(form.errors, residence_address_form.errors, billing_address_form.errors))
        display_errors(request, errors)
    return render(request, 'registration_form.html', locals())


@login_required
def generate_pdf_registration(request, admission_uuid):
    admission = api.get_registration(request, admission_uuid)
    if admission['state'] != REGISTRATION_SUBMITTED:
        return redirect(
            reverse('registration_detail', kwargs={'admission_uuid': admission_uuid})
        )
    pdf_filename = get_valid_filename("{}_{}".format(
        admission['person_information']['person']['last_name'],
        admission['formation']['education_group']['acronym'])
    )

    result = write_fillable_pdf(get_data(admission))
    if result:
        # Creating http response
        response = HttpResponse(content_type='application/pdf;')
        response['Content-Disposition'] = 'attachment; filename={}.pdf'.format(pdf_filename)
        response['Content-Transfer-Encoding'] = 'binary'
        response.write(result)
        return response
    else:
        return common.page_not_found(request)

