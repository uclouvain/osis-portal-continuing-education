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
from base.models.person import Person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.forms.person import PersonForm
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
    adm_form = AdmissionForm(request.POST or None, instance=admission)
    if person_information:
        person_form = ContinuingEducationPersonForm(request.POST or None,
                                                    b_country=person_information.birth_country,
                                                    b_date=person_information.birth_date,
                                                    b_location=person_information.birth_location,
                                                    instance=person_information
                                                    )
    else:
        person_form = ContinuingEducationPersonForm(request.POST or None,
                                                    instance=person_information
                                                    )
    old_admission = Admission.objects.filter(person_information=person_information).last()
    address = old_admission.address if old_admission else None
    address_form = AddressForm(request.POST or None, instance=address)
    
    if base_person:
        id_form = PersonForm(request.POST or None,
                             first_name=base_person.first_name,
                             last_name=base_person.last_name,
                             gender=base_person.gender,
                             user_email=base_person.email
                             )
    else:
        id_form = PersonForm(request.POST or None)

    if adm_form.is_valid() and person_form.is_valid() and address_form.is_valid() and id_form.is_valid():
        address, created = Address.objects.get_or_create(**address_form.cleaned_data)
        identity, created = Person.objects.get_or_create(**id_form.cleaned_data)
        identity.user = request.user
        identity.save()
        person = person_form.save(commit=False)
        person.person_id = identity.pk
        person.save()
        admission = adm_form.save(commit=False)
        admission.person_information = person
        admission.address = address
        admission.save()
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
