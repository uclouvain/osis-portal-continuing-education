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
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.models import person as mdl_person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.person import PersonForm
from continuing_education.forms.registration import RegistrationForm
from continuing_education.models import continuing_education_person
from continuing_education.models.address import Address
from continuing_education.models.admission import Admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.models.enums.admission_state_choices import ACCEPTED
from continuing_education.views.common import display_errors, get_submission_errors, _find_user_admission_by_id, \
    _show_submit_warning, add_informations_message_on_submittable_file
from continuing_education.views.file import _get_files_list


@login_required
def registration_detail(request, admission_id):
    admission = get_object_or_404(Admission, pk=admission_id)

    if admission.state == admission_state_choices.ACCEPTED:
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
        settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission.uuid) + "/files/"
    )

    return render(request, "registration_detail.html", locals())


@login_required
@require_http_methods(["POST"])
def registration_submit(request):
    admission = _find_user_admission_by_id(request.POST.get('admission_id'), user=request.user)
    if admission.state == admission_state_choices.ACCEPTED:
        registration_submission_errors, errors_fields = get_submission_errors(admission, is_registration=True)
        if request.POST.get("submit") and not registration_submission_errors:
            admission.submit_registration()
            return redirect('registration_detail', admission.pk)
    raise PermissionDenied


@login_required
def registration_edit(request, admission_id):
    admission = get_object_or_404(Admission, pk=admission_id, state=ACCEPTED)
    form = RegistrationForm(request.POST or None, instance=admission)
    billing_address_form = AddressForm(request.POST or None, instance=admission.billing_address, prefix="billing")
    residence_address_form = AddressForm(request.POST or None, instance=admission.residence_address, prefix="residence")
    base_person = mdl_person.find_by_user(user=request.user)
    id_form = PersonForm(request.POST or None, instance=base_person)
    person_information = continuing_education_person.find_by_person(person=base_person)
    person_form = ContinuingEducationPersonForm(request.POST or None, instance=person_information)

    address = admission.address
    residence_address = admission.residence_address
    billing_address = admission.billing_address

    errors = []
    errors_fields = []
    if admission and not request.POST:
        registration_submission_errors, errors_fields = get_submission_errors(admission, is_registration=True)
        admission_is_submittable = not registration_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(registration_submission_errors, request)

    if form.is_valid() and billing_address_form.is_valid() and residence_address_form.is_valid():
        use_address = {
            'for_billing': form.cleaned_data['use_address_for_billing'],
            'for_post': form.cleaned_data['use_address_for_post']
        }
        admission.residence_address = residence_address
        admission.billing_address = billing_address
        billing_address, residence_address = _update_or_create_billing_and_post_address(
            address,
            {'address': billing_address, 'form': billing_address_form},
            {'address': residence_address, 'form': residence_address_form},
            use_address,
        )
        admission = form.save(commit=False)
        admission.billing_address = billing_address
        admission.residence_address = residence_address
        admission.save()
        errors, errors_fields = get_submission_errors(admission, is_registration=True)
        return redirect(
            reverse('registration_detail', kwargs={'admission_id': admission_id})
        )
    else:
        errors = list(itertools.product(form.errors, residence_address_form.errors, billing_address_form.errors))
        display_errors(request, errors)
    return render(request, 'registration_form.html', locals())


def _update_or_create_billing_and_post_address(address, billing, residence, use_address):
    if use_address['for_billing']:
        billing['address'] = address
    elif billing['address'] == address:
        billing['address'], created = Address.objects.get_or_create(**billing['form'].cleaned_data)
    else:
        Address.objects.filter(id=billing['address'].id).update(**billing['form'].cleaned_data)

    if use_address['for_post']:
        residence['address'] = address
    elif residence['address'] == address:
        residence['address'], created = Address.objects.get_or_create(**residence['form'].cleaned_data)
    else:
        Address.objects.filter(id=residence['address'].id).update(**residence['form'].cleaned_data)
    return billing['address'], residence['address']
