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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

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
from continuing_education.views.common import display_errors


@login_required
def admission_detail(request, admission_id):
    admission = _find_user_admission_by_id(admission_id, user=request.user)
    admission_submission_errors = get_admission_submission_errors(admission)
    admission_is_submittable = not admission_submission_errors

    if request.POST.get("submit") and admission_is_submittable:
        admission.submit()

    if not admission_is_submittable:
        messages.add_message(
            request=request,
            level=messages.WARNING,
            message=_build_warning_from_errors(admission_submission_errors),
        )

    return render(
        request,
        "admission_detail.html",
        {
            'admission': admission,
            'admission_is_submittable': admission_is_submittable,
        }
    )


def get_admission_submission_errors(admission):
    errors = {}

    person_form = StrictPersonForm(
        data=model_to_dict(admission.person_information.person)
    )
    errors.update(person_form.errors)

    person_information_form = ContinuingEducationPersonForm(
        data=model_to_dict(admission.person_information)
    )
    errors.update(person_information_form.errors)

    address_form = StrictAddressForm(
        data=model_to_dict(admission.address)
    )
    errors.update(address_form.errors)

    adm_form = StrictAdmissionForm(
        data=model_to_dict(admission)
    )
    errors.update(adm_form.errors)

    return errors


def _build_warning_from_errors(errors):
    warning_message = _("Your admission file is not submittable because you did not provide the following data : ")
    warning_message += ", ".join(['"' + ugettext(key) + '"' for key in errors.keys()])
    return warning_message


@login_required
def admission_form(request, admission_id=None):
    base_person = mdl_person.find_by_user(user=request.user)
    admission = _find_user_admission_by_id(admission_id, user=request.user) if admission_id else None
    if admission and admission.state != admission_state_choices.DRAFT:
        raise PermissionDenied
    person_information = continuing_education_person.find_by_person(person=base_person)
    adm_form = AdmissionForm(request.POST or None, instance=admission)

    person_form = check_continuing_education_person(request, person_information)

    current_address = admission.address if admission else None
    old_admission = Admission.objects.filter(person_information=person_information).last()
    address = current_address if current_address else (old_admission.address if old_admission else None)
    address_form = AddressForm(request.POST or None, instance=address)

    id_form = check_base_person(request, base_person)

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


def check_base_person(request, base_person):
    if base_person:
        return PersonForm(
            request.POST or None,
            instance=base_person,
        )
    else:
        return PersonForm(request.POST or None)


def check_continuing_education_person(request, person_information):
    if person_information:
        return ContinuingEducationPersonForm(
            request.POST or None,
            instance=person_information,
            )
    else:
        return ContinuingEducationPersonForm(request.POST or None)


def _find_user_admission_by_id(admission_id, user):
    return get_object_or_404(
        Admission,
        pk=admission_id,
        person_information__person__user=user
    )
