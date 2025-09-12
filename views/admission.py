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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET

from base.models.person import Person
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.forms.person import PersonForm
from continuing_education.forms.registration import RegistrationForm
from continuing_education.models.enums import admission_state_choices
from continuing_education.views import api
from continuing_education.views.api import get_continuing_education_training
from continuing_education.views.common import display_errors, get_submission_errors, _show_submit_warning, \
    add_informations_message_on_submittable_file, add_contact_for_edit_message, display_info_messages
from continuing_education.views.file import _get_files_list, FILES_URL
from frontoffice.settings.base import MAX_UPLOAD_SIZE
from osis_common.decorators.ajax import ajax_required
from reference.services.country import CountryService

STATES_CAN_UPLOAD_FILE = [
    admission_state_choices.DRAFT,
    admission_state_choices.ACCEPTED,
    admission_state_choices.WAITING,
]


@login_required
def admission_detail(request, admission_uuid):
    try:
        admission = api.get_admission(request, admission_uuid)
        registration = api.get_registration(request, admission_uuid)
    except Http404:
        registration = api.get_registration(request, admission_uuid)
        if registration and registration['state'] == admission_state_choices.ACCEPTED:
            return redirect(reverse('registration_detail',
                                    kwargs={'admission_uuid': admission_uuid if registration else ''}),
                            )
        else:
            return Http404

    admission_is_submittable = False

    if admission['state'] == admission_state_choices.ACCEPTED_NO_REGISTRATION_REQUIRED:
        admission['state'] = admission_state_choices.ACCEPTED
    elif admission['state'] == admission_state_choices.SUBMITTED:
        add_contact_for_edit_message(request, formation=admission['formation'])
        display_info_messages(
            request,
            _("Your admission request has been correctly submitted. The program manager will get back to you shortly.")
        )
    elif admission['state'] == admission_state_choices.DRAFT and admission['formation']['active']:
        add_informations_message_on_submittable_file(
            request=request,
            title=_("Your admission file has been saved. Please consider the following information :")
        )
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(admission_submission_errors, request)
    elif admission['state'] == admission_state_choices.DRAFT and not admission['formation']['active']:
        formation_acronym = admission['formation']['education_group']['acronym']
        managers_emails = ', '.join(manager['email'] for manager in admission['formation']['managers'])
        form_url = reverse('prospect_form', kwargs={'acronym': formation_acronym})
        msg = _("It is not possible to submit your admission file because the formation %(formation)s is now "
                "closed.<br>You can fill the <a href=\"%(form_url)s \">interest form</a> or reach the formation "
                "managers : %(emails)s.") % {
                    'formation': formation_acronym,
                    'form_url': form_url,
                    'emails': managers_emails,
                }
        messages.add_message(
            request=request,
            level=messages.WARNING,
            message=mark_safe(msg)
        )

    list_files = _get_files_list(
        request,
        admission,
        FILES_URL % {'admission_uuid': str(admission_uuid)}
    )
    return render(
        request,
        "admission_detail.html",
        {
            'admission': admission,
            'admission_is_submittable': admission_is_submittable,
            'list_files': list_files,
            'states': {
                'is_draft': admission['state'] == admission_state_choices.DRAFT,
                'is_rejected': admission['state'] == admission_state_choices.REJECTED,
                'is_waiting': admission['state'] == admission_state_choices.WAITING
            },
            'MAX_UPLOAD_SIZE': MAX_UPLOAD_SIZE,
            'registration': registration,
            'registration_required': registration['formation']['registration_required'],
            'can_upload': admission['state'] in STATES_CAN_UPLOAD_FILE
        }
    )


def _show_save_before_submit(request):
    messages.add_message(
        request=request,
        level=messages.INFO,
        message=_(
            "You can save your file, even if it is not fully completed. "
            "You will then be able to modify it and submit it when it is complete."
        ),
    )


