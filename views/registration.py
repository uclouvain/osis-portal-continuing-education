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
from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.views.decorators.http import require_http_methods

from base.models import person as mdl_person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm, StrictAddressForm
from continuing_education.forms.person import PersonForm
from continuing_education.forms.registration import RegistrationForm, StrictRegistrationForm
from continuing_education.models import continuing_education_person
from continuing_education.models.address import Address
from continuing_education.models.admission import Admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.admission import _find_user_admission_by_id, _show_submit_warning
from continuing_education.views.common import display_errors


@login_required
def registration_detail(request, admission_id):
    admission = get_object_or_404(Admission, pk=admission_id)
    if admission.state == admission_state_choices.ACCEPTED:
        registration_submission_errors, errors_fields = get_registration_submission_errors(admission)
        registration_is_submittable = not registration_submission_errors
        if not registration_is_submittable:
            _show_submit_warning(registration_submission_errors, request)
    else:
        registration_is_submittable = False
    return render(request, "registration_detail.html", locals())


def get_registration_submission_errors(admission):
    errors_field = []
    errors = OrderedDict()

    address_form = StrictAddressForm(
        data=model_to_dict(admission.billing_address)
    )
    for field in address_form.errors:
        errors.update({address_form[field].label: address_form.errors[field]})
        errors_field.append(field)

    if not admission.use_address_for_post:
        residence_address_form = StrictAddressForm(
            data=model_to_dict(admission.residence_address)
        )
        for field in residence_address_form.errors:
            errors.update({residence_address_form[field].label: residence_address_form.errors[field]})
            errors_field.append(field)

    adm_form = StrictRegistrationForm(
        data=model_to_dict(admission)
    )
    for field in adm_form.errors:
        errors.update({adm_form[field].label: adm_form.errors[field]})
        errors_field.append(field)

    return errors, errors_field


def _build_warning_from_errors_dict(errors):
    warning_message = ugettext(
        "Your registration file is not submittable because you did not provide the following data : "
    )

    warning_message = \
        "<strong>" + \
        warning_message + \
        "</strong><br>" + \
        " · ".join([ugettext(key) for key in errors.keys()])

    return mark_safe(warning_message)


@login_required
@require_http_methods(["POST"])
def registration_submit(request):
    admission = _find_user_admission_by_id(request.POST.get('admission_id'), user=request.user)

    if admission.state == admission_state_choices.ACCEPTED:
        registration_submission_errors, errors_fields = get_registration_submission_errors(admission)
        if request.POST.get("submit") and not registration_submission_errors:
            admission.submit_registration()
            return redirect('registration_detail', admission.pk)

    raise PermissionDenied


@login_required
def registration_edit(request, admission_id):
    admission = get_object_or_404(Admission, pk=admission_id)
    form = RegistrationForm(request.POST or None, instance=admission)
    billing_address_form = AddressForm(request.POST or None, instance=admission.billing_address, prefix="billing")
    residence_address_form = AddressForm(request.POST or None, instance=admission.residence_address, prefix="residence")
    errors = []
    errors_fields = []
    base_person = mdl_person.find_by_user(user=request.user)
    id_form = PersonForm(request.POST or None, instance=base_person)
    person_information = continuing_education_person.find_by_person(person=base_person)
    person_form = ContinuingEducationPersonForm(request.POST or None, instance=person_information)
    address = admission.address
    if form.is_valid() and billing_address_form.is_valid() and residence_address_form.is_valid():
        billing_address, created = Address.objects.get_or_create(**billing_address_form.cleaned_data)
        residence_address, created = Address.objects.get_or_create(**residence_address_form.cleaned_data)
        admission = form.save(commit=False)
        admission.billing_address = billing_address
        admission.residence_address = residence_address
        admission.save()
        errors, errors_fields = get_registration_submission_errors(admission)
        return redirect(reverse('registration_detail', kwargs={'admission_id': admission_id}))
    else:
        errors = list(itertools.product(form.errors, residence_address_form.errors, billing_address_form.errors))
        display_errors(request, errors)

    return render(request, 'registration_form.html', locals())
