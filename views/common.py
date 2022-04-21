##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, gettext

from base.models.person import Person
from base.views import layout
from base.views.layout import render
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.address import StrictAddressForm
from continuing_education.forms.admission import StrictAdmissionForm
from continuing_education.forms.person import StrictPersonForm
from continuing_education.forms.registration import StrictRegistrationForm
from continuing_education.views.login import ContinuingEducationLoginView
from osis_common.utils.models import get_object_or_none

ONE_OF_THE_NEEDED_FIELD_BEFORE_SUBMISSION = 'national_registry_number'


def display_errors(request, errors):
    for error in errors:
        for key, value in error.items():
            messages.add_message(request, messages.ERROR, "{} : {}".format(_(key), value[0]), "alert-danger")


def login(request):
    if "next" in request.GET:
        formation_id = request.GET['next'].rsplit('/', 1)[-1]
    if request.method == 'POST':
        _handle_login_view(request)
        person, user = _retrieve_auth_info(request)
        if user and not person:
            return redirect(reverse('admission_new'))
        return redirect(reverse('continuing_education_home'))
    else:
        return render(request, "authentication/login.html", locals())


def _retrieve_auth_info(request):
    user = request.user if request.user.pk else None
    person = get_object_or_none(Person, user=user) if user else None
    # ./manage.py createsuperuser (in local) doesn't create automatically a Person associated to User
    if person and person.language:
        user_language = person.language
        translation.activate(user_language)
        request.session[translation.LANGUAGE_SESSION_KEY] = user_language
    return person, user


def _handle_login_view(request):
    login_view = ContinuingEducationLoginView.as_view()(request)
    if hasattr(login_view, 'context_data') and login_view.context_data['form']:
        form = login_view.context_data['form']
        for error, message in form.errors.items():
            display_error_messages(request, message)


def log_out(request):
    logout(request)
    return redirect('continuing_education_logged_out')


def logged_out(request):
    return layout.render(request, 'authentication/logged_out.html', {})


def display_error_messages(request, messages_to_display):
    display_messages(request, messages_to_display, messages.ERROR)


def display_success_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.SUCCESS, extra_tags=extra_tags)


def display_info_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.INFO, extra_tags=extra_tags)


def display_warning_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.WARNING, extra_tags=extra_tags)


def display_messages(request, messages_to_display, level, extra_tags=None):
    if not isinstance(messages_to_display, (tuple, list)):
        messages_to_display = [messages_to_display]

    for msg in messages_to_display:
        messages.add_message(request, level, _(msg), extra_tags=extra_tags)


def get_submission_errors(admission, is_registration=False):
    errors_field = []
    errors = OrderedDict()

    if is_registration:

        address_form = StrictAddressForm(
            data=admission['billing_address']
        )
        adm_form = StrictRegistrationForm(
            data=admission
        )

        _update_errors([address_form, adm_form], errors, errors_field)

        if not admission['use_address_for_post']:
            residence_address_form = StrictAddressForm(
                data=admission['residence_address']
            )
            _update_errors([residence_address_form], errors, errors_field)
    else:
        person_form = StrictPersonForm(
            data=admission['person_information']['person'] if 'person' in admission['person_information'] else None
        )
        person_information_form = ContinuingEducationPersonForm(
            data=admission['person_information']
        )
        address_form = StrictAddressForm(
            data=admission['address']
        )
        adm_form = StrictAdmissionForm(
            data=admission,
        )
        print('------a')
        for e in address_form.errors:
            print(e)
        print('------b')
        forms = [person_form, person_information_form, address_form, adm_form]
        _update_errors(forms, errors, errors_field)

    return errors, errors_field


def _update_errors(forms, errors, errors_field):
    for form in forms:
        for field in form.errors:
            print('field {}'.format(field))
            errors.update({form[field].label: form.errors[field]})
            errors_field.append(field)


def _build_warning_from_errors_dict(errors):
    warning_message = gettext(
        "Your file is not submittable because you did not provide the following data : "
    )
    warning_message = \
        "<strong>" + \
        warning_message + \
        "</strong><br>" + \
        " · ".join([gettext(key) for key in _build_error_data(errors)])

    return mark_safe(warning_message)


def _show_submit_warning(admission_submission_errors, request):
    if request.method == 'GET':
        messages.add_message(
            request=request,
            level=messages.WARNING,
            message=_build_warning_from_errors_dict(admission_submission_errors),
        )


def add_informations_message_on_submittable_file(request, title):
    if request.method == 'GET':
        items = [
            _("You are still able to edit the form, via the 'Edit' button"),
            _("You can upload documents via the 'Documents'"),
        ]
        message = "<strong>{}</strong><br>".format(title) + \
                  "".join(["- {}<br>".format(item) for item in items])

        messages.add_message(
            request=request,
            level=messages.INFO,
            message=mark_safe(message)
        )

        message_warning = "<strong>" + \
                          str(_("Do not forget to submit your file when it is complete")) + \
                          "</strong>"
        messages.add_message(
            request=request,
            level=messages.WARNING,
            message=mark_safe(message_warning)
        )


def add_remaining_tasks_message(request, formation):
    message = _("Your registration file has been saved. "
                "<b>Please consider the following remaining instructions</b> to complete submission. ")
    message += "<a id='show-instructions-button'><b>{}</b></a>".format(_("Show instructions"))
    if not formation['postal_address']:
        message = message.replace(' : ', '.')
    messages.add_message(
        request=request,
        level=messages.WARNING,
        message=mark_safe(message)
    )


def format_formation_address(address):
    if address:
        return address['location'] + '<br/>' + address['postal_code'] + ' ' + address['city'] + \
               (' (' + address['country']['name'] + ')' if address['country'] else '')
    return ''


def add_contact_for_edit_message(request, formation=None, is_registration=False):
    mails = _get_managers_mails(formation)
    if is_registration:
        message = _("If you want to edit again your registration, please contact the program manager : %(mail)s") \
                  % {'mail': mails}
    else:
        message = _("If you want to edit again your admission, please contact the program manager : %(mail)s") \
                  % {'mail': mails}
    if not mails:
        message = message.replace(' : ', '.')
    messages.add_message(
        request=request,
        level=messages.INFO,
        message=mark_safe(message)
    )


def _get_managers_mails(formation):
    managers_mail = [d['email'] for d in formation['managers'] if d['email']] if formation['managers'] else []
    return _(" or ").join(managers_mail)


def _build_error_data(errors):
    errors_data = []
    phone_fields = [_('Phone mobile'), _('Residence phone')]
    error_phone = ''
    for k, v in errors.items():
        if ONE_OF_THE_NEEDED_FIELD_BEFORE_SUBMISSION in v:
            errors_data.append(
                _('At least one of the 3 following fields must be filled-in : national registry, id card number '
                  'or passport number')
            )
        elif k in phone_fields and v.data[0].code != 'required':
            error_phone = "<br>" + str(v.data[0].message) + '<br>'
        else:
            errors_data.append(k)
    if error_phone:
        errors_data.append(error_phone)
    return errors_data
