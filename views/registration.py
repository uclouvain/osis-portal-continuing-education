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
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.models import person as mdl_person
from continuing_education.business import perms
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.person import PersonForm
from continuing_education.forms.registration import RegistrationForm
from continuing_education.models.address import Address
from continuing_education.models.admission import Admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.api import get_registration, get_data_list_from_osis, \
    prepare_registration_data, update_registration
from continuing_education.views.common import display_errors, get_submission_errors, _show_submit_warning, \
    add_informations_message_on_submittable_file, add_contact_for_edit_message, \
    add_remaining_tasks_message
from continuing_education.views.file import _get_files_list, FILES_URL
from osis_common.document.pdf_build import render_pdf


@login_required
@perms.has_participant_access
def registration_detail(request, registration_uuid):
    admission = get_registration(registration_uuid)
    if admission['state'] == admission_state_choices.REGISTRATION_SUBMITTED:
        add_remaining_tasks_message(request)
        add_contact_for_edit_message(request, is_registration=True)
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
        FILES_URL % {'admission_uuid': str(registration_uuid)}
    )

    return render(request, "registration_detail.html", locals())


@login_required
@require_http_methods(["POST"])
def registration_submit(request):
    registration = get_registration(request.POST.get('registration_uuid'))
    if registration['state'] == admission_state_choices.ACCEPTED:
        registration_submission_errors, errors_fields = get_submission_errors(registration, is_registration=True)
        if request.POST.get("submit") and not registration_submission_errors:
            registration['state'] = admission_state_choices.REGISTRATION_SUBMITTED
            update_registration(registration)
            return redirect('registration_detail', registration['uuid'])
    raise PermissionDenied('To submit a registration, its state must be ACCEPTED.')


@login_required
@perms.has_participant_access
def registration_edit(request, registration_uuid):
    registration = get_registration(registration_uuid)
    if registration and registration['state'] != admission_state_choices.ACCEPTED:
        raise PermissionDenied

    form = RegistrationForm(request.POST or None, initial=registration)
    billing_address_form = AddressForm(request.POST or None, instance=registration['billing_address'], prefix="billing")
    residence_address_form = AddressForm(
        request.POST or None,
        instance=registration['residence_address'],
        prefix="residence"
    )
    base_person = mdl_person.find_by_user(user=request.user)
    id_form = PersonForm(request.POST or None, instance=base_person)
    person_information = get_data_list_from_osis("persons", "person", str(base_person.uuid))[0]
    person_form = ContinuingEducationPersonForm(request.POST or None, instance=person_information)

    address = registration['address']
    residence_address = registration['residence_address']
    billing_address = registration['billing_address']

    errors = []
    errors_fields = []
    if registration and not request.POST:
        registration_submission_errors, errors_fields = get_submission_errors(registration, is_registration=True)
        admission_is_submittable = not registration_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(registration_submission_errors, request)

    if all([form.is_valid(), billing_address_form.is_valid(), residence_address_form.is_valid()]):
        # use_address = {
        #     'for_billing': form.cleaned_data['use_address_for_billing'],
        #     'for_post': form.cleaned_data['use_address_for_post']
        # }
        # admission['residence_address'] = residence_address
        # admission['billing_address'] = billing_address
        # billing_address, residence_address = _update_or_create_billing_and_post_address(
        #     address,
        #     {'address': billing_address, 'form': billing_address_form},
        #     {'address': residence_address, 'form': residence_address_form},
        #     use_address,
        # )
        #
        # admission['billing_address'] = billing_address
        # admission['residence_address'] = residence_address
        prepare_registration_data(
            registration,
            forms={
                'registration': form,
                'residence': residence_address_form,
                'billing': billing_address_form,
            }
        )
        update_registration(form.cleaned_data)
        return redirect(
            reverse('registration_detail', kwargs={'admission_uuid': registration_uuid})
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


@login_required
def generate_pdf_registration(request, admission_id):
    admission = get_object_or_404(Admission.objects.select_related(), pk=admission_id)
    if not admission.is_registration_submitted():
        return redirect(
            reverse('registration_detail', kwargs={'admission_id': admission_id})
        )
    context = {
        'root': admission.formation,
        'admission': admission,
        'created': datetime.datetime.now(),
    }
    pdf_filename = get_valid_filename("{}_{}".format(admission.person_information.person, admission.formation.acronym))
    return render_pdf(
        request,
        context=context,
        filename="{}".format(pdf_filename),
        template='registration_pdf.html',
    )