@login_required
@require_http_methods(["POST"])
def admission_submit(request):
    admission = api.get_admission(request, request.POST.get('admission_uuid'))
    admission_submission_errors, errors_fields = get_submission_errors(admission)
    if request.POST.get("submit") \
            and not admission_submission_errors:
        _update_admission_state(request, admission)
    return redirect('admission_detail', admission['uuid'])


def _update_admission_state(request, admission):
    submitted_admission = {
        'state': admission_state_choices.SUBMITTED,
        'uuid': admission['uuid']
    }
    api.update_admission(request, submitted_admission)


def _has_instance_with_values(instance):
    for k, v in instance.items():
        if v is None:
            return False
    return True


@login_required
def admission_form(request, admission_uuid=None):
    admission = _get_admission_or_403(admission_uuid, request)
    formation = _get_formation(request, admission)
    registration_required = formation.get('registration_required', False) if formation else True
    address_form, adm_form, id_form, person_form = _fill_forms_with_existing_data(admission, formation, request)
    forms_valid = all([adm_form.is_valid(), person_form.is_valid(), address_form.is_valid(), id_form.is_valid()])
    billing_address_form, registration, registration_form, forms_valid = _get_billing_datas(
        request, admission_uuid, forms_valid, registration_required
    )

    errors_fields = []
    if not admission and not request.POST:
        _show_save_before_submit(request)

    errors_fields = _is_admission_submittable_and_show_errors(admission, errors_fields, request)
    if forms_valid:
        api.prepare_admission_data(
            request,
            admission,
            forms={
                'admission': adm_form,
                'address': address_form,
                'person': person_form,
                'id': id_form
            }
        )

        admission = _update_or_create_admission(adm_form, admission, request)
        registration = registration or {'uuid': admission['uuid'], 'address': admission['address']}
        _update_billing_informations(
            request, {
                'billing': billing_address_form,
                'registration': registration_form
            }, registration, registration_required
        )

        request.session.pop('formation_id', '')

        return redirect(
            reverse('admission_detail', kwargs={'admission_uuid': admission['uuid'] if admission else ''}),
        )
    else:
        errors = []
        if adm_form.errors:
            errors.append(adm_form.errors)
        if person_form.errors:
            errors.append(person_form.errors)
        if address_form.errors:
            errors.append(address_form.errors)
        if id_form.errors:
            errors.append(id_form.errors)
        if registration_form.errors:
            errors.append(registration_form.errors)
        if billing_address_form.errors:
            errors.append(billing_address_form.errors)
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
            'errors_fields': errors_fields,
            'billing_address_form': billing_address_form,
            'registration_form': registration_form,
            'registration': registration
        }
    )


def _update_billing_informations(request, forms, registration, registration_required):
    if not registration_required:
        api.prepare_registration_data(
            registration,
            registration['address'],
            forms={
                'registration': forms['registration'],
                'billing': forms['billing'],
            },
            registration_required=registration_required
        )
        api.update_registration(request, forms['registration'].cleaned_data)


def _get_billing_datas(request, admission_uuid, forms_valid, registration_required):
    registration = None
    registration_form = RegistrationForm(request.POST or None, only_billing=True)
    billing_address_form = AddressForm(request.POST or None, prefix='billing')
    if not registration_required and admission_uuid:
        registration = api.get_registration(request, admission_uuid)
        registration_form = RegistrationForm(request.POST or None, initial=registration, only_billing=True)
        billing_address_form = AddressForm(
            request.POST or None,
            initial=registration['billing_address'],
            prefix='billing',
        )
    forms_valid = forms_valid and registration_form.is_valid() and billing_address_form.is_valid()
    return billing_address_form, registration, registration_form, forms_valid


def _get_admission_or_403(admission_uuid, request):
    admission = api.get_admission(request, admission_uuid) if admission_uuid else None
    if admission and admission['state'] != admission_state_choices.DRAFT:
        raise PermissionDenied
    return admission


