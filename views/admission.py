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

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404

from base.models import person as mdl_person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.models import continuing_education_person
from continuing_education.models.address import Address
from continuing_education.models.admission import Admission
from continuing_education.views.common import display_errors


@login_required
def admission_detail(request, admission_id):
    admission = get_object_or_404(Admission, pk=admission_id)
    return render(request, "admission_detail.html", locals())

@login_required
def admission_form(request, admission_id=None):
    base_person = mdl_person.find_by_user(user=request.user)
    admission = get_object_or_404(Admission, pk=admission_id) if admission_id else None
    person_information = continuing_education_person.find_by_person(person=base_person)
    address = person_information.address if person_information else None
    admission_form = AdmissionForm(request.POST or None, instance=admission)
    person_form = ContinuingEducationPersonForm(request.POST or None, instance=person_information)
    address_form = AddressForm(request.POST or None, instance=address)
    if all((admission_form.is_valid(), person_form.is_valid(), address_form.is_valid())):
        address, created = Address.objects.get_or_create(**address_form.cleaned_data)
        person = person_form.save(commit=False)
        person.address = address
        person.person_id = base_person.pk
        person.save()
        admission = admission_form.save(commit=False)
        admission.person_information = person
        admission.save()
        return redirect(reverse('admission_detail', kwargs={'admission_id':admission.pk}))
    else:
        errors = list(itertools.product(admission_form.errors, person_form.errors, address_form.errors))
        display_errors(request, errors)

    return render(request, 'admission_form.html', {'admission_form': admission_form, 'person_form': person_form,
                                                   'address_form': address_form})