def _get_formation(request, admission=None):
    formation = admission and admission.get('formation')
    session_acronym = request.session.get('acronym')
    if formation or session_acronym:
        if isinstance(formation, dict) and formation.get('education_group'):
            return formation
        _, acronym = formation or (None, session_acronym)
        if request.POST:
            acronym = request.POST.get('formation')
        return api.get_continuing_education_training(request, acronym)


def _is_admission_submittable_and_show_errors(admission, errors_fields, request):
    if admission and not request.POST:
        admission['formation_info'] = _get_formation(request, admission)
        admission_submission_errors, errors_fields = get_submission_errors(admission)
        admission_is_submittable = not admission_submission_errors
        if not admission_is_submittable:
            _show_submit_warning(admission_submission_errors, request)
    return errors_fields


def _fill_forms_with_existing_data(admission, formation, request):
    person_information = api.get_continuing_education_person(request)
    person_information.get('person').pop('uuid')
    # exclude person birth_date field as it is not in osis-portal Person model
    person_information.get('person').pop('birth_date')
    Person.objects.filter(user=request.user).update(**person_information.get('person'))
    base_person = Person.objects.get(user=request.user)
    person_form = ContinuingEducationPersonForm(
        request.POST or None,
        initial=person_information if _has_instance_with_values(person_information) else None
    )
    adm_form = AdmissionForm(request.POST or None, initial=admission, formation=formation, user=request.user)

    _keep_posted_data_in_form(adm_form, person_form, request)

    id_form = PersonForm(
        data=request.POST or None,
        instance=base_person,
        no_first_name_checked=request.POST.get('no_first_name', False)
    )
    admissions = api.get_admission_list(request, person_information['uuid'])['results']
    old_admission = _get_old_admission_if_exists(admissions, person_information, request)
    current_address = admission['address'] if admission else None
    address = current_address if current_address else (old_admission['address'] if old_admission else None)
    address_form = AddressForm(request.POST or None, initial=address, person=request.user.person)
    return address_form, adm_form, id_form, person_form


def _keep_posted_data_in_form(adm_form, person_form, request):
    birth_country = request.POST.get('birth_country')
    if birth_country:
        country = CountryService.get_countries(person=request.user.person, iso_code=birth_country)[0]
        person_form.fields['birth_country'].initial = birth_country
        person_form.fields['birth_country'].choices = [
            (country.iso_code, country.name)
        ]
    citizenship = request.POST.get('citizenship')
    if citizenship:
        country = CountryService.get_countries(person=request.user.person, iso_code=citizenship)[0]
        adm_form.fields['citizenship'].initial = citizenship
        adm_form.fields['citizenship'].choices = [
            (country.iso_code, country.name)
        ]
    training = request.POST.get('formation')
    if training:
        adm_form.fields['formation'].initial = training
        adm_form.fields['formation'].choices = [
            (training, training)
        ]


def _get_old_admission_if_exists(admissions, person_information, request):
    old_admission = admissions[0] if admissions \
        else api.get_registration_list(request, person_information['uuid'])['results']
    if old_admission:
        if admissions:
            old_admission = api.get_admission(request, old_admission['uuid'])
        else:
            old_admission = api.get_registration(request, old_admission[0]['uuid'])
    return old_admission


def _update_or_create_admission(adm_form, admission, request):
    if admission:
        api.update_admission(request, adm_form.cleaned_data)
    else:
        admission, status = api.post_admission(request, adm_form.cleaned_data)
    return admission


@ajax_required
@login_required
@require_GET
def get_formation_information(request):
    formation_acronym = request.GET.get('formation_acronym')
    training = get_continuing_education_training(request, acronym=formation_acronym)
    return JsonResponse(data={
        'additional_information_label': linebreaks(training.get('additional_information_label', '')),
        'registration_required': training.get('registration_required', True)
    })
